@echo off
REM Script de instalação para Defesa Civil SC Meshtastic - Home Assistant AppDaemon
REM Uso: install-home-assistant.bat [--pull]

setlocal enabledelayedexpansion

REM Parse de argumentos
set PULL=false
for %%a in (%*) do (
    if "%%a"=="--pull" set PULL=true
    if "%%a"=="--help" goto :show_help
    if "%%a"=="-h" goto :show_help
)

goto :start

:show_help
echo Uso: install-home-assistant.bat [--pull]
echo   --pull    Atualiza o repositório com git pull antes de instalar
exit /b 0

:start
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
    if "!PULL!"=="true" (
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
    for %%d in (
        "%USERPROFILE%\.homeassistant\appdaemon"
        "%USERPROFILE%\AppData\Local\AppDaemon\appdaemon"
        "%USERPROFILE%\AppData\Roaming\AppDaemon\appdaemon"
        "%PROGRAMDATA%\AppDaemon\appdaemon"
        "%PROGRAMFILES%\AppDaemon"
        "C:\AppDaemon"
    ) do (
        if exist "%%~d" (
            set APPDAEMON_DIR=%%~d
            goto :found_appdaemon
        )
    )
)

:found_appdaemon
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
echo CONFIGURACAO NECESSARIA:
echo 1. Edite o arquivo de configuração:
echo    %APPS_DIR%\..\apps.yaml
echo.
echo 2. Configure os campos obrigatórios:
echo    - notify_entity: entidade notify (ex: notify.mesh_channel_alertas_sc)
echo    - gateway_node_id: ID numérico do seu Meshtastic
echo    - channel: número do canal para enviar alertas
echo.
echo ATIVANDO A INTEGRACAO:
echo 1. Edite o arquivo de configuração conforme acima
echo 2. Vá para Home Assistant Settings Add-ons AppDaemon
echo 3. Clique em Reiniciar para recarregar a configuração
echo.
echo VERIFICANDO A INSTALACAO:
echo 1. Acesse Home Assistant Settings Add-ons AppDaemon Logs
echo 2. Procure por 'DefesaCivilSCAlertas' ou 'defesa_civil_sc_alertas'
echo 3. Se não houver erros, a integração está funcionando
echo.
echo LOCALIZACAO DOS ARQUIVOS:
echo   App: %APPS_DIR%\defesa_civil_sc_alertas.py
echo   Config: %APPS_DIR%\..\apps.yaml
echo   Core: %APPDAEMON_DIR%\config\core\
echo   AppDaemon config: %APPDAEMON_DIR%\config\
echo.
echo MODO DE TESTE:
echo   Para testar sem conectar ao Meshtastic:
echo   1. Edite apps.yaml e defina: test_mode: true
echo   2. Restart AppDaemon
echo.
echo COMANDOS UTEIS:
echo   Ver logs em tempo real:
echo     Home Assistant Settings Add-ons AppDaemon Logs
echo.
echo   Listar entidades notify:
echo     Home Assistant Developer Tools States
echo     Procurar por 'notify'
echo.
echo DOCUMENTACAO:
echo   - README detalhado: integrations\home-assistant-appdaemon\README.md
echo   - Arquitetura do projeto: docs\ARCHITECTURE.md
echo.
echo TROUBLESHOOTING:
echo   App não aparece em Home Assistant?
echo   - Verifique logs do AppDaemon
echo   - Confirme nome correto em apps.yaml
echo   - Verifique indentação YAML (use espaços, não tabs)
echo.
echo Erro de entidade notify?
echo   - Verifique se entidade realmente existe
echo   - Teste envio manual em Services
echo.
echo OK - Instalação concluída! Agora configure e reinicie AppDaemon.
echo.
