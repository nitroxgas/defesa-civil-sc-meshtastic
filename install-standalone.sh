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
IS_TEMP_SCRIPT=0
PROJECT_ROOT=""

# Verificar se este script está em um diretório temporário (wget)
if [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == /var/tmp/* ]]; then
    IS_TEMP_SCRIPT=1
fi

# Verificar se está dentro de um repositório válido
if [ -d ".git" ] && [ -f "core/__init__.py" ]; then
    PROJECT_ROOT="$(pwd)"
    echo -e "${GREEN}✓ Executando dentro do repositório${NC}"
    echo -e "${BLUE}  Caminho: $PROJECT_ROOT${NC}"
    
    # Se argumento --pull foi passado, fazer git pull
    if [[ "$*" == *"--pull"* ]]; then
        echo -e "${YELLOW}  Atualizando repositório com git pull...${NC}"
        git pull origin main
        echo -e "${GREEN}  ✓ Repositório atualizado${NC}"
    fi
else
    # Não está em um repositório, fazer clone
    if [ $IS_TEMP_SCRIPT -eq 1 ]; then
        echo -e "${YELLOW}Executando via wget - clonando repositório...${NC}"
        
        # Clonar em diretório temporário ou current
        INSTALL_DIR="${1:-.}"
        if [ ! -d "$INSTALL_DIR" ]; then
            mkdir -p "$INSTALL_DIR"
        fi
        cd "$INSTALL_DIR"
        
        if [ ! -d "defesa-civil-sc-meshtastic" ]; then
            git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
            cd defesa-civil-sc-meshtastic
        else
            cd defesa-civil-sc-meshtastic
            git pull origin main
        fi
        PROJECT_ROOT="$(pwd)"
    else
        # Script foi clonado mas não estamos no diretório certo
        echo -e "${YELLOW}Script local detectado - procurando repositório...${NC}"
        
        # Tentar achar o repositório
        if [ -d "defesa-civil-sc-meshtastic" ] && [ -f "defesa-civil-sc-meshtastic/core/__init__.py" ]; then
            cd defesa-civil-sc-meshtastic
            PROJECT_ROOT="$(pwd)"
            echo -e "${GREEN}✓ Repositório encontrado${NC}"
        else
            echo -e "${RED}Não conseguiu encontrar ou clonar o repositório${NC}"
            echo -e "${YELLOW}Use um dos seguintes métodos:${NC}"
            echo "  1. Entre no diretório clonado: cd defesa-civil-sc-meshtastic && bash install-standalone.sh"
            echo "  2. Especifique caminho: bash install-standalone.sh /caminho/desejado"
            echo "  3. Ou use wget: bash <(wget -qO- https://raw...install-standalone.sh)"
            exit 1
        fi
    fi
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
