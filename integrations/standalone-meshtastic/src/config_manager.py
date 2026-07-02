"""
Gerenciador de configuração da aplicação.
Carrega e valida arquivo YAML de configuração.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Gerencia configuração da aplicação a partir de arquivo YAML."""
    
    DEFAULT_CONFIG = {
        "meshtastic": {
            "connection_type": "serial",
            "serial_port": "",
            "tcp_host": None,
            "tcp_port": 4403,
            "host": None,
            "port": 4403
        },
        "channel": {
            "name": "Alertas-SC",
            "number": 0
        },
        "feed": {
            "url": "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/",
            "default_interval_minutes": 60,
            "min_interval_minutes": 15,
            "max_interval_minutes": 1440,
            "timeout_seconds": 30
        },
        "state": {
            "file": "./state.json",
            "max_history": 10
        },
        "direct_message": {
            "enabled": True,
            "trigger_word": "ALERTAS",
            "max_alerts_reply": 3
        },
        "test_mode": False,
        "logging": {
            "level": "DEBUG",
            "file": None
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa o gerenciador de configuração.
        
        Args:
            config_file: Caminho do arquivo de configuração YAML.
                        Se None, tenta encontrar 'config.yaml' no diretório atual.
        """
        self.config_file = config_file or "config.yaml"
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self) -> None:
        """Carrega configuração do arquivo YAML."""
        if not os.path.exists(self.config_file):
            print(f"Arquivo de configuração não encontrado: {self.config_file}")
            print("Usando configuração padrão.")
            return
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f) or {}
            
            # Deep merge com configuração padrão
            self._deep_merge(self.config, loaded_config)
            
            # Normalizar configuração TCP (converter host/port para tcp_host/tcp_port)
            self._normalize_tcp_config()
            
            print(f"Configuração carregada de: {self.config_file}")
        
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            print("Usando configuração padrão.")
    
    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Faz merge profundo de dicionários.
        Modifica 'target' in-place, adicionando/sobrescrevendo valores de 'source'.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração usando notação de ponto.
        
        Exemplo: get("meshtastic.serial_port")
        
        Args:
            key_path: Caminho da chave (pode ser "seção.subsecao.chave")
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração
        """
        keys = key_path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtém seção inteira de configuração.
        
        Args:
            section: Nome da seção (ex: "meshtastic", "feed")
            
        Returns:
            Dicionário com configurações da seção
        """
        return self.config.get(section, {})
    
    def get_meshtastic_config(self) -> Dict[str, Any]:
        """Retorna configuração do Meshtastic."""
        return self.get_section("meshtastic")
    
    def get_channel_config(self) -> Dict[str, Any]:
        """Retorna configuração do canal."""
        return self.get_section("channel")
    
    def get_feed_config(self) -> Dict[str, Any]:
        """Retorna configuração do feed."""
        return self.get_section("feed")
    
    def get_state_config(self) -> Dict[str, Any]:
        """Retorna configuração de persistência de estado."""
        return self.get_section("state")
    
    def get_dm_config(self) -> Dict[str, Any]:
        """Retorna configuração de mensagens diretas."""
        return self.get_section("direct_message")
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Retorna configuração de logging."""
        return self.get_section("logging")
    
    def is_test_mode(self) -> bool:
        """Retorna se está em modo de teste."""
        return self.get("test_mode", False)
    
    def _normalize_tcp_config(self) -> None:
        """
        Normaliza configuração de TCP.
        Converte host/port para tcp_host/tcp_port para manter compatibilidade.
        """
        mesh_config = self.config.get("meshtastic", {})
        
        if mesh_config.get("host") is not None:
            mesh_config["tcp_host"] = mesh_config["host"]
        
        if mesh_config.get("port") is not None:
            mesh_config["tcp_port"] = mesh_config["port"]
    
    def validate(self) -> bool:
        """
        Valida configuração.
        
        Returns:
            True se configuração válida, False caso contrário
        """
        # Normalizar configuração TCP
        self._normalize_tcp_config()
        
        # Validar tipo de conexão Meshtastic
        connection_type = self.get("meshtastic.connection_type", "").lower()
        if connection_type not in ("serial", "tcp"):
            print(f"Tipo de conexão inválido: {connection_type}")
            return False
        
        # Validar se TCP tem host configurado (aceita tcp_host ou host)
        if connection_type == "tcp":
            tcp_host = self.get("meshtastic.tcp_host") or self.get("meshtastic.host")
            if not tcp_host:
                print("Conexão TCP requer 'host' ou 'tcp_host' configurado")
                return False
        
        # Validar URL do feed
        feed_url = self.get("feed.url")
        if not feed_url or not feed_url.startswith("http"):
            print("URL do feed inválida")
            return False
        
        # Validar níveis de logging
        log_level = self.get("logging.level", "INFO").upper()
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if log_level not in valid_levels:
            print(f"Nível de logging inválido: {log_level}")
            return False
        
        return True
