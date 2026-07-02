#!/bin/bash
# Script de setup geral para Defesa Civil SC Meshtastic
# Menu para escolher integração
# Uso: bash install.sh [--pull]
# Ou: bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install.sh)

set -e

echo "=========================================="
echo "Defesa Civil SC Meshtastic"
echo "Setup Inicial"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificações iniciais
echo -e "${YELLOW}Verificando pré-requisitos...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}Git não encontrado. Instale git primeiro.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Git encontrado${NC}"

echo -e "${YELLOW}Detectando repositório...${NC}"

# Detectar se já está em um repositório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IS_TEMP_SCRIPT=0

# Verificar se este script está em um diretório temporário (wget)
if [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == /var/tmp/* ]]; then
    IS_TEMP_SCRIPT=1
fi

# Verificar se está dentro de um repositório válido
if [ -d ".git" ] && [ -f "core/__init__.py" ]; then
    echo -e "${GREEN}✓ Executando dentro do repositório${NC}"
    
    # Se argumento --pull foi passado, fazer git pull
    if [[ "$*" == *"--pull"* ]]; then
        echo -e "${YELLOW}Atualizando repositório com git pull...${NC}"
        git pull origin main
        echo -e "${GREEN}✓ Repositório atualizado${NC}"
    fi
else
    # Não está em um repositório, fazer clone
    if [ $IS_TEMP_SCRIPT -eq 1 ]; then
        echo -e "${YELLOW}Executando via wget - clonando repositório...${NC}"
        
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
    else
        # Script foi clonado mas não estamos no diretório certo
        echo -e "${YELLOW}Script local detectado - procurando repositório...${NC}"
        
        # Tentar achar o repositório
        if [ -d "defesa-civil-sc-meshtastic" ] && [ -f "defesa-civil-sc-meshtastic/core/__init__.py" ]; then
            cd defesa-civil-sc-meshtastic
            echo -e "${GREEN}✓ Repositório encontrado${NC}"
        else
            echo -e "${RED}Não conseguiu encontrar ou clonar o repositório${NC}"
            echo -e "${YELLOW}Use um dos seguintes métodos:${NC}"
            echo "  1. Entre no diretório clonado: cd defesa-civil-sc-meshtastic && bash install.sh"
            echo "  2. Ou use wget: bash <(wget -qO- https://raw...install.sh)"
            exit 1
        fi
    fi
fi

echo -e "${GREEN}✓ Repositório pronto${NC}"
echo ""

# Menu de instalação
echo -e "${BLUE}Qual integração deseja instalar?${NC}"
echo "1) Home Assistant + AppDaemon"
echo "2) Standalone Meshtastic"
echo "3) Ambas"
echo ""
read -p "Escolha (1-3): " choice

case $choice in
    1)
        echo -e "${YELLOW}Instalando Home Assistant + AppDaemon...${NC}"
        bash install-home-assistant.sh
        ;;
    2)
        echo -e "${YELLOW}Instalando Standalone Meshtastic...${NC}"
        bash install-standalone.sh
        ;;
    3)
        echo -e "${YELLOW}Instalando ambas as integrações...${NC}"
        bash install-home-assistant.sh
        echo ""
        bash install-standalone.sh
        ;;
    *)
        echo -e "${RED}Opção inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=========================================="
echo "Setup concluído!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}Próximas etapas:${NC}"
echo "1. Consulte o README.md da sua integração"
echo "2. Configure conforme necessário"
echo "3. Teste a integração"
echo ""
echo -e "${YELLOW}Documentação:${NC}"
echo "  - README.md (instruções gerais)"
echo "  - integrations/home-assistant-appdaemon/README.md"
echo "  - integrations/standalone-meshtastic/README.md"
echo "  - docs/ARCHITECTURE.md"
echo ""
