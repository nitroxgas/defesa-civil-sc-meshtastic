# Versão Standalone Meshtastic

Integração sem dependência do Home Assistant que lê alertas RSS da Defesa Civil SC e redistribui para uma malha Meshtastic via conexão serial ou TCP.

## ℹ️ Refatoração - Uso de Módulos Compartilhados

A partir da v1.0, esta integração usa módulos centralizados em `core/` para evitar duplicação de código:

- `core.RSSParser` - Parser RSS
- `core.MessageFormatter` - Compactação de mensagens
- `core.State`, `core.Alert` - Modelos de dados
- `core.constants` - Constantes centralizadas

Veja [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) para detalhes de arquitetura.

## 📋 Pré-requisitos

- ✅ Python 3.8+
- ✅ Gateway Meshtastic (USB/Serial ou TCP)
- ✅ Conexão com internet (para feed RSS)
- ✅ Git instalado

## Arquitetura

```text
RSS Defesa Civil SC
        ↓
   RSSParser (de core/)
        ↓
   MessageFormatter (de core/ - compactação)
        ↓
   StateManager (deduplicação + histórico JSON)
        ↓
   MeshtasticConnector (serial/TCP)
        ↓
   Canal Meshtastic "Alertas-SC"
```

## 🚀 Instalação Rápida (Recomendado)

### ⚡ Opção 1: Wget Direto (Sem Clone Prévio)

**Linux/Mac:**
```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
```

O script irá:
- Clonar repositório automaticamente
- Criar ambiente virtual Python
- Instalar dependências
- Copiar configuração de exemplo
- Verificar integração com `core/`

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

### 📋 Opção 2: Clone Local + Script

**Linux/Mac:**
```bash
# 1. Clonar repositório
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic

# 2. Executar script de instalação
bash install-standalone.sh

# 3. (Opcional) Atualizar antes de instalar
bash install-standalone.sh --pull
```

**Windows (PowerShell):**
```powershell
# 1. Clonar repositório
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic

# 2. Executar script de instalação
powershell -ExecutionPolicy Bypass -File install-standalone.ps1

# 3. (Opcional) Atualizar antes de instalar
powershell -ExecutionPolicy Bypass -File install-standalone.ps1 -Pull
```

**Windows (CMD):**
```batch
# 1. Clonar repositório
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic

# 2. Executar script
install-standalone.bat

# 3. (Opcional) Atualizar antes de instalar
install-standalone.bat --pull
```

## 📋 Instalação Manual

### Passo 1: Clonar Repositório

```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic/integrations/standalone-meshtastic
```

### Passo 2: Criar Ambiente Virtual

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (CMD):**
```batch
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### Passo 3: Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Passo 4: Importar Módulos Core

A integração precisa acessar os módulos compartilhados em `core/`.

**Opção A: Symlink (recomendado para desenvolvimento)**

```bash
# Linux/Mac
ln -s ../../core ./core

# Windows (PowerShell como admin)
New-Item -ItemType SymbolicLink -Path ".\core" -Target "..\..\core"
```

**Opção B: Copiar diretório**

```bash
# Linux/Mac
cp -r ../../core ./core

# Windows
xcopy ..\..\core core /E /I
```

**Verificar se está correto:**

```bash
python -c "from core import RSSParser, MessageFormatter; print('✓ Core importado com sucesso')"
```

### Passo 5: Configurar Aplicação

Copie e edite o arquivo de configuração:

```bash
cp config.example.yaml config.yaml
```

**Edite `config.yaml`:**

```yaml
meshtastic:
  connection_type: serial  # 'serial' ou 'tcp'
  serial_port: ""          # vazio para auto-detect, ou ex: "/dev/ttyUSB0"
  # Para TCP (gateway T-Deck, etc):
  # tcp_host: "192.168.1.100"
  # tcp_port: 4403

channel:
  name: "Alertas-SC"       # nome do canal
  number: 0                # índice do canal

feed:
  url: "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"
  timeout_seconds: 30
  # Intervalo fixo em minutos. Se 0 ou omitido, usa 1/4 do período do feed
  # (hourly -> 15 min, daily -> 360 min). Limite mínimo: 15 min.
  interval_minutes: 0

state:
  file: "./state.json"     # onde guardar histórico

direct_message:
  enabled: true
  trigger_word: "ALERTAS"

test_mode: false           # mude para true para testar

logging:
  level: DEBUG             # DEBUG, INFO, WARNING, ERROR
  file: null               # null = console only
```

### Passo 6: Testar Conexão

**Testar conexão serial (auto-detect):**

```bash
python -c "import meshtastic; dev = meshtastic.serial_port.SerialInterface(); print('✓ Conexão OK'); dev.close()"
```

**Testar conexão TCP:**

```bash
python -c "import meshtastic; dev = meshtastic.mesh_pb2.TCPInterface(hostname='192.168.1.100'); print('✓ Conexão OK'); dev.close()"
```

## ▶️ Execução

### Modo Normal

```bash
# Ativar venv se não estiver ativo
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate.bat  # Windows CMD
# ou
venv\Scripts\Activate.ps1  # Windows PowerShell

# Executar
python main.py config.yaml
```

Você deve ver:
```
INFO: Defesa Civil SC Alertas iniciado
INFO: Conectando ao Meshtastic...
INFO: Feed verificado. Itens: 5. Novos: 0.
```

### Modo de Teste

Para enviar um alerta sem esperar por novos:

**Edite `config.yaml`:**
```yaml
test_mode: true
```

**Execute:**
```bash
python main.py config.yaml
```

Você deve receber um alerta no canal. Depois, mude para `test_mode: false`.

### Executar em Background

**Linux/Mac (nohup):**
```bash
nohup python main.py config.yaml > alertas.log 2>&1 &
```

**Linux/Mac (screen):**
```bash
screen -S alertas-sc -d -m python main.py config.yaml
# Ver: screen -ls
# Conectar: screen -r alertas-sc
# Sair: Ctrl+A, D
```

**Linux (systemd - serviço permanente):**

Criar `/etc/systemd/system/defesa-civil-sc-alertas.service`:

```ini
[Unit]
Description=Defesa Civil SC Meshtastic Alerts
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/defesa-civil-sc-meshtastic/integrations/standalone-meshtastic
ExecStart=/home/your_user/defesa-civil-sc-meshtastic/integrations/standalone-meshtastic/venv/bin/python main.py config.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable defesa-civil-sc-alertas
sudo systemctl start defesa-civil-sc-alertas
sudo systemctl status defesa-civil-sc-alertas

# Ver logs
sudo journalctl -u defesa-civil-sc-alertas -f
```

## 🎛️ Configuração Detalhada

### Conexão Serial

**Auto-detect (recomendado):**
```yaml
meshtastic:
  connection_type: serial
  serial_port: ""  # Python encontrará automaticamente
```

**Linux (específico):**
```bash
# Listar portas
ls /dev/tty* | grep USB
# Resultado: /dev/ttyUSB0

# Configurar em config.yaml
meshtastic:
  connection_type: serial
  serial_port: "/dev/ttyUSB0"
```

**Windows (específico):**
```
Gerenciador de Dispositivos → Portas → COM3 (exemplo)

config.yaml:
meshtastic:
  connection_type: serial
  serial_port: "COM3"
```

### Conexão TCP

Para gateways que suportam TCP (ex: T-Deck Meshtastic):

```yaml
meshtastic:
  connection_type: tcp
  tcp_host: "192.168.1.100"  # IP do gateway
  tcp_port: 4403
```

Como encontrar o IP do gateway:
- Abra interface Meshtastic Web (`meshtastic.org/client/`)
- Procure por "IP Address" nas configurações
- Use `ping 192.168.1.100` para testar

## 🧪 Funcionalidades

### 1️⃣ Polling Automático
- Lê feed RSS a cada 1/4 do período informado pelo feed (ex: hourly -> 15 min)
- Pode ser sobrescrito por `feed.interval_minutes`
- Respeita limite mínimo de 15 min
- Compacta mensagens para caber em LoRa (180 chars)

### 2️⃣ Compactação (via `core.MessageFormatter`)
- Prefixos: `ALERTA` → `AL:`, `ATENÇÃO` → `AT:`, `OBSERVAÇÃO` → `OBS:`
- Termos: `TEMPESTADE SEVERA` → `tempestade severa`, `RAJADAS DE VENTO` → `vento`
- Regiões: `Grande Florianópolis` → `Gde Fpolis`
- Validades: `nas próximas 2 horas` → `Val: 2h`

### 3️⃣ Mensagens em Canal
Cada alerta é enviado em 2 mensagens:
1. Conteúdo compactado (max 180 chars): `DC-SC AL: ...`
2. Link (max 180 chars): `Link: https://...`

Aguarda 10 segundos entre mensagens para respeitar LoRa.

### 4️⃣ Resposta a Mensagens Diretas
Se outro node enviar `ALERTAS`, responde com os 2 últimos alertas.

### 5️⃣ Histórico Persistente
- Armazena últimos 10 alertas em `state.json`
- Consultas offline funcionam
- Deduplicação via GUID (evita reenvio)

## 📁 Estrutura de Arquivos

```text
integrations/standalone-meshtastic/
├── main.py                      # Orquestrador principal
├── requirements.txt             # Dependências Python
├── config.example.yaml          # Exemplo de config
├── config.yaml                  # Config (criar a partir do .example)
├── state.json                   # Histórico (auto-criado)
├── alertas.log                  # Logs (opcional)
├── venv/                        # Ambiente virtual
└── src/
    ├── __init__.py
    ├── config_manager.py        # Gerenciar config YAML
    ├── state_manager.py         # Persistir estado JSON
    ├── meshtastic_connector.py  # Integração Meshtastic
    └── (rss_parser.py e message_formatter.py → importadas de core/)
```

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: core` | Verifique symlink/cópia de core/, rode: `python -c "from core import RSSParser"` |
| `SerialException: port not found` | Conecte gateway USB, verifique com `ls /dev/tty*` (Linux) ou Gerenciador de Dispositivos (Windows) |
| `ConnectionRefusedError (TCP)` | Verifique IP e porta do gateway, teste: `ping 192.168.1.100` |
| `Feed RSS não carrega` | Verifique internet, teste URL em navegador, aumente log para DEBUG |
| Mensagens não chegam | Verifique se canal existe, teste modo de teste (`test_mode: true`), procure por erros nos logs |
| `Permission denied /dev/ttyUSB0` | Linux: `sudo usermod -a -G dialout $USER` (saia e entre novamente) |

## 📊 Logs

**Console (padrão):**
```
INFO: Defesa Civil SC Alertas iniciado
DEBUG: Conectando a serial_port=
INFO: Conectado ao Meshtastic
INFO: Feed verificado. Itens: 5. Novos: 2. Próxima: 15 min
```

**Arquivo (se configurado):**
```yaml
logging:
  file: "./alertas.log"
```

Ver logs em tempo real:
```bash
tail -f alertas.log
# ou
tail -f alertas.log | grep ERROR
```

## 🔄 Atualizando

```bash
cd defesa-civil-sc-meshtastic
git pull origin main
cp integrations/standalone-meshtastic/config.example.yaml integrations/standalone-meshtastic/
# Se usou symlink, core/ será atualizado automaticamente
```

## ⚠️ Cuidados

- **LoRa airtime**: Cada mensagem consome recursos. App aguarda 10s entre mensagens.
- **Flood inicial**: Primeira execução carrega histórico sem enviar (evita flood).
- **Chaves de canal**: Não publique `config.yaml` com chaves de canal públicas.
- **Taxa de feed**: Se feed publica muito (< 15 min), o intervalo mínimo de 15 min é respeitado.
- **Histórico**: `state.json` pode crescer. Limite de 10 alertas é controlado.

## 📚 Documentação

- [Arquitetura e Design](../../docs/ARCHITECTURE.md)
- [README Principal](../../README.md)
- [Meshtastic Docs](https://meshtastic.org/docs/)
- [Python meshtastic](https://github.com/meshtastic/python)

## Licença

MIT. Veja `LICENSE`.
