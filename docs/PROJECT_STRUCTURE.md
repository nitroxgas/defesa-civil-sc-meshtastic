# Estrutura sugerida do projeto

```text
defesa-civil-sc-meshtastic/
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── .gitignore
├── integrations/
│   ├── home-assistant-appdaemon/
│   │   ├── README.md
│   │   ├── apps/
│   │   │   └── defesa_civil_sc_alertas.py
│   │   └── config/
│   │       ├── appdaemon.yaml.example
│   │       └── apps.yaml.example
│   └── standalone-meshtastic/
│       └── README.md
├── examples/
│   └── defesa_civil_sc_alertas_state.example.json
├── docs/
│   └── PROJECT_STRUCTURE.md
└── tests/
    └── README.md
```

## Direção para próximas versões

### `integrations/home-assistant-appdaemon/`

Versão atual usando Home Assistant + AppDaemon + integração Meshtastic.

### `integrations/standalone-meshtastic/`

Local sugerido para uma versão sem Home Assistant. Possíveis transportes:

- conexão serial/USB com gateway Meshtastic;
- conexão TCP com node Meshtastic;
- MQTT do Meshtastic;
- daemon systemd em Linux;
- Docker Compose.

### `tests/`

Local para testes do parser RSS, compactação de texto e deduplicação.
