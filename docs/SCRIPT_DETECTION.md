# 🔍 Como Funciona a Detecção Automática dos Scripts

## Cenário 1: Usuário Clona + Executa Localmente ✅

```
1. Usuario: git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
2. Usuario: cd defesa-civil-sc-meshtastic
3. Usuario: bash install-standalone.sh

Script detecta:
  ✓ Está dentro de um repositório (.git existe)
  ✓ Está no diretório correto (core/__init__.py existe)
  ✓ Usa versão local do repositório
  ✓ Pula o clone
```

**Resultado:** ✅ Instalação rápida, sem duplicação

---

## Cenário 2: Usuário Executa via Wget (Sem Clone Prévio) ✅

```
1. Usuario: bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)

Script detecta:
  ✓ Script está em /tmp (diretório temporário)
  ✓ Não está em um repositório
  ✓ Faz clone automaticamente
  ✓ Executa instalação no diretório clonado
```

**Resultado:** ✅ One-liner rápido, clonagem automática

---

## Cenário 3: Usuário Tenta Clonar Novamente (ERRO EVITADO) ❌ → ✅

```
ANTES (comportamento antigo):
1. Usuario: git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
2. Usuario: cd defesa-civil-sc-meshtastic
3. Usuario: bash install-standalone.sh
   ⚠ Script fazia: git clone novamente
   ⚠ Resultado: defesa-civil-sc-meshtastic/defesa-civil-sc-meshtastic/

DEPOIS (comportamento corrigido):
1. Usuario: git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
2. Usuario: cd defesa-civil-sc-meshtastic
3. Usuario: bash install-standalone.sh
   ✓ Script detecta já estar no repositório
   ✓ Usa versão local
   ✓ Sem duplicação!
```

**Resultado:** ✅ Evita duplicação de diretórios

---

## Cenário 4: Usuário Quer Atualizar Antes (--pull) ✅

```
1. Usuario: cd defesa-civil-sc-meshtastic
2. Usuario: bash install-standalone.sh --pull

Script executa:
  ✓ Detecta repositório
  ✓ Reconhece argumento --pull
  ✓ Executa: git pull origin main
  ✓ Instala com versão atualizada
```

**Resultado:** ✅ Instalação com atualização garantida

---

## Fluxograma de Detecção

```
INICIO DO SCRIPT
   |
   v
Scripts pode estar em 2 lugares:
  1. /tmp/... ou /var/tmp/... (wget)
  2. Local (git clone)
   |
   +---> SE está em /tmp ou /var/tmp:
   |        (Executado via wget)
   |        v
   |     Precisa clonar?
   |     |
   |     +---> Clona em $INSTALL_DIR
   |
   +---> SE não está em /tmp:
        (Executado localmente)
        v
        Verifica se está em repositório:
        - .git existe?
        - core/__init__.py existe?
        |
        +---> SIM: Usa versão local
        |        - Se --pull: git pull
        |
        +---> NÃO: Procura defesa-civil-sc-meshtastic/
                 - Se encontra: cd e usa local
                 - Se não encontra: ERRO (instrua usuário)
```

---

## Arquivos-Chave para Detecção

### Bash (install-*.sh)

```bash
# Verificar se é script temporário (wget)
if [[ "$SCRIPT_DIR" == /tmp/* ]] || [[ "$SCRIPT_DIR" == /var/tmp/* ]]; then
    IS_TEMP_SCRIPT=1
fi

# Verificar se está em repositório válido
if [ -d ".git" ] && [ -f "core/__init__.py" ]; then
    PROJECT_ROOT="$(pwd)"
    # Usa versão local
fi

# Se argumento --pull foi passado
if [[ "$*" == *"--pull"* ]]; then
    git pull origin main
fi
```

### PowerShell (install-*.ps1)

```powershell
# Verificar se script é temporário
$isTempScript = ($scriptPath -like "*\AppData\Local\Temp*")

# Verificar se está em repositório
$gitDir = Test-Path ".git"
$coreDir = Test-Path "core\__init__.py"

if ($gitDir -and $coreDir) {
    $projectRoot = (Get-Location).Path
    # Usa versão local
}

# Se switch -Pull foi passado
if ($Pull) {
    git pull origin main
}
```

### Batch (install-*.bat)

```batch
REM Verificar se está em repositório
if exist ".git" if exist "core\__init__.py" (
    REM Usa versão local
    set PROJECT_ROOT=%cd%
)

REM Se --pull foi passado
if "%~1"=="--pull" (
    git pull origin main
)
```

---

## Testes Recomendados

Para validar que a detecção funciona corretamente:

```bash
# Teste 1: Clonar e executar
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git test1
cd test1
bash install-standalone.sh --pull   # Deve detectar e usar local
cd ..

# Teste 2: Executar via wget
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
# Deve fazer clone automaticamente

# Teste 3: Validar sintaxe
bash -n install-standalone.sh
bash -n install-home-assistant.sh
bash -n install.sh
# Todos devem retornar 0 (sem erros)
```

---

## Benefícios da Detecção Automática

| Cenário | Antes | Depois |
|---------|-------|--------|
| Clone + Executa | ⚠ Duplica diretório | ✅ Usa local |
| Clone + Pull + Executa | ❌ Falha | ✅ Atualiza |
| Wget direto | ❌ Erro | ✅ Clone automático |
| Verificação | Manual | ✅ Automática |

---

## Próximos Passos

1. **Usuários podem instalar de forma simples:**
   - Opção 1: `bash install-standalone.sh` (se já clonado)
   - Opção 2: `bash <(wget -qO- ...)` (sem clone prévio)

2. **Scripts garantem:**
   - Sem duplicação
   - Versão correta
   - Atualização opcional com `--pull`

3. **Documentação clara em INSTALL.md** com todos os cenários
