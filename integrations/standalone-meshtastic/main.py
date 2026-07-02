#!/usr/bin/env python3
"""
Defesa Civil SC - Meshtastic Standalone
Integração para ler alertas da Defesa Civil SC e redistribuir via Meshtastic.
"""

import sys
import os
import time
import logging
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
from core import RSSParser, MessageFormatter, MAX_HISTORY, CHANNEL_LINK_DELAY_SECONDS, CHANNEL_ALERT_BATCH_DELAY_SECONDS

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
            timeout_seconds=self.config.get("feed.timeout_seconds", 30)
        )
        self.formatter = MessageFormatter()
        self.mesh = None
        self.running = False
        self.next_check_time = time.time()
    
    def _setup_logging(self) -> None:
        """Configura logging da aplicação."""
        log_level = self.config.get("logging.level", "INFO").upper()
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
    
    def connect_meshtastic(self) -> bool:
        """Conecta ao Meshtastic."""
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
        
        return True
    
    def on_message_received(self, packet: dict, interface) -> None:
        """
        Callback para mensagens recebidas.
        
        Args:
            packet: Pacote recebido
            interface: Interface Meshtastic
        """
        try:
            # Verificar se é mensagem de texto
            if "decoded" not in packet:
                return
            
            decoded = packet["decoded"]
            if "payload" not in decoded:
                return
            
            # Se for mensagem direta com texto
            if decoded.get("portNum") == 1:  # Text message port
                try:
                    message_text = decoded["payload"].decode("utf-8")
                except:
                    return
                
                trigger_word = self.config.get("direct_message.trigger_word", "ALERTAS")
                
                if message_text.strip().upper() == trigger_word:
                    self.handle_dm_alerts_request(packet, interface)
        
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
            if not from_id:
                return
            
            # Obter alertas recentes
            max_alerts = self.config.get("direct_message.max_alerts_reply", 3)
            alerts = self.state_manager.get_latest_alerts(max_alerts)
            
            if not alerts:
                self.logger.info(f"Sem alertas para responder a {from_id}")
                return
            
            self.logger.info(f"Enviando {len(alerts)} alerta(s) via DM para {from_id}")
            
            for idx, alert in enumerate(alerts):
                # Enviar em duas mensagens
                msg1, msg2 = self.formatter.build_alert_messages(alert)
                
                self.mesh.send_direct_message(msg1, str(from_id))
                time.sleep(CHANNEL_LINK_DELAY_SECONDS)
                
                self.mesh.send_direct_message(msg2, str(from_id))
                
                if idx < len(alerts) - 1:
                    time.sleep(CHANNEL_ALERT_BATCH_DELAY_SECONDS)
        
        except Exception as e:
            self.logger.error(f"Erro ao responder DM de alertas: {e}")
    
    def send_alert_to_channel(self, alert: dict, channel_id: int = 0) -> None:
        """
        Envia alerta para canal Meshtastic.
        
        Args:
            alert: Dicionário com dados do alerta
            channel_id: ID do canal
        """
        try:
            msg1, msg2 = self.formatter.build_alert_messages(alert)
            
            # Enviar mensagem de conteúdo
            self.mesh.send_to_channel(msg1, channel_id)
            self.logger.info(f"Alerta enviado: {msg1[:80]}...")
            
            # Aguardar antes de enviar link
            time.sleep(CHANNEL_LINK_DELAY_SECONDS)
            
            # Enviar link
            self.mesh.send_to_channel(msg2, channel_id)
            self.logger.debug(f"Link enviado: {msg2}")
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta: {e}")
    
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
            channel_id = channel_config.get("number", 0)
            
            # Primeira execução: carregar histórico sem enviar
            is_first_run = len(self.state_manager.get_alerts()) == 0
            
            new_alerts_count = 0
            
            for item in items:
                guid = item.get("guid")
                
                if self.state_manager.is_guid_sent(guid):
                    self.logger.debug(f"Alerta já enviado: {guid}")
                    continue
                
                # Se for primeira execução, apenas armazenar
                if is_first_run:
                    self.logger.debug(f"Primeira execução: armazenando alerta {guid}")
                else:
                    # Enviar alerta
                    self.logger.info(f"Novo alerta detectado: {item.get('title', '')[:60]}...")
                    self.send_alert_to_channel(item, channel_id)
                    new_alerts_count += 1
                    
                    # Aguardar antes do próximo alerta
                    if new_alerts_count < len(items):
                        time.sleep(CHANNEL_ALERT_BATCH_DELAY_SECONDS)
                
                # Marcar como enviado e armazenar
                self.state_manager.add_sent_guid(guid)
                self.state_manager.add_alert(item, self.config.get("state.max_history", MAX_HISTORY))
            
            # Salvar estado
            self.state_manager.save()
            
            if new_alerts_count > 0:
                self.logger.info(f"{new_alerts_count} novo(s) alerta(s) enviado(s)")
            
            # Calcular próximo horário de verificação
            self.next_check_time = time.time() + (interval_minutes * 60)
        
        except Exception as e:
            self.logger.error(f"Erro ao verificar feed: {e}")
            # Usar intervalo padrão em caso de erro
            default_interval = self.config.get("feed.default_interval_minutes", 60)
            self.next_check_time = time.time() + (default_interval * 60)
    
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
                channel_id = channel_config.get("number", 0)
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
        
        # Handler para Ctrl+C
        def signal_handler(sig, frame):
            self.logger.info("Encerrando aplicação...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
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
                
                if now >= self.next_check_time:
                    self.check_feed()
                
                # Sleep para não usar 100% CPU
                time.sleep(5)
            
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                time.sleep(10)
        
        # Limpeza
        if self.mesh:
            self.mesh.disconnect()
        
        self.logger.info("Aplicação encerrada.")
    
    def cleanup(self) -> None:
        """Limpeza antes de encerrar."""
        self.running = False
        if self.mesh:
            self.mesh.disconnect()


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
