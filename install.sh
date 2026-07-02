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
CURRENT_DIR="$(pwd)"
PROJECT_ROOT=""

# Prioridade 1: Verificar se o script está no repositório (caso wget)
if [ -d "$SCRIPT_DIR/.git" ] && [ -f "$SCRIPT_DIR/core/__init__.py" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"
    echo -e "${GREEN}✓ Repositório detectado (script no diretório)${NC}"
    cd "$PROJECT_ROOT"
    
    # Se argumento --pull foi passado, fazer git pull
    if [[ "$*" == *"--pull"* ]]; then
        echo -e "${YELLOW}Atualizando repositório com git pull...${NC}"
        git pull origin main
        echo -e "${GREEN}✓ Repositório atualizado${NC}"
    fi
# Prioridade 2: Verificar se o diretório atual é o repositório
elif [ -d "$CURRENT_DIR/.git" ] && [ -f "$CURRENT_DIR/core/__init__.py" ]; then
    PROJECT_ROOT="$CURRENT_DIR"
    echo -e "${GREEN}✓ Repositório detectado (diretório atual)${NC}"
    
    if [[ "$*" == *"--pull"* ]]; then
        echo -e "${YELLOW}Atualizando repositório com git pull...${NC}"
        git pull origin main
        echo -e "${GREEN}✓ Repositório atualizado${NC}"
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
echo -e "${YELLOW}📝 PRÓXIMAS ETAPAS:${NC}"
echo ""
if [[ "$choice" == "1" ]] || [[ "$choice" == "3" ]]; then
    echo -e "${BLUE}Para Home Assistant + AppDaemon:${NC}"
    echo "  1. Edite: $APPDAEMON_DIR/config/apps.yaml"
    echo "  2. Configure: notify_service, gateway_id, channel"
    echo "  3. Restart AppDaemon em Home Assistant"
    echo "  4. Verifique logs em Add-ons → AppDaemon → Logs"
    echo ""
fi
if [[ "$choice" == "2" ]] || [[ "$choice" == "3" ]]; then
    echo -e "${BLUE}Para Standalone Meshtastic:${NC}"
    echo "  1. Edite: integrations/standalone-meshtastic/config.yaml"
    echo "  2. Configure: connection_type, serial_port/tcp_host, gateway_id, channel"
    echo "  3. Execute: cd integrations/standalone-meshtastic"
    echo "            source venv/bin/activate"
    echo "            python main.py config.yaml"
    echo ""
fi
echo -e "${YELLOW}📚 DOCUMENTAÇÃO COMPLETA:${NC}"
echo "  - README.md (instruções gerais)"
echo "  - integrations/home-assistant-appdaemon/README.md (HA específico)"
echo "  - integrations/standalone-meshtastic/README.md (Standalone específico)"
echo "  - docs/ARCHITECTURE.md (arquitetura do projeto)"
echo "  - SCRIPT_FIX_REPORT.md (informações técnicas)"
echo ""
echo -e "${YELLOW}🧪 VALIDAR INSTALAÇÃO:${NC}"
echo "  Testar imports: python test_imports.py"
echo ""
echo -e "${GREEN}✓ Instalação concluída! Siga as instruções acima.${NC}"
echo ""
