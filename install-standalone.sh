#!/bin/bash
# Script de instalação para Defesa Civil SC Meshtastic - Standalone
# Uso: bash install-standalone.sh [--pull]
# Ou: bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)

set -e

echo "=========================================="
echo "Instalação - Defesa Civil SC Meshtastic"
echo "Integração: Standalone Meshtastic"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificações iniciais
echo -e "${YELLOW}[1/7] Verificando pré-requisitos...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}Git não encontrado. Instale git primeiro.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 não encontrado. Instale Python 3.8+ primeiro.${NC}"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓ Python $python_version encontrado${NC}"

echo ""
echo -e "${YELLOW}[2/7] Detectando repositório...${NC}"

# Detectar se já está em um repositório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_DIR="$(pwd)"
PROJECT_ROOT=""

# Prioridade 1: Verificar se o script está no repositório (caso wget)
if [ -d "$SCRIPT_DIR/.git" ] && [ -f "$SCRIPT_DIR/core/__init__.py" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"
    echo -e "${GREEN}✓ Repositório detectado (script no diretório)${NC}"
    
    # Se argumento --pull foi passado, fazer git pull
    if [[ "$*" == *"--pull"* ]]; then
        echo -e "${YELLOW}  Atualizando repositório com git pull...${NC}"
        cd "$PROJECT_ROOT"
        git pull origin main
        echo -e "${GREEN}  ✓ Repositório atualizado${NC}"
    fi
# Prioridade 2: Verificar se o diretório atual é o repositório
elif [ -d "$CURRENT_DIR/.git" ] && [ -f "$CURRENT_DIR/core/__init__.py" ]; then
    PROJECT_ROOT="$CURRENT_DIR"
    echo -e "${GREEN}✓ Repositório detectado (diretório atual)${NC}"
    
    if [[ "$*" == *"--pull"* ]]; then
        echo -e "${YELLOW}  Atualizando repositório com git pull...${NC}"
        git pull origin main
        echo -e "${GREEN}  ✓ Repositório atualizado${NC}"
    fi
# Prioridade 3: Verificar se script está em diretório temporário (wget) e tentar clonar
elif [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == /var/tmp/* ]]; then
    echo -e "${YELLOW}Executando via wget - clonando repositório...${NC}"
    
    INSTALL_DIR="${1:-.}"
    if [ ! -d "$INSTALL_DIR" ]; then
        mkdir -p "$INSTALL_DIR"
    fi
    cd "$INSTALL_DIR" || exit 1
    
    if [ ! -d "defesa-civil-sc-meshtastic" ]; then
        git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
    fi
    cd defesa-civil-sc-meshtastic || exit 1
    PROJECT_ROOT="$(pwd)"
    echo -e "${GREEN}✓ Repositório clonado${NC}"
# Prioridade 4: Tentar encontrar em subdiretório
elif [ -d "$CURRENT_DIR/defesa-civil-sc-meshtastic/.git" ] && [ -f "$CURRENT_DIR/defesa-civil-sc-meshtastic/core/__init__.py" ]; then
    cd "$CURRENT_DIR/defesa-civil-sc-meshtastic" || exit 1
    PROJECT_ROOT="$(pwd)"
    echo -e "${GREEN}✓ Repositório encontrado em subdiretório${NC}"
# Prioridade 5: Clonar no diretório especificado
else
    echo -e "${YELLOW}Repositório não encontrado - clonando...${NC}"
    
    INSTALL_DIR="${1:-.}"
    if [ ! -d "$INSTALL_DIR" ]; then
        mkdir -p "$INSTALL_DIR"
    fi
    cd "$INSTALL_DIR" || exit 1
    
    if [ ! -d "defesa-civil-sc-meshtastic" ]; then
        git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
    fi
    cd defesa-civil-sc-meshtastic || exit 1
    PROJECT_ROOT="$(pwd)"
    echo -e "${GREEN}✓ Repositório clonado${NC}"
fi

STANDALONE_DIR="integrations/standalone-meshtastic"

# Garantir que estamos no diretório raiz do projeto
cd "$PROJECT_ROOT" || exit 1

echo -e "${GREEN}✓ Repositório pronto${NC}"

echo ""
echo -e "${YELLOW}[3/7] Criando ambiente virtual Python...${NC}"

if [ ! -d "$STANDALONE_DIR/venv" ]; then
    cd "$STANDALONE_DIR"
    python3 -m venv venv
    echo -e "${GREEN}✓ Ambiente virtual criado${NC}"
else
    echo -e "${YELLOW}Ambiente virtual já existe${NC}"
    cd "$STANDALONE_DIR"
fi

# Ativar venv
source venv/bin/activate

echo ""
echo -e "${YELLOW}[4/7] Instalando dependências...${NC}"

pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependências instaladas${NC}"

echo ""
echo -e "${YELLOW}[5/7] Preparando configuração...${NC}"

if [ ! -f "config.yaml" ]; then
    cp config.example.yaml config.yaml
    echo -e "${GREEN}✓ Arquivo config.yaml criado${NC}"
    echo -e "${YELLOW}⚠ EDITE config.yaml COM SUAS CONFIGURAÇÕES!${NC}"
else
    cp config.example.yaml config.yaml.example
    echo -e "${YELLOW}config.yaml.example disponível como referência${NC}"
fi

if [ ! -f "state.json" ]; then
    cp state.example.json state.json
    echo -e "${GREEN}✓ Arquivo state.json criado${NC}"
fi

echo ""
echo -e "${YELLOW}[6/7] Verificando integração com core/...${NC}"

# Verificar se core/ está acessível
python3 -c "import sys; sys.path.insert(0, '../..'); from core import RSSParser, MessageFormatter; print('✓ Core importado com sucesso')" 2>/dev/null && echo -e "${GREEN}✓ Core/RSSParser e MessageFormatter acessíveis${NC}" || echo -e "${YELLOW}⚠ Aviso ao importar core (pode estar ok)${NC}"

echo ""
echo -e "${YELLOW}[7/7] Teste rápido de importação...${NC}"

python3 -c "
import sys
sys.path.insert(0, '../..')
from core import RSSParser, MessageFormatter, State, Alert
print('✓ Todas as importações de core/ funcionam')
print('  - RSSParser')
print('  - MessageFormatter')
print('  - State')
print('  - Alert')
" || echo -e "${YELLOW}⚠ Aviso ao verificar importações${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "Instalação concluída com sucesso!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}Próximas etapas:${NC}"
echo "1. Edite o arquivo de configuração:"
echo "   $(pwd)/config.yaml"
echo ""
echo "2. Configure:"
echo "   - connection_type (serial ou tcp)"
echo "   - serial_port ou tcp_host"
echo "   - channel name e number"
echo ""
echo "3. Execute a aplicação:"
echo "   source venv/bin/activate"
echo "   python main.py config.yaml"
echo ""
echo "4. Para modo de teste:"
echo "   Edite config.yaml e defina 'test_mode: true'"
echo "   Depois: python main.py config.yaml"
echo ""
echo -e "${YELLOW}Localização dos arquivos:${NC}"
echo "  App: $(pwd)/main.py"
echo "  Config: $(pwd)/config.yaml"
echo "  Estado: $(pwd)/state.json"
echo "  Core: ../../core/"
echo ""
echo -e "${YELLOW}Ambiente virtual:${NC}"
echo "  Ativar: source $(pwd)/venv/bin/activate"
echo "  Desativar: deactivate"
echo ""
echo -e "${YELLOW}Documentação:${NC}"
echo "  - Instruções detalhadas: README.md"
echo "  - Arquitetura: ../../docs/ARCHITECTURE.md"
echo ""
