# Script de instalação para Defesa Civil SC Meshtastic - Home Assistant AppDaemon
# Uso: powershell -ExecutionPolicy Bypass -File install-home-assistant.ps1 [-Pull]
# Ou: Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [switch]$Pull = $false
)

$ErrorActionPreference = "Stop"

Write-Host "===========================================" -ForegroundColor Green
Write-Host "Instalação - Defesa Civil SC Meshtastic" -ForegroundColor Green
Write-Host "Integração: Home Assistant + AppDaemon" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

# Verificar Git
Write-Host "[1/5] Verificando pré-requisitos..." -ForegroundColor Yellow
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
Write-Host "[2/5] Detectando repositório..." -ForegroundColor Yellow

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
        
        $repoPath = Join-Path $env:TEMP "defesa-civil-sc-meshtastic"
        if (-not (Test-Path $repoPath)) {
            git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git $repoPath
        } else {
            Push-Location $repoPath
            git pull origin main
            Pop-Location
        }
        
        $projectRoot = $repoPath
    } else {
        # Script foi clonado mas não estamos no diretório certo
        Write-Host "Script local detectado - procurando repositório..." -ForegroundColor Yellow
        
        $repoPath = Join-Path (Get-Location) "defesa-civil-sc-meshtastic"
        if ((Test-Path $repoPath) -and (Test-Path "$repoPath\core\__init__.py")) {
            Set-Location $repoPath
            Write-Host "✓ Repositório encontrado" -ForegroundColor Green
            $projectRoot = $repoPath
        } else {
            Write-Host "Não conseguiu encontrar ou clonar o repositório" -ForegroundColor Red
            Write-Host "Use um dos seguintes métodos:" -ForegroundColor Yellow
            Write-Host "  1. Entre no diretório clonado: cd defesa-civil-sc-meshtastic; powershell -ExecutionPolicy Bypass -File install-home-assistant.ps1"
            Write-Host "  2. Ou use Invoke-WebRequest para baixar: Invoke-WebRequest -Uri 'https://raw...install-home-assistant.ps1' -OutFile install.ps1"
            exit 1
        }
    }
}

Write-Host "✓ Repositório pronto" -ForegroundColor Green
Write-Host ""

# Garantir que estamos no diretório raiz do projeto
Set-Location $projectRoot

Write-Host "[3/5] Localizando AppDaemon..." -ForegroundColor Yellow

# Procurar AppDaemon nos locais comuns
$appDaemonDirs = @(
    "$env:USERPROFILE\.homeassistant\appdaemon",
    "C:\AppDaemon",
    "$env:PROGRAMFILES\AppDaemon",
    "C:\Users\*\AppData\Local\*\appdaemon"
)

$appDaemonPath = $null

foreach ($dir in $appDaemonDirs) {
    $expandedDir = Resolve-Path $dir -ErrorAction SilentlyContinue
    if ($expandedDir) {
        Write-Host "✓ AppDaemon encontrado: $expandedDir" -ForegroundColor Green
        $appDaemonPath = $expandedDir
        break
    }
}

if (-not $appDaemonPath) {
    Write-Host "Não foi encontrado AppDaemon automaticamente" -ForegroundColor Yellow
    Write-Host "Digite o caminho do AppDaemon (exemplo: C:\Users\seu_usuario\.homeassistant\appdaemon):" -ForegroundColor Yellow
    $appDaemonPath = Read-Host "Caminho do AppDaemon"
    
    if (-not (Test-Path $appDaemonPath)) {
        Write-Host "Erro: Diretório não existe: $appDaemonPath" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ AppDaemon configurado: $appDaemonPath" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] Copiando arquivos..." -ForegroundColor Yellow

# Copiar app para AppDaemon
$appsDir = Join-Path $appDaemonPath "config\apps"
if (-not (Test-Path $appsDir)) {
    New-Item -ItemType Directory -Path $appsDir -Force | Out-Null
}

$sourceApp = Join-Path $projectRoot "integrations\home-assistant-appdaemon\apps\defesa_civil_sc_alertas.py"
Copy-Item $sourceApp $appsDir -Force
Write-Host "✓ App copiado para: $appsDir\defesa_civil_sc_alertas.py" -ForegroundColor Green

# Copiar core para AppDaemon
$coreDestDir = Join-Path $appDaemonPath "config\core"
$sourceCore = Join-Path $projectRoot "core"

if (-not (Test-Path $coreDestDir)) {
    Copy-Item $sourceCore $coreDestDir -Recurse -Force
    Write-Host "✓ Módulos compartilhados (core/) copiados" -ForegroundColor Green
} else {
    Write-Host "⚠ Core já existe, atualizando..." -ForegroundColor Yellow
    Remove-Item $coreDestDir -Recurse -Force
    Copy-Item $sourceCore $coreDestDir -Recurse -Force
    Write-Host "✓ Core atualizado" -ForegroundColor Green
}

# Copiar apps.yaml
$appsYamlDest = Join-Path $appDaemonPath "config\apps.yaml"
if (-not (Test-Path $appsYamlDest)) {
    $appsYamlSource = Join-Path $projectRoot "integrations\home-assistant-appdaemon\config\apps.yaml.example"
    Copy-Item $appsYamlSource $appsYamlDest -Force
    Write-Host "✓ Arquivo apps.yaml criado (EDITE COM SUAS CONFIGURAÇÕES!)" -ForegroundColor Yellow
} else {
    Write-Host "✓ apps.yaml já existe (não foi sobrescrito)" -ForegroundColor Green
}

Write-Host ""

Write-Host "[5/5] Finalizando instalação..." -ForegroundColor Yellow

Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "✓ Instalação concluída com sucesso!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

Write-Host "PRÓXIMAS ETAPAS:" -ForegroundColor Yellow
Write-Host "1. Edite o arquivo de configuração:"
Write-Host "   $appsYamlDest"
Write-Host ""
Write-Host "2. Configure os parâmetros necessários:"
Write-Host "   - notify_entity: entidade de notificação (ex: notify.mesh_channel_1)"
Write-Host "   - gateway_node_id: ID do gateway Meshtastic"
Write-Host "   - test_mode: true/false"
Write-Host ""
Write-Host "3. Reinicie o AppDaemon"
Write-Host ""
Write-Host "4. Verifique os logs:"
Write-Host "   Home Assistant > Settings > Add-ons > AppDaemon > Logs"
Write-Host ""

Write-Host "LOCALIZAÇÃO DOS ARQUIVOS:" -ForegroundColor Yellow
Write-Host "  App: $appsDir\defesa_civil_sc_alertas.py"
Write-Host "  Config: $appsYamlDest"
Write-Host "  Core: $coreDestDir"
Write-Host ""

Write-Host "DOCUMENTAÇÃO:" -ForegroundColor Yellow
Write-Host "  - Instruções detalhadas: README.md"
Write-Host "  - Configuração: integrations/home-assistant-appdaemon/README.md"
Write-Host "  - Arquitetura: docs/ARCHITECTURE.md"
Write-Host ""
