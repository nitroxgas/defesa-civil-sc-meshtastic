#!/bin/bash
# Script de setup geral para Defesa Civil SC Meshtastic
# Clona e prepara o repositório
# Uso: bash install.sh [/caminho/instalacao]

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

# Definir diretório
INSTALL_DIR="${1:-.}"
cd "$INSTALL_DIR"

echo -e "${YELLOW}Clonando repositório...${NC}"

if [ ! -d "defesa-civil-sc-meshtastic" ]; then
    git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
    cd defesa-civil-sc-meshtastic
else
    cd defesa-civil-sc-meshtastic
    git pull origin main
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
