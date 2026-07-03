# Segurança e privacidade

Este projeto foi pensado para ser compartilhado sem credenciais. Antes de publicar forks, issues ou exemplos de configuração, revise se há dados sensíveis.

Não publique:

- `gateway_node_id` real se você considera o identificador do seu node sensível;
- nomes de canais privados no Meshtastic;
- chaves de canais privados no Meshtastic;
- arquivos reais `defesa_civil_sc_alertas_state.json` contendo histórico operacional da sua malha;
- tokens do Home Assistant, MQTT, Telegram ou qualquer outro serviço;
- logs com IDs de nodes, nomes longos, short names ou localização.

Use os arquivos `.example` como base para documentação pública.
