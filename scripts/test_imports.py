#!/usr/bin/env python3
"""
Script de teste para validar que os imports de core funcionam corretamente
a partir de qualquer localização.
"""

import sys
import os
from pathlib import Path

print("=" * 70)
print("TESTE DE IMPORTAÇÕES - CORE MODULES")
print("=" * 70)
print()

# Teste 1: Import direto de core (a partir de projeto root)
print("[TESTE 1] Import direto de core (from project root)")
try:
    PROJECT_ROOT = Path(__file__).parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from core import (
        RSSParser,
        MessageFormatter,
        State,
        Alert,
        FEED_URL,
        MAX_HISTORY,
    )
    print("✓ PASSOU - Imports de core OK")
    print(f"  - RSSParser: {RSSParser}")
    print(f"  - MessageFormatter: {MessageFormatter}")
    print(f"  - State: {State}")
    print(f"  - Alert: {Alert}")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 2: Import de standalone/src
print("[TESTE 2] Import a partir de standalone/src")
try:
    standalone_src = Path(__file__).parent / "integrations/standalone-meshtastic/src"
    sys.path.insert(0, str(standalone_src))
    
    # Remove cache para forçar reimport
    if 'core' in sys.modules:
        del sys.modules['core']
    if 'state_manager' in sys.modules:
        del sys.modules['state_manager']
    
    from state_manager import StateManager
    print("✓ PASSOU - StateManager import OK")
    print(f"  - StateManager: {StateManager}")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 3: Verificar que core.__init__.py está correto
print("[TESTE 3] Verificar core.__init__.py")
try:
    core_init = Path(__file__).parent / "core/__init__.py"
    if core_init.exists():
        print(f"✓ PASSOU - core/__init__.py existe")
        print(f"  - Localização: {core_init}")
    else:
        print(f"✗ FALHOU - core/__init__.py não encontrado")
        sys.exit(1)
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 4: Verificar imports no __init__.py
print("[TESTE 4] Verificar que core.__init__.py exporta corretamente")
try:
    import core
    attrs = dir(core)
    required = ['RSSParser', 'MessageFormatter', 'State', 'Alert', 'FEED_URL', 'MAX_HISTORY']
    
    missing = [attr for attr in required if attr not in attrs]
    if missing:
        print(f"✗ FALHOU - Atributos faltando: {missing}")
        print(f"  - Disponíveis: {[a for a in attrs if not a.startswith('_')]}")
        sys.exit(1)
    else:
        print(f"✓ PASSOU - Todos os atributos exportados corretamente")
        for attr in required:
            print(f"  - {attr}: OK")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 5: Validar que RSSParser pode ser instanciado
print("[TESTE 5] Instanciar RSSParser")
try:
    parser = RSSParser()
    print(f"✓ PASSOU - RSSParser instanciado")
    print(f"  - Instância: {parser}")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 6: Validar que MessageFormatter pode ser instanciado
print("[TESTE 6] Instanciar MessageFormatter")
try:
    formatter = MessageFormatter()
    print(f"✓ PASSOU - MessageFormatter instanciado")
    print(f"  - Instância: {formatter}")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 7: Validar que State pode ser criado
print("[TESTE 7] Criar instância de State")
try:
    state = State(sent_guids=[], alerts=[], update_period="weekly", update_frequency="1")
    print(f"✓ PASSOU - State criado")
    print(f"  - Estado: {state}")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()

# Teste 8: Validar que Alert pode ser criado
print("[TESTE 8] Criar instância de Alert")
try:
    alert = Alert(
        guid="test-123",
        title="Teste",
        content="Conteúdo de teste",
        link="http://test.com",
        pub_date="2024-01-01T00:00:00Z",
        seen_at="2024-01-01T00:00:00Z"
    )
    print(f"✓ PASSOU - Alert criado")
    print(f"  - Alerta: {alert}")
except Exception as e:
    print(f"✗ FALHOU - {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✓ TODOS OS TESTES PASSARAM!")
print("=" * 70)
print()
print("Resumo:")
print("  ✓ Core imports funcionando corretamente")
print("  ✓ Standalone/src imports funcionando corretamente")
print("  ✓ Dataclasses (State, Alert) funcionando")
print("  ✓ Classes (RSSParser, MessageFormatter) funcionando")
print()
print("Próximos passos:")
print("  1. python main.py config.yaml (dentro de standalone-meshtastic/)")
print("  2. Ou: cd defesa-civil-sc-meshtastic && python integrations/standalone-meshtastic/main.py config.yaml")
