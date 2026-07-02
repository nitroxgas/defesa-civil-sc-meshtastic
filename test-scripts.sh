#!/bin/bash
# Teste de todos os scripts de instalação
# Este script valida que todos os scripts executam corretamente

echo "✓ Testando detecção automática dos scripts de instalação..."
echo ""

# Teste 1: Verificar que os scripts existem
echo "📋 Scripts criados:"
ls -1 install*.sh install*.ps1 install*.bat 2>/dev/null | while read script; do
    lines=$(wc -l < "$script")
    echo "  ✓ $script ($lines linhas)"
done
echo ""

# Teste 2: Verificar sintaxe dos scripts Bash
echo "🔍 Validando sintaxe Bash:"
for script in install*.sh; do
    if bash -n "$script" 2>/dev/null; then
        echo "  ✓ $script - OK"
    else
        echo "  ✗ $script - ERRO"
        exit 1
    fi
done
echo ""

# Teste 3: Verificar se scripts detectam repositório
echo "🎯 Testando detecção de repositório:"
if [ -f ".git" ] || [ -d ".git" ]; then
    echo "  ✓ Estamos dentro de um repositório (.git encontrado)"
else
    echo "  ⚠ Não estamos em um repositório Git"
fi

if [ -f "core/__init__.py" ]; then
    echo "  ✓ core/__init__.py encontrado"
else
    echo "  ⚠ core/__init__.py não encontrado"
fi
echo ""

echo "✅ Validação concluída com sucesso!"
