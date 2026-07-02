"""
Conector Meshtastic para enviar mensagens e ouvir eventos.
Responsável pela comunicação com o gateway Meshtastic via serial ou TCP.
"""

import meshtastic
import meshtastic.serial_interface
import meshtastic.tcp_interface
from typing import Optional, Callable, Any
import logging


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
            
            # Registrar callback para mensagens recebidas
            if self.on_message_callback:
                self.interface.on_receive = self.on_message_callback
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Meshtastic: {e}")
            self.interface = None
            return False
    
    def disconnect(self) -> None:
        """Desconecta do gateway Meshtastic."""
        try:
            if self.interface:
                self.interface.close()
                self.logger.info("Desconectado do Meshtastic.")
        except Exception as e:
            self.logger.error(f"Erro ao desconectar: {e}")
        finally:
            self.interface = None
    
    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        return self.interface is not None
    
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
        try:
            if not self.is_connected():
                self.logger.error("Não conectado ao Meshtastic.")
                return False
            
            self.logger.debug(
                f"Enviando texto para canal {channel_id}: {message[:80]}..."
            )
            
            self.interface.sendText(
                message,
                destinationId="^all",  # Broadcast para o canal
                channelIndex=channel_id,
                wantAck=want_ack
            )
            
            self.logger.debug(f"Texto enviado para canal {channel_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem para canal: {e}")
            return False
    
    def send_direct_message(
        self,
        message: str,
        node_id: str,
        want_ack: bool = True
    ) -> bool:
        """
        Envia mensagem de texto direta para um node.
        
        Args:
            message: Texto da mensagem
            node_id: ID do node destino
            want_ack: Se quer receber confirmação de entrega
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            if not self.is_connected():
                self.logger.error("Não conectado ao Meshtastic.")
                return False
            
            self.logger.debug(
                f"Enviando DM para {node_id}: {message[:80]}..."
            )
            
            self.interface.sendText(
                message,
                destinationId=str(node_id),
                wantAck=want_ack
            )
            
            self.logger.debug(f"DM enviado para {node_id}")
            return True
        
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
        self.on_message_callback = callback
        if self.interface:
            self.interface.on_receive = callback
    
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
