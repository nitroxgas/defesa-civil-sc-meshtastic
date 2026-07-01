"""
Defesa Civil SC - Meshtastic Standalone Integration
Módulos de integração para ler alertas da Defesa Civil SC e redistribuir via Meshtastic.
"""

__version__ = "1.0.0"
__author__ = "Comunidade defesa-civil-sc-meshtastic"

from .config_manager import ConfigManager
from .state_manager import StateManager
from .rss_parser import RSSParser
from .message_formatter import MessageFormatter
from .meshtastic_connector import MeshtasticConnector

__all__ = [
    "ConfigManager",
    "StateManager",
    "RSSParser",
    "MessageFormatter",
    "MeshtasticConnector",
]
