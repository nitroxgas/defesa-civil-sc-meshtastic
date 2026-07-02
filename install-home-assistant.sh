#!/bin/bash
# Script de instalação para Defesa Civil SC Meshtastic - Home Assistant AppDaemon
# Uso: bash install-home-assistant.sh [--pull]
# Ou: bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.sh)

set -e

echo "=========================================="
echo "Instalação - Defesa Civil SC Meshtastic"
echo "Integração: Home Assistant + AppDaemon"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificações iniciais
echo -e "${YELLOW}[1/5] Verificando pré-requisitos...${NC}"

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
echo -e "${YELLOW}[2/5] Detectando repositório...${NC}"

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
    echo -e "${YELLOW}  Caminho: $PROJECT_ROOT${NC}"
    
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
        
        # Clonar em diretório current
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
            echo "  1. Entre no diretório clonado: cd defesa-civil-sc-meshtastic && bash install-home-assistant.sh"
            echo "  2. Especifique caminho: bash install-home-assistant.sh /caminho/desejado"
            echo "  3. Ou use wget: bash <(wget -qO- https://raw...install-home-assistant.sh)"
            exit 1
        fi
    fi
fi

# Garantir que estamos no diretório raiz do projeto
cd "$PROJECT_ROOT" || exit 1

echo -e "${GREEN}✓ Repositório pronto${NC}"

echo ""
echo -e "${YELLOW}[3/5] Localizando AppDaemon...${NC}"

# Procurar Home Assistant AppDaemon
if [ -d "/root/addon_config" ]; then
    APPDAEMON_DIR=$(find /root/addon_config -name "appdaemon" -type d 2>/dev/null | head -1)
    if [ -n "$APPDAEMON_DIR" ]; then
        echo -e "${GREEN}✓ AppDaemon encontrado em: $APPDAEMON_DIR${NC}"
    fi
fi

if [ -z "$APPDAEMON_DIR" ]; then
    echo -e "${YELLOW}AppDaemon não encontrado automaticamente.${NC}"
    read -p "Digite o caminho do AppDaemon (ex: /root/addon_config/.../appdaemon): " APPDAEMON_DIR
fi

if [ ! -d "$APPDAEMON_DIR" ]; then
    echo -e "${RED}Diretório AppDaemon inválido: $APPDAEMON_DIR${NC}"
    exit 1
fi

APPS_DIR="$APPDAEMON_DIR/config/apps"
mkdir -p "$APPS_DIR"

echo ""
echo -e "${YELLOW}[4/5] Copiando arquivos...${NC}"

# Copiar app principal
cp integrations/home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py "$APPS_DIR/"
echo -e "${GREEN}✓ App copiado para: $APPS_DIR/defesa_civil_sc_alertas.py${NC}"

# Copiar core/ para AppDaemon (para importação)
if [ ! -d "$APPDAEMON_DIR/config/core" ]; then
    cp -r core "$APPDAEMON_DIR/config/"
    echo -e "${GREEN}✓ Módulos compartilhados (core/) copiados${NC}"
else
    echo -e "${YELLOW}Core já existe, atualizando...${NC}"
    cp -r core/* "$APPDAEMON_DIR/config/core/"
fi

# Copiar exemplo de configuração
if [ ! -f "$APPS_DIR/apps.yaml" ]; then
    cp integrations/home-assistant-appdaemon/config/apps.yaml.example "$APPS_DIR/../apps.yaml"
    echo -e "${YELLOW}⚠ Arquivo apps.yaml criado (exemplo). EDITE COM SUAS CONFIGURAÇÕES!${NC}"
else
    cp integrations/home-assistant-appdaemon/config/apps.yaml.example "$APPS_DIR/../apps.yaml.example"
    echo -e "${YELLOW}⚠ Arquivo apps.yaml.example disponível como referência${NC}"
fi

echo ""
echo -e "${YELLOW}[5/5] Configuração final...${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "Instalação concluída com sucesso!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}Próximas etapas:${NC}"
echo "1. Edite o arquivo de configuração:"
echo "   $APPS_DIR/../apps.yaml"
echo ""
echo "2. Substitua:"
echo "   - notify.mesh_channel_alertas_sc → sua entidade notify real"
echo "   - 0000000000 → ID numérico do seu gateway Meshtastic"
echo ""
echo "3. Reinicie o AppDaemon no Home Assistant"
echo ""
echo -e "${YELLOW}Localização dos arquivos:${NC}"
echo "  App: $APPS_DIR/defesa_civil_sc_alertas.py"
echo "  Config: $APPS_DIR/../apps.yaml"
echo "  Core: $APPDAEMON_DIR/config/core/"
echo "  Repositório: $(pwd)"
echo ""
echo -e "${YELLOW}Documentação:${NC}"
echo "  - Instruções detalhadas: integrations/home-assistant-appdaemon/README.md"
echo "  - Arquitetura: docs/ARCHITECTURE.md"
echo ""
