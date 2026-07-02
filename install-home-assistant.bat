@echo off
REM Script de instalação para Defesa Civil SC Meshtastic - Home Assistant AppDaemon
REM Uso: install-home-assistant.bat [--pull]

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Instalação - Defesa Civil SC Meshtastic
echo Integração: Home Assistant + AppDaemon
echo ==========================================
echo.

REM Verificar Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Git não encontrado. Instale git primeiro.
    exit /b 1
)

REM Verificar Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado. Instale Python 3.8+ primeiro.
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% encontrado
echo.

echo [1/5] Detectando repositório...

REM Verificar se está dentro de um repositório válido
if exist ".git" if exist "core\__init__.py" (
    echo [OK] Executando dentro do repositório
    echo [AVISO] Caminho: %cd%
    
    REM Verificar se --pull foi passado
    if "%~1"=="--pull" (
        echo [AVISO] Atualizando repositório com git pull...
        git pull origin main
        echo [OK] Repositório atualizado
    )
    set PROJECT_ROOT=%cd%
) else (
    echo [AVISO] Script local detectado - procurando repositório...
    
    if exist "defesa-civil-sc-meshtastic\core\__init__.py" (
        cd /d "defesa-civil-sc-meshtastic"
        echo [OK] Repositório encontrado
        set PROJECT_ROOT=%cd%
    ) else (
        echo [ERRO] Não conseguiu encontrar o repositório
        echo [AVISO] Use um dos seguintes métodos:
        echo   1. Entre no diretório clonado: cd defesa-civil-sc-meshtastic ^&^& install-home-assistant.bat
        echo   2. Ou clone o repositório: git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
        exit /b 1
    )
)

echo.
echo [OK] Repositório pronto
echo.

REM Garantir que estamos no diretório raiz do projeto
cd /d "%PROJECT_ROOT%"

echo [2/5] Localizando AppDaemon...

echo.
REM Procurar AppDaemon em locais comuns

if "%APPDAEMON_DIR%"=="" (
    echo [AVISO] AppDaemon não encontrado automaticamente
    set /p APPDAEMON_DIR="Digite o caminho do AppDaemon (ex: C:\Users\...\appdaemon): "
)

if not exist "%APPDAEMON_DIR%" (
    echo [ERRO] Diretório AppDaemon inválido: %APPDAEMON_DIR%
    exit /b 1
)

echo [OK] AppDaemon em: %APPDAEMON_DIR%
echo.

echo [3/5] Copiando arquivos...

set APPS_DIR=%APPDAEMON_DIR%\config\apps
if not exist "%APPS_DIR%" mkdir "%APPS_DIR%"

copy "%PROJECT_ROOT%\integrations\home-assistant-appdaemon\apps\defesa_civil_sc_alertas.py" "%APPS_DIR%\" >nul
echo [OK] App copiado para: %APPS_DIR%\defesa_civil_sc_alertas.py

if not exist "%APPDAEMON_DIR%\config\core" (
    xcopy /E /I "%PROJECT_ROOT%\core" "%APPDAEMON_DIR%\config\core\" >nul
    echo [OK] Módulos compartilhados (core/) copiados
) else (
    echo [AVISO] Core já existe, atualizando...
    xcopy /E /I /Y "%PROJECT_ROOT%\core" "%APPDAEMON_DIR%\config\core\" >nul
)

if not exist "%APPS_DIR%\..\apps.yaml" (
    copy "%PROJECT_ROOT%\integrations\home-assistant-appdaemon\config\apps.yaml.example" "%APPS_DIR%\..\apps.yaml" >nul
    echo [AVISO] Arquivo apps.yaml criado (exemplo). EDITE COM SUAS CONFIGURAÇÕES!
) else (
    copy "%PROJECT_ROOT%\integrations\home-assistant-appdaemon\config\apps.yaml.example" "%APPS_DIR%\..\apps.yaml.example" >nul
    echo [AVISO] Arquivo apps.yaml.example disponível como referência
)

echo.
echo ==========================================
echo [OK] Instalação concluída com sucesso!
echo ==========================================
echo.
echo PRÓXIMAS ETAPAS:
echo 1. Edite o arquivo de configuração:
echo    %APPS_DIR%\..\apps.yaml
echo.
echo 2. Substitua:
echo    - notify.mesh_channel_alertas_sc por sua entidade notify real
echo    - 0000000000 por ID numérico do seu gateway Meshtastic
echo.
echo 3. Reinicie o AppDaemon no Home Assistant
echo.
echo LOCALIZAÇÃO DOS ARQUIVOS:
echo   App: %APPS_DIR%\defesa_civil_sc_alertas.py
echo   Config: %APPS_DIR%\..\apps.yaml
echo   Core: %APPDAEMON_DIR%\config\core\
echo.
echo DOCUMENTAÇÃO:
echo   - Instruções detalhadas: integrations\home-assistant-appdaemon\README.md
echo   - Arquitetura: docs\ARCHITECTURE.md
echo.
