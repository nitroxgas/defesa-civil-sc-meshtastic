# Integração Home Assistant + AppDaemon

Esta integração lê o feed RSS de alertas da Defesa Civil de Santa Catarina e envia novos alertas para um canal Meshtastic via entidade `notify.mesh_channel_*` do Home Assistant.

## Arquivos

```text
apps/defesa_civil_sc_alertas.py       # App AppDaemon
config/apps.yaml.example              # Exemplo de configuração do app
config/appdaemon.yaml.example         # Exemplo mínimo de AppDaemon
```

## Instalação

1. Instale o add-on AppDaemon no Home Assistant.
 - Para o Home Assistant OS após a instalação os arquivos ficam em /root/addon_config/<ALGUMACOISA>_appdaemon/ - Este será o diretório raiz para o AppDaemon e assumido daqui para frente na documentação;
 
 ```text
 O arquivo:
/root/addon_config/<ALGUMACOISA>_appdaemon/config/apps/defesa_civil_sc_alertas.py

Será referenciado como:
/config/apps/defesa_civil_sc_alertas.py
```

2. Copie `apps/defesa_civil_sc_alertas.py` para o diretório onde está instalado seu AppDaemon:

```text
/config/apps/defesa_civil_sc_alertas.py
```

3. Copie o bloco de `config/apps.yaml.example` para:

```text
/config/apps/apps.yaml
```

4. Ajuste:

```yaml
notify_entity: notify.mesh_channel_<NOME_DO_CANAL>
gateway_node_id: 0000000000
test_mode: false
```

5. Reinicie o AppDaemon.

## Teste

Para testar sem esperar novos alertas, use:

```yaml
test_mode: true
```

Reinicie o AppDaemon. O app enviará o alerta mais recente salvo ou buscará o feed para popular o histórico.

Depois do teste, retorne para:

```yaml
test_mode: false
```

## Operação

- Lê o feed RSS a cada hora ou conforme `sy:updatePeriod`/`sy:updateFrequency`.
- Armazena os últimos 10 alertas.
- Evita reenviar alertas repetidos usando `guid`.
- Na primeira execução, armazena o histórico sem enviar os 10 alertas antigos, evitando flood.
- Responde mensagem direta `ALERTAS` com os 3 últimos alertas armazenados.
