# Estrutura do projeto

```text
defesa-civil-sc-meshtastic/
├── README.md                         # Documentação principal
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── .gitignore
├── install.sh                        # Menu de instalação
├── install-home-assistant.sh         # Script HA (Linux/Mac)
├── install-home-assistant.ps1        # Script HA (Windows)
├── install-standalone.sh             # Script Standalone (Linux/Mac)
├── install-standalone.ps1            # Script Standalone (Windows)
├── core/                             # Módulos compartilhados entre integrações
│   ├── __init__.py
│   ├── constants.py                  # URLs, limites e constantes
│   ├── models.py                   # Dataclasses Alert e State
│   ├── rss_parser.py               # Parser RSS e cálculo de intervalo
│   ├── message_formatter.py        # Compactação de mensagens para LoRa
│   ├── region_filter.py            # Filtro por mesorregião/município
│   └── sc_mesorregioes_microrregioes_municipios.json
├── integrations/
│   ├── home-assistant-appdaemon/
│   │   ├── README.md
│   │   ├── apps/
│   │   │   └── defesa_civil_sc_alertas.py
│   │   └── config/
│   │       ├── appdaemon.yaml.example
│   │       └── apps.yaml.example
│   └── standalone-meshtastic/
│       ├── README.md
│       ├── main.py                 # Orquestrador principal
│       ├── requirements.txt
│       ├── config.example.yaml
│       ├── state.example.json
│       └── src/
│           ├── __init__.py
│           ├── config_manager.py
│           ├── state_manager.py
│           └── meshtastic_connector.py
├── examples/
│   └── defesa_civil_sc_alertas_state.example.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_STRUCTURE.md
│   └── SCRIPT_DETECTION.md
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── README.md
    ├── test_constants.py
    ├── test_models.py
    ├── test_rss_parser.py
    ├── test_message_formatter.py
    ├── test_region_filter.py
    ├── test_standalone_main.py
    └── fixtures/
        └── sample_feed.xml
```

## Direção por diretório

### `core/`

Módulos compartilhados entre Home Assistant e Standalone. Centraliza parsing, formatação, modelos e filtro regional. Evita duplicação de código e permite testes centralizados.

### `integrations/home-assistant-appdaemon/`

Versão usando Home Assistant + AppDaemon + integração Meshtastic. Consome `core/` para parser e formatação.

### `integrations/standalone-meshtastic/`

Versão sem dependência do Home Assistant. Conecta diretamente a um gateway Meshtastic via serial/TCP, gerencia estado local e implementa reconexão automática.

### `tests/`

Suite de testes com pytest. Cobre `core/` e a integração Standalone, incluindo parser RSS, formatação, filtro regional, modelos e reconexão.
