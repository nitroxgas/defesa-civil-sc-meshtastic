# Integração Home Assistant + AppDaemon

Esta integração lê o feed RSS de alertas da Defesa Civil de Santa Catarina e envia novos alertas para um canal Meshtastic via entidade `notify.mesh_channel_*` do Home Assistant.

## ℹ️ Refatoração - Uso de Módulos Compartilhados

A partir da v1.0, esta integração usa módulos centralizados em `core/` para evitar duplicação de código:

- `core.RSSParser` - Parser RSS
- `core.MessageFormatter` - Compactação de mensagens  
- `core.State`, `core.Alert` - Modelos de dados
- `core.constants` - Constantes centralizadas

**Redução de código**: 658 linhas → 380 linhas (-42%)

Veja [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) para detalhes de arquitetura.

### Pré-requisitos

- Home Assistant funcionando.
- Integração Meshtastic instalada e conectada a um gateway.
- Canal Meshtastic criado, por exemplo `Alertas-SC`.
- Entidade `notify.mesh_channel_*` disponível para o canal.
- Add-on AppDaemon instalado.

### Arquivos

```text
apps/defesa_civil_sc_alertas.py       # App AppDaemon
config/apps.yaml.example              # Exemplo de configuração do app
config/appdaemon.yaml.example         # Exemplo mínimo de AppDaemon
```

## Instalação

### 1. Instale o add-on AppDaemon no Home Assistant.
 - Para o Home Assistant OS após a instalação os arquivos ficam em /root/addon_config/<ALGUMACOISA>_appdaemon/ - Este será o diretório raiz para o AppDaemon e assumido daqui para frente na documentação;

 ```text
 O arquivo:
/root/addon_config/<ALGUMACOISA>_appdaemon/config/apps/defesa_civil_sc_alertas.py

Será referenciado como:
/config/apps/defesa_civil_sc_alertas.py
```

### 2. Copie `integrations/home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py` para o diretório onde está instalado seu AppDaemon:

```text
/config/apps/defesa_civil_sc_alertas.py
```

### 3. Configurar o AppDaemon

Use como base `integrations/home-assistant-appdaemon/config/apps.yaml.example` e copie para: 

```text
/config/apps.yaml
```
Substitua:

- `notify.mesh_channel_<NOME_DO_CANAL>` pela entidade real do seu canal;
- `0000000000` pelo node ID numérico do gateway Meshtastic.

Exemplo:

```yaml
defesa_civil_sc_alertas:
  module: defesa_civil_sc_alertas
  class: DefesaCivilSCAlertas
  notify_entity: notify.mesh_channel_<NOME_DO_CANAL>
  gateway_node_id: 0000000000
  test_mode: false
```

### 4. Reiniciar o AppDaemon

Depois de copiar os arquivos e ajustar a configuração, reinicie o add-on AppDaemon.

## Teste sem esperar novo alerta

Ative o modo de teste:

```yaml
test_mode: true
```

Reinicie o AppDaemon. O app enviará o alerta mais recente salvo no estado local; se não houver estado, buscará o feed, populará o histórico e enviará o item mais recente.

Depois do teste, volte para:

```yaml
test_mode: false
```


## Operação

- Lê o feed RSS a cada hora ou conforme `sy:updatePeriod`/`sy:updateFrequency`.
- Armazena os últimos 10 alertas.
- Evita reenviar alertas repetidos usando `guid`.
- Na primeira execução, armazena o histórico sem enviar os 10 alertas antigos, evitando flood.
- Responde mensagem direta `ALERTAS` com os 3 últimos alertas armazenados.
