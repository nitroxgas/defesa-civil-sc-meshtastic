"""Fixtures e configurações para testes."""

import sys
from pathlib import Path

# Adicionar core ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
