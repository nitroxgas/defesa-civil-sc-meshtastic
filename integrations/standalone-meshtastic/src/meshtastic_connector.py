"""
Conector Meshtastic para enviar mensagens e ouvir eventos.
Responsável pela comunicação com o gateway Meshtastic via serial ou TCP.
"""

import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
from typing import Optional, Callable, Any
import logging
import threading

from pubsub import pub


class MeshtasticConnector:
    """Gerencia conexão e comunicação com Meshtastic."""
    
    def __init__(
        self,
        connection_type: str = "serial",
        serial_port: Optional[str] = None,
        tcp_host: Optional[str] = None,
        tcp_port: int = 4403,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa o conector Meshtastic.
        
        Args:
            connection_type: "serial" ou "tcp"
            serial_port: Porta serial (deixar vazio para auto-detect)
            tcp_host: Host TCP
            tcp_port: Porta TCP (padrão 4403)
            logger: Logger para mensagens
        """
        self.connection_type = connection_type.lower()
        self.serial_port = serial_port or None
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.logger = logger or logging.getLogger(__name__)
        self.interface = None
        self.on_message_callback = None
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """
        Conecta ao gateway Meshtastic.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            if self.connection_type == "serial":
                self.logger.info(
                    f"Conectando via serial (porta: {self.serial_port or 'auto-detect'})..."
                )
                self.interface = meshtastic.serial_interface.SerialInterface(
                    devPath=self.serial_port or None
                )
            elif self.connection_type == "tcp":
                self.logger.info(f"Conectando via TCP ({self.tcp_host}:{self.tcp_port})...")
                try:
                    # Try with portNumber first (newer versions of Meshtastic)
                    self.interface = meshtastic.tcp_interface.TCPInterface(
                        hostname=self.tcp_host,
                        portNumber=self.tcp_port
                    )
                except TypeError as e:
                    if "portNumber" in str(e):
                        # Fallback to port (older versions of Meshtastic)
                        self.logger.debug("portNumber not supported, trying port parameter...")
                        self.interface = meshtastic.tcp_interface.TCPInterface(
                            hostname=self.tcp_host,
                            port=self.tcp_port
                        )
                    else:
                        raise
            else:
                self.logger.error(f"Tipo de conexão desconhecido: {self.connection_type}")
                return False
            
            self.logger.info("Conectado ao Meshtastic com sucesso!")
            
            # Registrar callback para mensagens recebidas via pubsub
            if self.on_message_callback:
                pub.subscribe(self.on_message_callback, "meshtastic.receive.text")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Meshtastic: {e}")
            self.interface = None
            return False
    
    def disconnect(self) -> None:
        """Desconecta do gateway Meshtastic."""
        with self._lock:
            try:
                if self.on_message_callback:
                    try:
                        pub.unsubscribe(self.on_message_callback, "meshtastic.receive.text")
                    except Exception:
                        pass
                if self.interface:
                    self.interface.close()
                    self.logger.info("Desconectado do Meshtastic.")
            except Exception as e:
                self.logger.error(f"Erro ao desconectar: {e}")
            finally:
                self.interface = None
    
    def is_connected(self) -> bool:
        """Verifica se a conexão com o Meshtastic ainda está ativa."""
        if self.interface is None:
            return False
        try:
            # Tentar acessar myInfo e, se disponível, validar socket serial
            _ = self.interface.myInfo
            if hasattr(self.interface, "socket") and self.interface.socket:
                # getpeername() levanta exceção se o socket estiver fechado
                self.interface.socket.getpeername()
            return True
        except Exception:
            return False
    
    def resolve_channel_id(self, name_or_number: Any, default: int = 0) -> int:
        """
        Resolve nome ou número do canal para o índice usado pela biblioteca.
        
        Args:
            name_or_number: Nome do canal (string) ou índice numérico
            default: Índice padrão se não for possível resolver
            
        Returns:
            Índice do canal para sendText
        """
        try:
            return int(name_or_number)
        except (ValueError, TypeError):
            pass
        
        if not name_or_number or not self.is_connected():
            return default
        
        try:
            local_channels = getattr(self.interface, "_localChannels", None)
            if local_channels:
                for ch in local_channels:
                    ch_name = ""
                    if hasattr(ch, "settings") and hasattr(ch.settings, "name"):
                        ch_name = ch.settings.name
                    elif hasattr(ch, "name"):
                        ch_name = ch.name
                    
                    if ch_name and ch_name == name_or_number:
                        idx = getattr(ch, "index", None)
                        if idx is not None:
                            return int(idx)
                
                self.logger.warning(
                    f"Canal '{name_or_number}' não encontrado; usando {default}"
                )
        except Exception as e:
            self.logger.error(f"Erro ao resolver canal: {e}")
        
        return default
    
    def send_to_channel(
        self,
        message: str,
        channel_id: int = 0,
        want_ack: bool = False
    ) -> bool:
        """
        Envia mensagem de texto para um canal.
        
        Args:
            message: Texto da mensagem
            channel_id: ID do canal (padrão 0)
            want_ack: Se quer receber confirmação de entrega
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        with self._lock:
            try:
                if not self.is_connected():
                    self.logger.error("Não conectado ao Meshtastic.")
                    return False
                
                self.logger.info(
                    f"Enviando texto para canal {channel_id}: {message[:80]}..."
                )
                
                self.interface.sendText(
                    message,
                    destinationId="^all",  # Broadcast para o canal
                    channelIndex=channel_id,
                    wantAck=want_ack
                )
                
                self.logger.info(f"Texto enviado para canal {channel_id}")
                return True
            
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                self.logger.error(f"Conexão perdida ao enviar para canal: {e}")
                self.interface = None
                return False
            except Exception as e:
                self.logger.error(f"Erro ao enviar mensagem para canal: {e}")
                return False
    
    def send_alert(
        self,
        message: str,
        channel_id: int = 0,
        node_id: Optional[str] = None,
    ) -> bool:
        """
        Envia mensagem de alerta com notificação especial do Meshtastic.

        Usa ALERT_APP e prioridade ALERT para que clientes configurados
        possam tocar/buzzar ao receber. Se node_id for informado, o alerta
        é enviado como mensagem direta; caso contrário, é broadcast no canal.

        Args:
            message: Texto do alerta
            channel_id: ID do canal (padrão 0)
            node_id: ID do node destino para DM (opcional)

        Returns:
            True se enviado com sucesso, False caso contrário
        """
        with self._lock:
            try:
                if not self.is_connected():
                    self.logger.error("Não conectado ao Meshtastic.")
                    return False

                destination_id = node_id if node_id is not None else "^all"
                target_label = f"node {destination_id}" if node_id else f"canal {channel_id}"

                self.logger.info(
                    f"Enviando alerta de notificação para {target_label}: {message[:80]}..."
                )

                try:
                    self.interface.sendAlert(
                        message,
                        destinationId=str(destination_id),
                        channelIndex=channel_id,
                    )
                except AttributeError as ae:
                    self.logger.warning(
                        f"sendAlert não suportado ({ae}); usando sendText como fallback"
                    )
                    self.interface.sendText(
                        message,
                        destinationId=str(destination_id),
                        channelIndex=channel_id,
                        wantAck=False,
                    )

                self.logger.info(f"Alerta de notificação enviado para {target_label}")
                return True

            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                self.logger.error(f"Conexão perdida ao enviar alerta: {e}")
                self.interface = None
                return False
            except Exception as e:
                self.logger.error(f"Erro ao enviar alerta de notificação: {e}")
                return False

    def send_direct_message(
        self,
        message: str,
        node_id: str,
        want_ack: bool = False
    ) -> bool:
        """
        Envia mensagem de texto direta para um node.
        
        Args:
            message: Texto da mensagem
            node_id: ID do node destino
            want_ack: Se quer receber confirmação de entrega (padrão: False
                      para evitar bloqueio no callback de recebimento)
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        with self._lock:
            try:
                if not self.is_connected():
                    self.logger.error("Não conectado ao Meshtastic.")
                    return False
                
                self.logger.info(
                    f"Enviando DM para {node_id}: {message[:80]}..."
                )
                
                self.interface.sendText(
                    message,
                    destinationId=str(node_id),
                    wantAck=want_ack
                )
                
                self.logger.info(f"DM enviado para {node_id}")
                return True
            
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                self.logger.error(f"Conexão perdida ao enviar DM: {e}")
                self.interface = None
                return False
            except Exception as e:
                self.logger.error(f"Erro ao enviar mensagem direta: {e}")
                return False
    
    def get_node_info(self, node_id: str) -> Optional[dict]:
        """
        Obtém informações sobre um node.
        
        Args:
            node_id: ID do node
            
        Returns:
            Dicionário com informações do node, ou None se não encontrado
        """
        try:
            if not self.is_connected():
                return None
            
            nodes = self.interface.nodes
            return nodes.get(node_id, None)
        
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do node: {e}")
            return None
    
    def register_receive_callback(self, callback: Callable[[dict, Any], None]) -> None:
        """
        Registra callback para mensagens recebidas.
        
        Args:
            callback: Função que será chamada quando uma mensagem for recebida.
                     Assinatura: callback(packet_dict, interface)
        """
        if self.on_message_callback:
            try:
                pub.unsubscribe(self.on_message_callback, "meshtastic.receive.text")
            except Exception:
                pass
        self.on_message_callback = callback
        if self.interface:
            pub.subscribe(callback, "meshtastic.receive.text")
    
    def get_my_info(self) -> Optional[dict]:
        """
        Obtém informações do node local (gateway).
        
        Returns:
            Dicionário com informações do node local, ou None se erro
        """
        try:
            if not self.is_connected():
                return None
            
            my_info = self.interface.myInfo
            return my_info
        
        except Exception as e:
            self.logger.error(f"Erro ao obter informações locais: {e}")
            return None
    
    def get_channels(self) -> Optional[list]:
        """
        Obtém lista de canais configurados.
        
        Returns:
            Lista de canais, ou None se erro
        """
        try:
            if not self.is_connected():
                return None
            
            channels = self.interface.channels
            return channels
        
        except Exception as e:
            self.logger.error(f"Erro ao obter canais: {e}")
            return None
