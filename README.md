# Defesa Civil SC → Meshtastic

Integração para ler alertas publicados pela Defesa Civil de Santa Catarina e redistribuir mensagens resumidas para uma malha Meshtastic.

Disponíveis duas versões:
- 🏠 **Home Assistant + AppDaemon** (usa notificações do HA)
- 🔧 **Standalone Python** (sem dependências do HA)

> Este projeto não é oficial da Defesa Civil. Use como integração comunitária e mantenha sempre os canais oficiais de alerta como referência primária.

## ✨ Funcionalidades

- ✅ Lê feed RSS da Defesa Civil SC com polling automático
- ✅ Intervalo de polling: 1/4 do período do feed, com override opcional
- ✅ Armazena histórico dos últimos alertas (limite configurável)
- ✅ Evita reenvio de alertas repetidos (deduplicação por GUID)
- ✅ Compacta mensagens para caber em LoRa (180 caracteres)
- ✅ Envia alertas em 2 mensagens: conteúdo + link
- ✅ Filtro regional opcional por mesorregião e/ou município (somente Standalone)
- ✅ Responde mensagens diretas `ALERTAS` com últimos alertas
- ✅ Reconexão automática com backoff exponencial (Standalone)
- ✅ Modo de teste para validação
- ✅ Suporta ambas as integrações: HA + AppDaemon e Standalone Python


## Fonte de dados

Feed RSS:
```text
https://www.defesacivil.sc.gov.br/categoria/alerta/feed/
```

Campos utilizados:
- `item/title` - Título do alerta
- `item/content:encoded` - Conteúdo completo
- `item/guid` - Identificador único
- `channel/sy:updatePeriod` - Período de atualização
- `channel/sy:updateFrequency` - Frequência de atualização

## 📊 Formato das mensagens

Exemplo:
```text
DC-SC AL: 01/07 11:47 - tempestade severa c/ vento, alag., granizo, raios e enxurr. Mun: Bom Jardim da Serra... Val: 1h. 199/193.
Link: https://www.defesacivil.sc.gov.br/?p=XXXXX
```

Compactações automáticas:
- `ALERTA` → `AL:`, `ATENÇÃO` → `AT:`, `OBSERVAÇÃO` → `OBS:`
- `TEMPESTADE SEVERA` → `tempestade severa`
- `Grande Florianópolis` → `Gde Fpolis`
- `nas próximas 2 horas` → `Val: 2h`
- 46+ compactações de regiões e termos específicos

## 📦 Estrutura do projeto

```text
defesa-civil-sc-meshtastic/
├── 📄 README.md (este arquivo)
├── 📄 LICENSE
├── 📄 SECURITY.md
├── 📄 CONTRIBUTING.md
├── 📄 .gitignore
│
├── 🔧 install.sh                           # Script menu de instalação
├── 🔧 install-home-assistant.sh            # Script HA (Linux/Mac)
├── 🔧 install-home-assistant.ps1           # Script HA (Windows)
├── 🔧 install-standalone.sh                # Script Standalone (Linux/Mac)
├── 🔧 install-standalone.ps1               # Script Standalone (Windows)
│
├── 📚 core/                                # Módulos compartilhados
│   ├── __init__.py                         # Exports
│   ├── constants.py                        # Constantes centralizadas
│   ├── models.py                           # Alert, State dataclasses
│   ├── rss_parser.py                       # Parser RSS
│   ├── message_formatter.py                # Formatação de mensagens
│   └── region_filter.py                    # Filtro regional (mesorregião/município)
│
├── 📦 integrations/
│   ├── home-assistant-appdaemon/
│   │   ├── README.md                       # Instalação HA
│   │   ├── apps/
│   │   │   └── defesa_civil_sc_alertas.py (380 linhas)
│   │   └── config/
│   │       ├── appdaemon.yaml.example
│   │       └── apps.yaml.example
│   │
│   └── standalone-meshtastic/
│       ├── README.md                       # Instalação Standalone
│       ├── main.py                         # Orquestrador
│       ├── requirements.txt                # Dependências
│       ├── config.example.yaml             # Config template
│       ├── state.example.json              # Estado template
│       ├── .gitignore
│       └── src/
│           ├── __init__.py
│           ├── config_manager.py
│           ├── state_manager.py
│           └── meshtastic_connector.py
│
├── 📚 docs/
│   ├── PROJECT_STRUCTURE.md                # Estrutura detalhada
│   └── ARCHITECTURE.md                     # Design e padrões
│
├── 🧪 tests/                               # Suite de testes (74+)
│   ├── __init__.py
│   ├── conftest.py
│   ├── README.md
│   ├── test_constants.py
│   ├── test_models.py
│   ├── test_rss_parser.py
│   ├── test_message_formatter.py
│   ├── test_region_filter.py
│   ├── test_standalone_main.py
│   └── fixtures/
│       └── sample_feed.xml
│
└── 📋 examples/
    └── defesa_civil_sc_alertas_state.example.json
```

## 🏠 Home Assistant + AppDaemon

**Requisitos:**
- Home Assistant funcionando
- Integração Meshtastic instalada
- Add-on AppDaemon instalado
- Canal Meshtastic com entidade notify

**Instalação Rápida:**
```bash
bash install-home-assistant.sh
```

**Vantagens:**
- Integração nativa com Home Assistant
- Usa notificações do HA
- Configurável via UI do HA
- Logs integrados com HA

[👉 Instruções Detalhadas](integrations/home-assistant-appdaemon/README.md)

## 🔧 Standalone Python

**Requisitos:**
- Python 3.8+
- Gateway Meshtastic (USB/Serial ou TCP)
- Conexão com internet

**Instalação Rápida:**
```bash
bash install-standalone.sh
```

**Vantagens:**
- Sem dependência de Home Assistant
- Executa em qualquer servidor com Python
- Modo daemon systemd (Linux)
- Mais leve e simples

[👉 Instruções Detalhadas](integrations/standalone-meshtastic/README.md)

## 📖 Documentação de Instalação

Consulte os READMEs específicos para instruções detalhadas:

| Integração | Link | Descrição |
|------------|------|-----------|
| **Home Assistant + AppDaemon** | [README](integrations/home-assistant-appdaemon/README.md) | Instalação manual passo a passo, configuração do AppDaemon |
| **Standalone Python** | [README](integrations/standalone-meshtastic/README.md) | Instalação com venv, conexão serial/TCP, modo daemon systemd |

## 🏗️ Arquitetura

A partir da v1.0, o projeto usa módulos centralizados em `core/`:

### Módulos Compartilhados (core/)

- **constants.py** - URLs, limites, intervalos, mapeamentos
- **models.py** - Dataclasses `Alert` e `State` para type-safety
- **rss_parser.py** - Parser RSS com intervalo de 1/4 do período do feed e override
- **message_formatter.py** - Compactação para LoRa (46 compactações)

Benefícios:
- 🔄 DRY - Sem duplicação entre integrações
- 🧪 Testável - Suite com 40+ testes
- 🔒 Type-safe - Dataclasses com type hints
- 📚 Bem documentado - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Comparação (antes vs depois)

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Código duplicado | 650 linhas | 0 linhas | ✅ -100% |
| App HA | 658 linhas | 380 linhas | ✅ -42% |
| Testes | 0 | 40+ | ✅ +40 |
| Documentação | Mínima | Completa | ✅ +300% |


## 🤝 Canal de Alertas de SC

![Exemplo de mensagem no canal](docs/images/channelConf.jpeg)

## Mensagens diretas

Se outro node Meshtastic enviar mensagem direta ao gateway com:

```text
ALERTAS
```

O app responde com os últimos alertas armazenados, cada um no mesmo formato de duas mensagens.

![Exemplo de mensagem direta](docs/images/dm_exemple.jpeg)

## Arquivos que não devem ir para o GitHub

Não publique arquivos reais de estado ou configuração local com dados da sua malha:

```text
/config/apps/defesa_civil_sc_alertas_state.json
/config/apps/apps.yaml
/config/appdaemon.yaml
```

O `.gitignore` deste projeto já ignora esses arquivos quando usados dentro do repositório.

## Próximas versões sugeridas

### Filtros futuros

- ✅ Filtrar por município.
- ✅ Filtrar por região da Defesa Civil SC.
- ✅ Enviar somente alertas que mencionem regiões configuradas.
- Filtrar por severidade: `AL:`, `AT:`, `OBS:`.
- Usar CAP/Common Alerting Protocol quando houver fonte pública estruturada.

## 🚀 Instalação Rápida

### ⚡ Opção 1: Wget/Invoke-WebRequest (Mais Rápido - Sem Clone Prévio)

**Linux/Mac:**
```bash
# Home Assistant
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.sh)

# OU Standalone
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
```

**Windows (PowerShell):**
```powershell
# Home Assistant
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1

# OU Standalone
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

### 📋 Opção 2: Clone + Script Local (Recomendado)

**Linux/Mac:**
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install-home-assistant.sh      # Ou install-standalone.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
# Home Assistant
powershell -ExecutionPolicy Bypass -File install-home-assistant.ps1
# OU Standalone
powershell -ExecutionPolicy Bypass -File install-standalone.ps1
```

**Windows (CMD):**
```batch
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
install-home-assistant.bat
```

### 🔄 Atualizar Antes de Instalar (Opcional)

Se você já clonado e quer atualizar para a versão mais recente:

**Linux/Mac:**
```bash
cd defesa-civil-sc-meshtastic
bash install-standalone.sh --pull      # Ou install-home-assistant.sh --pull
```

**Windows (PowerShell):**
```powershell
cd defesa-civil-sc-meshtastic
powershell -ExecutionPolicy Bypass -File install-standalone.ps1 -Pull
```

### ℹ️ Como os Scripts Funcionam

Os scripts são **inteligentes** e detectam automaticamente o contexto:

- ✅ Se executado após `git clone` → Usa versão local (sem duplicação)
- ✅ Se executado via `wget` → Clona repositório automaticamente
- ✅ Argumento `--pull` ou `-Pull` → Atualiza repositório antes de instalar

**Mais detalhes:** Veja [docs/SCRIPT_DETECTION.md](docs/SCRIPT_DETECTION.md) para explicação completa com fluxogramas.


## 🧪 Testes

Suite completa com pytest:

```bash
# Instalar pytest
pip install pytest

# Executar todos os testes
pytest tests/ -v

# Executar com cobertura
pytest tests/ --cov=core

# Executar teste específico
pytest tests/test_rss_parser.py -v
```

Testes incluem:
- ✅ Parser RSS e intervalos dinâmicos
- ✅ Formatação e compactação de mensagens
- ✅ Modelos (serialização/deserialização)
- ✅ Constantes e limites
- ✅ Tratamento de erros

[👉 Documentação de Testes](tests/README.md)

## Aviso operacional

Meshtastic usa rádio LoRa e tem capacidade limitada de payload e airtime. Evite flood:

- mantenha mensagens curtas;
- evite reenviar histórico completo na inicialização;
- use canais privados/comunitários;
- respeite boas práticas de uso da malha local.

## Licença

MIT. Veja `LICENSE`.
