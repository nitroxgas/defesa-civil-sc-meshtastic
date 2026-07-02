# Script de instalação para Defesa Civil SC Meshtastic - Standalone
# Uso: powershell -ExecutionPolicy Bypass -File install-standalone.ps1 [-Pull]
# Ou: Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [string]$InstallPath = ".",
    [switch]$Pull = $false
)

$ErrorActionPreference = "Stop"

Write-Host "===========================================" -ForegroundColor Green
Write-Host "Instalação - Defesa Civil SC Meshtastic" -ForegroundColor Green
Write-Host "Integração: Standalone Meshtastic" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

# Verificar Git
Write-Host "[1/7] Verificando pré-requisitos..." -ForegroundColor Yellow
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git não encontrado. Instale git primeiro." -ForegroundColor Red
    exit 1
}

# Verificar Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python não encontrado. Instale Python 3.8+ primeiro." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "✓ $pythonVersion encontrado" -ForegroundColor Green
Write-Host ""

# Detectar repositório
Write-Host "[2/7] Detectando repositório..." -ForegroundColor Yellow

$scriptPath = $PSScriptRoot
$isTempScript = $false

# Verificar se script está em diretório temporário
if ($scriptPath -like "*\AppData\Local\Temp*" -or $scriptPath -like "*\Temp*") {
    $isTempScript = $true
}

# Verificar se está dentro de um repositório válido
$gitDir = Test-Path ".git"
$coreDir = Test-Path "core\__init__.py"

if ($gitDir -and $coreDir) {
    Write-Host "✓ Executando dentro do repositório" -ForegroundColor Green
    Write-Host "  Caminho: $(Get-Location)" -ForegroundColor Yellow
    
    # Se argumento -Pull foi passado, fazer git pull
    if ($Pull) {
        Write-Host "  Atualizando repositório com git pull..." -ForegroundColor Yellow
        git pull origin main
        Write-Host "  ✓ Repositório atualizado" -ForegroundColor Green
    }
    
    $projectRoot = (Get-Location).Path
} else {
    # Não está em um repositório, fazer clone
    if ($isTempScript) {
        Write-Host "Executando via web - clonando repositório..." -ForegroundColor Yellow
        
        if (-not (Test-Path $InstallPath)) {
            New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        }
        
        Push-Location $InstallPath
        
        $repoPath = Join-Path $InstallPath "defesa-civil-sc-meshtastic"
        if (-not (Test-Path $repoPath)) {
            git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
            $projectRoot = $repoPath
        } else {
            Set-Location $repoPath
            git pull origin main
            $projectRoot = $repoPath
        }
        Pop-Location
        Set-Location $projectRoot
    } else {
        # Script foi clonado mas não estamos no diretório certo
        Write-Host "Script local detectado - procurando repositório..." -ForegroundColor Yellow

        $repoPath = $null
        if ($InstallPath -ne ".") {
            $repoPath = Join-Path $InstallPath "defesa-civil-sc-meshtastic"
            if (-not (Test-Path $InstallPath)) {
                New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
            }
            if (-not (Test-Path $repoPath)) {
                Push-Location $InstallPath
                git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
                Pop-Location
            }
        }

        if (-not $repoPath) {
            $repoPath = Join-Path (Get-Location) "defesa-civil-sc-meshtastic"
        }

        if ((Test-Path $repoPath) -and (Test-Path "$repoPath\core\__init__.py")) {
            Set-Location $repoPath
            Write-Host "✓ Repositório encontrado" -ForegroundColor Green
            $projectRoot = $repoPath
        } else {
            Write-Host "Não conseguiu encontrar ou clonar o repositório" -ForegroundColor Red
            Write-Host "Use um dos seguintes métodos:" -ForegroundColor Yellow
            Write-Host "  1. Entre no diretório clonado: cd defesa-civil-sc-meshtastic; powershell -ExecutionPolicy Bypass -File install-standalone.ps1"
            Write-Host "  2. Especifique caminho: powershell -ExecutionPolicy Bypass -File install-standalone.ps1 -InstallPath C:\caminho"
            Write-Host "  3. Ou use Invoke-WebRequest para baixar: Invoke-WebRequest -Uri 'https://raw...install-standalone.ps1' -OutFile install.ps1"
            exit 1
        }
    }
}

Write-Host "✓ Repositório pronto" -ForegroundColor Green
Write-Host ""

# Garantir que estamos no diretório raiz do projeto
Set-Location $projectRoot

# Criar ambiente virtual
Write-Host "[3/7] Criando ambiente virtual Python..." -ForegroundColor Yellow
$standaloneDir = Join-Path $projectRoot "integrations\standalone-meshtastic"
$venvPath = Join-Path $standaloneDir "venv"

if (-not (Test-Path $venvPath)) {
    Push-Location $standaloneDir
    python -m venv venv
    Write-Host "✓ Ambiente virtual criado" -ForegroundColor Green
} else {
    Write-Host "Ambiente virtual já existe" -ForegroundColor Yellow
    Push-Location $standaloneDir
}

# Ativar venv
& "$venvPath\Scripts\Activate.ps1"

Write-Host ""
Write-Host "[4/7] Instalando dependências..." -ForegroundColor Yellow
pip install --upgrade pip setuptools wheel | Out-Null
pip install -r requirements.txt
Write-Host "✓ Dependências instaladas" -ForegroundColor Green

Write-Host ""
Write-Host "[5/7] Preparando configuração..." -ForegroundColor Yellow

$configFile = Join-Path (Get-Location) "config.yaml"
$configExample = Join-Path (Get-Location) "config.example.yaml"

if (-not (Test-Path $configFile)) {
    Copy-Item $configExample $configFile
    Write-Host "✓ Arquivo config.yaml criado" -ForegroundColor Green
    Write-Host "⚠ EDITE config.yaml COM SUAS CONFIGURAÇÕES!" -ForegroundColor Yellow
} else {
    Copy-Item $configExample "$configFile.example"
    Write-Host "config.yaml.example disponível como referência" -ForegroundColor Yellow
}

$stateFile = Join-Path (Get-Location) "state.json"
$stateExample = Join-Path (Get-Location) "state.example.json"

if (-not (Test-Path $stateFile)) {
    Copy-Item $stateExample $stateFile
    Write-Host "✓ Arquivo state.json criado" -ForegroundColor Green
}

Write-Host ""
Write-Host "[6/7] Verificando integração com core/..." -ForegroundColor Yellow

# Teste de importação
try {
    python -c "import sys; sys.path.insert(0, '../..'); from core import RSSParser, MessageFormatter; print('✓ Core importado com sucesso')" | Write-Host -ForegroundColor Green
} catch {
    Write-Host "⚠ Aviso ao importar core (pode estar ok)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[7/7] Teste completo de importação..." -ForegroundColor Yellow

$importTest = @"
import sys
sys.path.insert(0, '../..')
from core import RSSParser, MessageFormatter, State, Alert
print('✓ Todas as importações de core/ funcionam')
print('  - RSSParser')
print('  - MessageFormatter')
print('  - State')
print('  - Alert')
"@

python -c $importTest

Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "✓ Instalação concluída com sucesso!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

Write-Host "📝 CONFIGURAÇÃO NECESSÁRIA:" -ForegroundColor Yellow
Write-Host "1. Edite o arquivo de configuração:"
Write-Host "   $configFile"
Write-Host ""
Write-Host "2. Configure os campos obrigatórios:"
Write-Host "   - connection_type: 'serial' ou 'tcp'"
Write-Host "   - serial_port: 'COM3' (para serial no Windows)"
Write-Host "   - tcp_host: 'localhost:4403' (para TCP)"
Write-Host "   - channel.name: nome do canal (ex: 'Alertas-SC')"
Write-Host "   - channel.number: número do canal (ex: 0)"
Write-Host ""

Write-Host "🚀 EXECUTANDO A APLICAÇÃO:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opção 1 - Execução direta:"
Write-Host "  venv\Scripts\Activate.ps1"
Write-Host "  python main.py config.yaml"
Write-Host ""
Write-Host "Opção 2 - Com path completo:"
Write-Host "  & '$(Get-Location)\venv\Scripts\Activate.ps1'"
Write-Host "  & '$(Get-Location)\venv\Scripts\python.exe' '$(Get-Location)\main.py' '$configFile'"
Write-Host ""

Write-Host "🧪 MODO DE TESTE:" -ForegroundColor Yellow
Write-Host "  1. Edite config.yaml e defina: test_mode: true"
Write-Host "  2. Execute normalmente: python main.py config.yaml"
Write-Host "  3. A aplicação simula conexão"
Write-Host ""

Write-Host "📂 LOCALIZAÇÃO DOS ARQUIVOS:" -ForegroundColor Yellow
Write-Host "  Instalação: $(Get-Location)"
Write-Host "  App: $(Get-Location)\main.py"
Write-Host "  Config: $configFile"
Write-Host "  Estado: $stateFile"
Write-Host "  Core (compartilhado): ..\..\core\"
Write-Host "  Requirements: $(Get-Location)\requirements.txt"
Write-Host ""

Write-Host "🔧 AMBIENTE VIRTUAL:" -ForegroundColor Yellow
Write-Host "  Ativar: venv\Scripts\Activate.ps1"
Write-Host "  Desativar: deactivate"
Write-Host "  Python executável: $(Get-Location)\venv\Scripts\python.exe"
Write-Host ""

Write-Host "📚 DOCUMENTAÇÃO:" -ForegroundColor Yellow
Write-Host "  - README detalhado: integrations\standalone-meshtastic\README.md"
Write-Host "  - Arquitetura do projeto: docs\ARCHITECTURE.md"
Write-Host "  - Exemplo config: $(Get-Location)\config.example.yaml"
Write-Host ""

Write-Host "⚠️  TROUBLESHOOTING:" -ForegroundColor Yellow
Write-Host "  Erro 'ModuleNotFoundError: No module named core'?"
Write-Host "  Execute: & '$projectRoot\test_imports.py'"
Write-Host ""
Write-Host "  Erro de conexão Meshtastic?"
Write-Host "  1. Verifique Device Manager para porta COM"
Write-Host "  2. Confirme serial_port em config.yaml"
Write-Host "  3. Teste conexão com meshtastic CLI"
Write-Host ""

Write-Host "✓ Instalação pronta! Execute agora para começar." -ForegroundColor Green
Write-Host ""

Pop-Location
