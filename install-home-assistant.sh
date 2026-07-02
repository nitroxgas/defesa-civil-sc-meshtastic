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
echo -e "${YELLOW}📝 CONFIGURAÇÃO NECESSÁRIA:${NC}"
echo "1. Edite o arquivo de configuração do AppDaemon:"
echo "   $APPS_DIR/../apps.yaml"
echo ""
echo "2. Configure os campos obrigatórios:"
echo "   - notify_service: entidade notify (ex: notify.mesh_channel_alertas_sc)"
echo "   - gateway_id: ID numérico do seu Meshtastic"
echo "   - channel: número do canal para enviar alertas"
echo ""
echo "3. Verifique a entidade notify no Home Assistant:"
echo "   - Vá em Developer Tools → States"
echo "   - Procure por 'notify.*' para listar entidades disponíveis"
echo "   - Use a entidade correta no apps.yaml"
echo ""
echo -e "${YELLOW}🔄 ATIVANDO A INTEGRAÇÃO:${NC}"
echo "1. Aguarde alguns segundos..."
echo "2. Vá em Settings → Developer Tools → YAML"
echo "3. Se necessário, restart AppDaemon:"
echo "   - Settings → Add-ons → AppDaemon → Reiniciar"
echo ""
echo "4. Verificar logs do AppDaemon:"
echo "   - Settings → Add-ons → AppDaemon → Logs"
echo "   - Procure por 'DefesaCivilSCAlertas' ou 'defesa_civil_sc_alertas'"
echo ""
echo -e "${YELLOW}📂 LOCALIZAÇÃO DOS ARQUIVOS:${NC}"
echo "  App: $APPS_DIR/defesa_civil_sc_alertas.py"
echo "  Config: $APPS_DIR/../apps.yaml"
echo "  Core (compartilhado): $APPDAEMON_DIR/config/core/"
echo "  Repositório origem: $(pwd)"
echo ""
echo -e "${YELLOW}🧪 MODO DE TESTE:${NC}"
echo "  Para testar sem conectar ao Meshtastic:"
echo "  1. Edite apps.yaml e defina: test_mode: true"
echo "  2. Restart AppDaemon"
echo "  3. A aplicação simula conexão"
echo ""
echo -e "${YELLOW}🔧 COMANDOS ÚTEIS:${NC}"
echo "  Ver logs em tempo real:"
echo "    docker exec appdaemon tail -f /config/logs/main.log"
echo ""
echo "  Listar entidades notify:"
echo "    Home Assistant → Developer Tools → States → Procurar 'notify'"
echo ""
echo "  Testar envio de notificação:"
echo "    Home Assistant → Developer Tools → Services"
echo "    Serviço: notify.seu_entidade"
echo "    Dados: { message: 'Teste' }"
echo ""
echo -e "${YELLOW}📚 DOCUMENTAÇÃO:${NC}"
echo "  - README detalhado: integrations/home-assistant-appdaemon/README.md"
echo "  - Arquitetura do projeto: docs/ARCHITECTURE.md"
echo "  - AppDaemon oficial: https://appdaemon.readthedocs.io"
echo ""
echo -e "${YELLOW}⚠️  TROUBLESHOOTING:${NC}"
echo "  App não aparece em Home Assistant?"
echo "  1. Verifique logs do AppDaemon"
echo "  2. Confirme nome correto em apps.yaml"
echo "  3. Verifique indentação YAML"
echo ""
echo "  Erro de entidade notify?"
echo "  1. Verifique se entidade realmente existe (States)"
echo "  2. Teste envio manual em Services"
echo "  3. Verifique permissões do usuário"
echo ""
echo "  Erro de importação de core?"
echo "  Execute: python $APPDAEMON_DIR/../../test_imports.py"
echo ""
echo -e "${GREEN}✓ Instalação concluída! Agora configure e reinicie AppDaemon.${NC}"
echo ""
