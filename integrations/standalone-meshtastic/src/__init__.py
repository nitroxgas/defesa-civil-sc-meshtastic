"""
Defesa Civil SC - Meshtastic Standalone Integration
Módulos de integração para ler alertas da Defesa Civil SC e redistribuir via Meshtastic.
"""

__version__ = "1.0.0"
__author__ = "Comunidade defesa-civil-sc-meshtastic"

from .config_manager import ConfigManager
from .state_manager import StateManager
from .meshtastic_connector import MeshtasticConnector

# RSSParser e MessageFormatter são importados de core
# neste módulo para compatibilidade com imports diretos de src/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core import RSSParser, MessageFormatter

__all__ = [
    "ConfigManager",
    "StateManager",
    "RSSParser",
    "MessageFormatter",
    "MeshtasticConnector",
]
