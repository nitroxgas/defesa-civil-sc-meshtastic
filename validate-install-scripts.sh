#!/bin/bash
# Script de teste para validar todos os scripts de instalação
# Testa detecção de repositório, clone, e paths

set -e

echo "================================"
echo "TESTE DE SCRIPTS DE INSTALAÇÃO"
echo "================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Contadores
PASSED=0
FAILED=0

# Função para teste
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    echo -n "Testando $test_name... "
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSOU${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FALHOU${NC}"
        ((FAILED++))
    fi
}

# Teste 1: Validar sintaxe Bash
run_test "install-standalone.sh (sintaxe)" "bash -n install-standalone.sh"
run_test "install-home-assistant.sh (sintaxe)" "bash -n install-home-assistant.sh"
run_test "install.sh (sintaxe)" "bash -n install.sh"

# Teste 2: Verificar se scripts existem
run_test "install-standalone.sh (existe)" "test -f install-standalone.sh"
run_test "install-home-assistant.sh (existe)" "test -f install-home-assistant.sh"
run_test "install-standalone.ps1 (existe)" "test -f install-standalone.ps1"
run_test "install-home-assistant.ps1 (existe)" "test -f install-home-assistant.ps1"
run_test "install-home-assistant.bat (existe)" "test -f install-home-assistant.bat"
run_test "install.sh (existe)" "test -f install.sh"

# Teste 3: Verificar se core/__init__.py existe
run_test "core/__init__.py (existe)" "test -f core/__init__.py"

# Teste 4: Verificar se repositório é válido
run_test "Repositório válido (.git)" "test -d .git"
run_test "Repositório válido (core/)" "test -d core"

# Teste 5: Conteúdo dos scripts
run_test "install-standalone.sh contém 'PROJECT_ROOT'" "grep -q 'PROJECT_ROOT' install-standalone.sh"
run_test "install-standalone.sh contém 'cd \$PROJECT_ROOT'" "grep -q 'cd \"\$PROJECT_ROOT\"' install-standalone.sh"

run_test "install-home-assistant.sh contém 'PROJECT_ROOT'" "grep -q 'PROJECT_ROOT' install-home-assistant.sh"
run_test "install-home-assistant.sh contém 'cd \$PROJECT_ROOT'" "grep -q 'cd \"\$PROJECT_ROOT\"' install-home-assistant.sh"

run_test "install-home-assistant.bat contém 'PROJECT_ROOT'" "grep -q 'PROJECT_ROOT' install-home-assistant.bat"
run_test "install-home-assistant.bat contém 'cd /d \"%PROJECT_ROOT%\"'" "grep -q 'cd /d \"%PROJECT_ROOT%\"' install-home-assistant.bat"

# Teste 6: Verificar se há detecção de wget
run_test "install-standalone.sh detecta wget (/tmp)" "grep -q '/tmp/\\|/var/tmp/' install-standalone.sh"
run_test "install-home-assistant.sh detecta wget (/tmp)" "grep -q '/tmp/\\|/var/tmp/' install-home-assistant.sh"

# Teste 7: Verificar se há suporte a --pull
run_test "install-standalone.sh suporta --pull" "grep -q '\-\-pull' install-standalone.sh"
run_test "install-home-assistant.sh suporta --pull" "grep -q '\-\-pull' install-home-assistant.sh"

# Teste 8: Verificar arquivos de configuração
run_test "INSTALL.md (existe)" "test -f INSTALL.md"
run_test "docs/SCRIPT_DETECTION.md (existe)" "test -f docs/SCRIPT_DETECTION.md"

echo ""
echo "================================"
echo "RESUMO DOS TESTES"
echo "================================"
echo -e "${GREEN}Passou: $PASSED${NC}"
echo -e "${RED}Falhou: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ TODOS OS TESTES PASSARAM!${NC}"
    exit 0
else
    echo -e "${RED}✗ ALGUNS TESTES FALHARAM${NC}"
    exit 1
fi
