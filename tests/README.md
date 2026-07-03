# Testes

Suite de testes automatizados com pytest. Execute com:

```bash
pytest tests/ -v
```

## Cobertura atual

- **test_constants.py**: constantes de tamanho, prefixos e intervalos.
- **test_models.py**: serialização/deserialização de `Alert` e `State`.
- **test_rss_parser.py**: parsing de feed RSS, cálculo de intervalo e extração de alertas.
- **test_message_formatter.py**: remoção de HTML, compactação de regiões/termos e limitação de tamanho.
- **test_region_filter.py**: matching por mesorregião, município, abreviações e modos de filtro.
- **test_standalone_main.py**: integração do Standalone, incluindo filtro regional em DM, deduplicação, monitoramento e reconexão automática.

## Principais cenários validados

- Compactação de prefixos `ALERTA`, `ATENÇÃO`, `OBSERVAÇÃO` para `AL:`, `AT:`, `OBS:`;
- Remoção de HTML em `content:encoded`;
- Compactação de regiões e eventos meteorológicos;
- Limitação de tamanho das mensagens para LoRa (180 caracteres);
- Deduplicação por `guid`;
- Filtro regional por mesorregião e município;
- Reconexão automática com backoff exponencial;
- Não marcar alertas como enviados quando o envio falha.
