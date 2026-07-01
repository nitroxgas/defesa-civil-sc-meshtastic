# Versão standalone Meshtastic

Esta pasta é reservada para versões sem Home Assistant.

## Ideias de implementação

### Opção 1 — Python + Meshtastic serial/TCP

Fluxo previsto:

```text
RSS Defesa Civil SC → parser Python → deduplicação SQLite/JSON → meshtastic-python → canal Alertas-SC
```

### Opção 2 — MQTT

Fluxo previsto:

```text
RSS Defesa Civil SC → parser Python → MQTT Meshtastic → canal Alertas-SC
```

### Opção 3 — serviço Linux

Executar como daemon via `systemd`, com configuração em arquivo `.env` ou YAML.

## Cuidados

- Limitar tamanho das mensagens.
- Evitar flood inicial.
- Implementar backoff em caso de erro de rede.
- Não publicar chaves de canal Meshtastic.
