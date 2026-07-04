#!/usr/bin/env python3
"""
Defesa Civil SC - Meshtastic Standalone
Integração para ler alertas da Defesa Civil SC e redistribuir via Meshtastic.
"""

import sys
import os
import time
import logging
import threading
from pathlib import Path
from typing import Optional
import signal

# Configurar paths - core deve estar antes de imports que o usam
PROJECT_ROOT = Path(__file__).parent.parent.parent
STANDALONE_SRC = Path(__file__).parent / "src"

# Adicionar paths para imports
sys.path.insert(0, str(STANDALONE_SRC))
sys.path.insert(0, str(PROJECT_ROOT))

# Imports de core/ (compartilhados) - ANTES de state_manager que depende disso
from core import (
    RSSParser,
    MessageFormatter,
    RegionFilter,
    MAX_HISTORY,
    CHANNEL_LINK_DELAY_SECONDS,
    CHANNEL_ALERT_BATCH_DELAY_SECONDS,
    DEFAULT_INTERVAL_MINUTES,
)

# Imports de src/ (específicos do standalone) - DEPOIS de core estar disponível
from config_manager import ConfigManager
from state_manager import StateManager
from meshtastic_connector import MeshtasticConnector


class DefesaCivilAlertasStandalone:
    """Orquestrador principal da aplicação."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa a aplicação.
        
        Args:
            config_file: Caminho do arquivo de configuração
        """
        self.config = ConfigManager(config_file)
        
        if not self.config.validate():
            raise ValueError("Configuração inválida")
        
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager(self.config.get("state.file"))
        self.rss_parser = RSSParser(
            timeout_seconds=self.config.get("feed.timeout_seconds", 30),
            interval_minutes=self.config.get("feed.interval_minutes") or None
        )
        self.formatter = MessageFormatter()
        self.region_filter = RegionFilter(
            self.config.get_region_filter_config()
        )
        valid, errors = self.region_filter.validate_config()
        if not valid:
            for error in errors:
                self.logger.warning(error)
        self.mesh = None
        self.running = False
        self.shutdown_requested = False
        self.next_check_time = time.time()
        
        # Monitoramento e reconexão automática
        self.connection_check_interval = 30  # segundos quando conectado
        self.disconnected_check_interval = 5  # segundos quando desconectado
        self.last_connection_check = 0.0
        self.reconnect_attempts = 0
        self.reconnect_backoff_seconds = 30  # inicia em 30s
        self.max_reconnect_backoff_seconds = 300  # máximo 5 minutos
        self.last_reconnect_attempt = 0.0
        self._connection_lock = threading.RLock()
    
    def _setup_logging(self) -> None:
        """Configura logging da aplicação."""
        log_level = self.config.get("logging.level", "DEBUG").upper()
        log_file = self.config.get("logging.file")
        
        # Formato de log
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if log_file:
            logging.basicConfig(
                level=getattr(logging, log_level),
                format=log_format,
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=getattr(logging, log_level),
                format=log_format
            )

        # Suprimir logs verbosos da biblioteca meshtastic quando não estiver em DEBUG
        if log_level != "DEBUG":
            logging.getLogger("meshtastic").setLevel(logging.ERROR)

            # Suprimir tracebacks de threads internas da lib meshtastic fora do DEBUG
            def _thread_excepthook(args):
                name = getattr(args.thread, "name", "?")
                self.logger.debug(
                    f"Exception em thread '{name}' suprimida: "
                    f"{args.exc_type.__name__}: {args.exc_value}"
                )

            threading.excepthook = _thread_excepthook
    
    def connect_meshtastic(self) -> bool:
        """Conecta ao Meshtastic."""
        with self._connection_lock:
            self.logger.info("Conectando ao Meshtastic...")
            
            mesh_config = self.config.get_meshtastic_config()
            
            self.mesh = MeshtasticConnector(
                connection_type=mesh_config.get("connection_type", "serial"),
                serial_port=mesh_config.get("serial_port"),
                tcp_host=mesh_config.get("tcp_host"),
                tcp_port=mesh_config.get("tcp_port", 4403),
                logger=self.logger
            )
            
            if not self.mesh.connect():
                self.logger.error("Falha ao conectar ao Meshtastic")
                return False
            
            # Registrar callback para mensagens diretas
            if self.config.get("direct_message.enabled", True):
                self.mesh.register_receive_callback(self.on_message_received)
                self.logger.debug("Callback de mensagens diretas registrado")
            
            return True
    
    def check_meshtastic_connection(self) -> bool:
        """Verifica se a conexão Meshtastic está ativa."""
        with self._connection_lock:
            if not self.mesh:
                return False
            if self.mesh.is_connected():
                # Resetar backoff em caso de conexão estável
                if self.reconnect_attempts > 0:
                    self.logger.info("Conexão Meshtastic restaurada")
                self.reconnect_attempts = 0
                self.reconnect_backoff_seconds = 30
                return True
            return False
    
    def reconnect_meshtastic(self) -> bool:
        """
        Tenta reconectar ao Meshtastic com backoff exponencial.
        
        Inicia em 30s e dobra até o máximo de 5 minutos (300s),
        tentando indefinidamente.
        
        Returns:
            True se reconectado com sucesso, False caso contrário.
        """
        with self._connection_lock:
            now = time.time()
            elapsed = now - self.last_reconnect_attempt
            
            if elapsed < self.reconnect_backoff_seconds:
                return False
            
            self.last_reconnect_attempt = now
            self.reconnect_attempts += 1
            
            self.logger.warning(
                f"Tentativa de reconexão {self.reconnect_attempts} ao Meshtastic "
                f"(próxima em {self.reconnect_backoff_seconds}s)"
            )
            
            try:
                if self.mesh:
                    self.mesh.disconnect()
            except Exception as e:
                self.logger.debug(f"Erro ao desconectar antes de reconectar: {e}")
            
            try:
                if self.mesh and self.mesh.connect():
                    self.logger.info("Reconectado ao Meshtastic com sucesso")
                    self.reconnect_attempts = 0
                    self.reconnect_backoff_seconds = 30
                    self.last_reconnect_attempt = 0.0
                    
                    # Re-registrar callback de mensagens diretas
                    if self.config.get("direct_message.enabled", True):
                        self.mesh.register_receive_callback(self.on_message_received)
                        self.logger.debug("Callback de mensagens diretas re-registrado")
                    
                    return True
            except Exception as e:
                self.logger.error(f"Erro durante tentativa de reconexão: {e}")
            
            # Backoff exponencial com limite de 5 minutos
            self.reconnect_backoff_seconds = min(
                self.reconnect_backoff_seconds * 2,
                self.max_reconnect_backoff_seconds
            )
            self.logger.warning(
                f"Reconexão falhou. Próxima tentativa em {self.reconnect_backoff_seconds}s"
            )
            return False
    
    def on_message_received(self, packet: dict, interface) -> None:
        """
        Callback para mensagens recebidas.
        
        Args:
            packet: Pacote recebido
            interface: Interface Meshtastic
        """
        try:
            self.logger.debug(f"Pacote recebido: {packet}")
            
            if "decoded" not in packet:
                self.logger.debug("Pacote ignorado: sem 'decoded'")
                return
            
            decoded = packet["decoded"]
            self.logger.debug(f"Decoded: {decoded}")
            
            # Verificar se é mensagem de texto (portnum 1 ou 'TEXT_MESSAGE_APP')
            portnum = decoded.get("portnum")
            if isinstance(portnum, int):
                is_text = portnum == 1
            elif isinstance(portnum, str):
                is_text = portnum.upper() == "TEXT_MESSAGE_APP"
            else:
                is_text = "text" in decoded
            
            if not is_text:
                self.logger.debug(f"Pacote ignorado: portnum={portnum} não é texto")
                return
            
            # Extrair texto (novas versões já expõem 'text'; fallback para payload)
            message_text = None
            if "text" in decoded:
                message_text = decoded["text"]
                self.logger.debug(f"Texto extraído de decoded['text']: '{message_text}'")
            elif "payload" in decoded:
                try:
                    message_text = decoded["payload"].decode("utf-8")
                    self.logger.debug(f"Texto decodificado de payload: '{message_text}'")
                except Exception as e:
                    self.logger.debug(f"Payload não decodificável como texto: {e}")
                    return
            else:
                self.logger.debug("Pacote ignorado: sem 'text' nem 'payload'")
                return
            
            trigger_word = self.config.get("direct_message.trigger_word", "ALERTAS")
            from_id = packet.get("from")
            to_id = packet.get("to")
            self.logger.debug(
                f"Mensagem de {from_id} para {to_id}: '{message_text}'"
            )
            
            # Responder apenas a mensagens diretas (não broadcast)
            BROADCAST_NUM = 0xFFFFFFFF
            my_info = self.mesh.get_my_info() if self.mesh else None
            my_node_num = None
            if my_info:
                if isinstance(my_info, dict):
                    my_node_num = my_info.get("my_node_num") or my_info.get("num")
                else:
                    my_node_num = getattr(my_info, "my_node_num", None) or getattr(my_info, "num", None)
            
            is_broadcast = to_id is None or to_id == BROADCAST_NUM
            if is_broadcast:
                self.logger.debug(f"Mensagem de broadcast ignorada (to={to_id})")
                return
            
            if my_node_num and to_id != my_node_num:
                self.logger.debug(
                    f"Mensagem não é para este node (to={to_id}, me={my_node_num})"
                )
                return
            
            if trigger_word in message_text.strip().upper():
                self.logger.info(
                    f"Comando '{trigger_word}' recebido de {from_id}"
                )
                # Responder em thread separada para não bloquear o callback pubsub
                threading.Thread(
                    target=self.handle_dm_alerts_request,
                    args=(packet, interface),
                    daemon=True
                ).start()
            else:
                self.logger.error(
                    f"Mensagem direta de {from_id} não contém comando "
                    f"'{trigger_word}': '{message_text}'"
                )
        
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem recebida: {e}")
    
    def handle_dm_alerts_request(self, packet: dict, interface) -> None:
        """
        Responde a requisição de alertas via DM.
        
        Args:
            packet: Pacote recebido
            interface: Interface Meshtastic
        """
        try:
            from_id = packet.get("from")
            from_id_str = packet.get("fromId") or str(from_id)
            if not from_id:
                self.logger.debug("DM sem remetente ignorado")
                return
            
            # Obter alertas recentes e aplicar filtro regional
            max_alerts = self.config.get("direct_message.max_alerts_reply", 3)
            latest_alerts = self.state_manager.get_latest_alerts(max_alerts * 2)
            alerts = [
                alert for alert in latest_alerts
                if self.region_filter.should_send(alert)
            ][:max_alerts]
            
            if not alerts:
                self.logger.info(f"Sem alertas para responder a {from_id_str}")
                self.mesh.send_direct_message(
                    "Nenhum alerta ativo no momento.", from_id_str
                )
                return
            
            self.logger.info(f"Enviando {len(alerts)} alerta(s) via DM para {from_id_str}")
            
            for idx, alert in enumerate(alerts):
                if not self.running:
                    self.logger.debug("Resposta a DM abortada: shutdown solicitado")
                    break
                
                # Enviar em duas mensagens
                msg1, msg2 = self.formatter.build_alert_messages(alert)
                
                self.logger.info(f"Enviando DM {idx+1}/{len(alerts)} parte 1 para {from_id_str}")
                if not self.mesh.send_direct_message(msg1, from_id_str):
                    self.logger.error(f"Falha ao enviar DM {idx+1} parte 1 para {from_id_str}")
                    self.reconnect_meshtastic()
                    break
                
                # Aguardar entre as duas partes, verificando shutdown
                for _ in range(int(CHANNEL_LINK_DELAY_SECONDS * 2)):
                    if not self.running:
                        break
                    time.sleep(0.5)
                if not self.running:
                    break
                
                self.logger.info(f"Enviando DM {idx+1}/{len(alerts)} parte 2 para {from_id_str}")
                if not self.mesh.send_direct_message(msg2, from_id_str):
                    self.logger.error(f"Falha ao enviar DM {idx+1} parte 2 para {from_id_str}")
                    self.reconnect_meshtastic()
                    break
                
                if idx < len(alerts) - 1:
                    for _ in range(int(CHANNEL_ALERT_BATCH_DELAY_SECONDS * 2)):
                        if not self.running:
                            break
                        time.sleep(0.5)
                    if not self.running:
                        break
            
            self.logger.info(f"Resposta de DM para {from_id_str} concluída")
        
        except Exception as e:
            self.logger.error(f"Erro ao responder DM de alertas: {e}")
    
    def send_alert_to_channel(
        self, alert: dict, channel_id: int = 0, is_first: bool = True
    ) -> bool:
        """
        Envia alerta para canal Meshtastic.
        
        Args:
            alert: Dicionário com dados do alerta
            channel_id: ID do canal
            is_first: Se True, marca a primeira mensagem como alerta de notificação
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            if not self.running:
                self.logger.debug("Envio abortado: aplicação está encerrando")
                return False
            
            msg1, msg2 = self.formatter.build_alert_messages(alert)
            
            # Apenas a primeira mensagem do lote usa send_alert (notificação especial)
            if is_first:
                self.logger.debug(f"Enviando alerta para canal {channel_id}: {msg1[:80]}...")
                if not self.mesh.send_alert(msg1, channel_id):
                    self.logger.error("Falha ao enviar mensagem de alerta")
                    return False
                self.logger.info(f"Alerta enviado: {msg1[:80]}...")
            else:
                self.logger.debug(f"Enviando mensagem para canal {channel_id}: {msg1[:80]}...")
                if not self.mesh.send_to_channel(msg1, channel_id):
                    self.logger.error("Falha ao enviar mensagem de alerta")
                    return False
                self.logger.info(f"Mensagem enviada: {msg1[:80]}...")
            
            # Aguardar antes de enviar link, verificando shutdown
            for _ in range(int(CHANNEL_LINK_DELAY_SECONDS * 2)):
                if not self.running:
                    self.logger.debug("Envio abortado durante espera do link")
                    return False
                time.sleep(0.5)
            
            # Enviar link
            self.logger.debug(f"Enviando link para canal {channel_id}: {msg2[:80]}...")
            if not self.mesh.send_to_channel(msg2, channel_id):
                self.logger.error("Falha ao enviar link do alerta")
                return False
            self.logger.debug(f"Link enviado: {msg2}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta: {e}")
            return False
    
    def check_feed(self) -> None:
        """Verifica feed RSS e envia novos alertas."""
        try:
            self.logger.info("Verificando feed RSS...")
            
            # Fazer fetch do feed
            items, period, frequency, interval_minutes = self.rss_parser.parse_and_fetch()
            
            self.logger.info(
                f"Feed carregado: {len(items)} itens "
                f"(próxima verificação em {interval_minutes} minutos)"
            )
            
            # Atualizar intervalo
            self.state_manager.set_update_interval(period, frequency, interval_minutes)
            
            channel_config = self.config.get_channel_config()
            channel_name = channel_config.get("name")
            channel_number = channel_config.get("number", 0)
            channel_id = self.mesh.resolve_channel_id(channel_name, default=channel_number)
            self.logger.info(f"Canal de envio: {channel_name or channel_number} (índice {channel_id})")
            
            new_alerts_count = 0
            first_message = True
            
            for item in items:
                if not self.running:
                    self.logger.debug("Verificação de feed abortada: shutdown solicitado")
                    break
                
                guid = item.get("guid")
                
                if not guid:
                    self.logger.warning(
                        f"Alerta sem GUID ignorado: {item.get('title', '')[:60]}..."
                    )
                    continue
                
                if self.state_manager.is_guid_processed(guid):
                    self.logger.debug(f"Alerta já processado: {guid}")
                    continue
                
                # Aplicar filtro regional
                if not self.region_filter.should_send(item):
                    matches = self.region_filter.get_matches(item)
                    self.logger.info(
                        f"Alerta ignorado por filtro regional: {guid} "
                        f"(matches: {matches})"
                    )
                    self.state_manager.add_ignored_guid(guid)
                    continue
                
                # Enviar alerta (apenas a primeira mensagem do lote é marcada como alerta)
                self.logger.info(f"Novo alerta detectado: {item.get('title', '')[:60]}...")
                if self.send_alert_to_channel(item, channel_id, is_first=first_message):
                    new_alerts_count += 1
                    first_message = False
                    # Marcar como enviado e armazenar apenas se enviou com sucesso
                    self.state_manager.add_sent_guid(guid)
                    self.state_manager.add_alert(
                        item, self.config.get("state.max_history", MAX_HISTORY)
                    )
                else:
                    self.logger.warning(
                        f"Alerta não enviado devido a falha de conexão: {guid}"
                    )
                    # Tentar reconectar imediatamente e parar processamento
                    self.reconnect_meshtastic()
                    break
                
                # Aguardar antes do próximo alerta, verificando shutdown
                if new_alerts_count < len(items):
                    for _ in range(int(CHANNEL_ALERT_BATCH_DELAY_SECONDS * 2)):
                        if not self.running:
                            self.logger.debug("Verificação de feed abortada durante espera")
                            break
                        time.sleep(0.5)
                    if not self.running:
                        break
            
            # Salvar estado
            self.state_manager.save()
            
            if new_alerts_count > 0:
                self.logger.info(f"{new_alerts_count} novo(s) alerta(s) enviado(s)")
            
            # Calcular próximo horário de verificação
            self.next_check_time = time.time() + (interval_minutes * 60)
        
        except Exception as e:
            self.logger.error(f"Erro ao verificar feed: {e}")
            # Usar intervalo padrão em caso de erro
            self.next_check_time = time.time() + (DEFAULT_INTERVAL_MINUTES * 60)
    
    def send_test_alert(self) -> None:
        """Modo de teste: envia alerta mais recente ou busca um do feed."""
        try:
            alerts = self.state_manager.get_alerts()
            
            if not alerts:
                self.logger.info("Modo de teste: nenhum alerta armazenado. Buscando feed...")
                items, _, _, _ = self.rss_parser.parse_and_fetch()
                
                if items:
                    alerts = [items[0]]
                    self.state_manager.add_alert(alerts[0])
                    self.state_manager.save()
                else:
                    self.logger.warning("Nenhum alerta encontrado no feed")
                    return
            
            if alerts:
                channel_config = self.config.get_channel_config()
                channel_name = channel_config.get("name")
                channel_number = channel_config.get("number", 0)
                channel_id = self.mesh.resolve_channel_id(channel_name, default=channel_number)
                self.logger.info("Modo de teste: enviando alerta mais recente...")
                self.send_alert_to_channel(alerts[0], channel_id)
        
        except Exception as e:
            self.logger.error(f"Erro no modo de teste: {e}")
    
    def run(self) -> None:
        """Loop principal da aplicação."""
        self.logger.info("Iniciando Defesa Civil SC - Meshtastic Standalone")
        
        if not self.connect_meshtastic():
            self.logger.error("Não foi possível conectar ao Meshtastic")
            return
        
        self.running = True
        self.logger.info("Aplicação iniciada com sucesso!")
        
        # Handler para Ctrl+C e SIGTERM
        def signal_handler(sig, frame):
            if self.shutdown_requested:
                self.logger.warning("Shutdown forçado")
                sys.exit(1)
            self.logger.info("Encerrando aplicação...")
            self.shutdown_requested = True
            self.running = False
            self.cleanup()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Primeira verificação
        if self.config.is_test_mode():
            self.logger.info("MODO DE TESTE ATIVADO")
            self.send_test_alert()
        else:
            self.check_feed()
        
        # Loop principal
        while self.running:
            try:
                now = time.time()
                
                # Monitorar conexão com Meshtastic periodicamente
                # Intervalo menor quando desconectado para reconectar mais rápido
                check_interval = (
                    self.disconnected_check_interval
                    if self.reconnect_attempts > 0
                    else self.connection_check_interval
                )
                if now - self.last_connection_check >= check_interval:
                    self.last_connection_check = now
                    if not self.check_meshtastic_connection():
                        self.reconnect_meshtastic()
                
                if now >= self.next_check_time:
                    self.check_feed()
                
                # Sleep curto para responder rápido a Ctrl+C
                time.sleep(0.5)
            
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                time.sleep(5)
        
        # Limpeza final
        self.cleanup()
        
        self.logger.info("Aplicação encerrada.")
    
    def cleanup(self) -> None:
        """Limpeza antes de encerrar."""
        self.running = False
        if self.mesh:
            try:
                self.mesh.disconnect()
            except Exception as e:
                self.logger.error(f"Erro ao desconectar: {e}")
        self.logger.debug("Cleanup concluído")


def main():
    """Ponto de entrada principal."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    
    try:
        app = DefesaCivilAlertasStandalone(config_file)
        app.run()
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário.")
    except Exception as e:
        print(f"Erro fatal: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
