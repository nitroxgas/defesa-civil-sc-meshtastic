# Defesa Civil SC → Meshtastic

Integração para ler alertas publicados pela Defesa Civil de Santa Catarina e redistribuir mensagens resumidas para uma malha Meshtastic.

A primeira versão usa **Home Assistant + AppDaemon + integração Meshtastic**. A estrutura do repositório já separa essa integração de futuras versões standalone sem Home Assistant.

> Este projeto não é oficial da Defesa Civil. Use como integração comunitária e mantenha sempre os canais oficiais de alerta como referência primária.

## Funcionalidades atuais

- Lê o feed RSS da categoria de alertas da Defesa Civil SC.
- Respeita os campos RSS `sy:updatePeriod` e `sy:updateFrequency` para definir o intervalo de leitura.
- Armazena os últimos 10 alertas.
- Evita reenvio de alertas repetidos usando `guid`.
- Envia cada novo alerta para canal Meshtastic via `notify.mesh_channel_*` do Home Assistant.
- Envia o alerta em duas mensagens:
  - resumo compactado;
  - link do alerta.
- Responde mensagens diretas com texto `ALERTAS`, retornando os 3 últimos alertas armazenados.
- Tem modo de teste para validar o envio sem depender de novos alertas reais.
- Compacta prefixos longos:
  - `ALERTA` → `AL:`
  - `ATENÇÃO` → `AT:`
  - `OBSERVAÇÃO` → `OBS:`

## Fonte de dados

Feed RSS usado pela integração:

```text
https://www.defesacivil.sc.gov.br/categoria/alerta/feed/
```

Campos principais utilizados:

- `item/title`
- `item/content:encoded`
- `item/guid`
- `channel/sy:updatePeriod`
- `channel/sy:updateFrequency`

## Estrutura do projeto

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

## Instalação rápida — Home Assistant + AppDaemon

### 1. Pré-requisitos

- Home Assistant funcionando.
- Integração Meshtastic instalada e conectada a um gateway.
- Canal Meshtastic criado, por exemplo `Alertas-SC`.
- Entidade `notify.mesh_channel_*` disponível para o canal.
- Add-on AppDaemon instalado.

### 2. Copiar o app

Copie:

```text
integrations/home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py
```

para:

```text
/config/apps/defesa_civil_sc_alertas.py
```

### 3. Configurar o AppDaemon

Use como base:

```text
integrations/home-assistant-appdaemon/config/apps.yaml.example
```

Exemplo:

```yaml
defesa_civil_sc_alertas:
  module: defesa_civil_sc_alertas
  class: DefesaCivilSCAlertas
  notify_entity: notify.mesh_channel_<NOME_DO_CANAL>
  gateway_node_id: 0000000000
  test_mode: false
```

Substitua:

- `notify.mesh_channel_<NOME_DO_CANAL>` pela entidade real do seu canal;
- `0000000000` pelo node ID numérico do gateway Meshtastic.

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

## Formato das mensagens

Exemplo de mensagem compactada:

```text
DC-SC AL: 01/07 11:47 - tempestade severa c/ vento, alag., granizo, raios e enxurr. Mun: Bom Jardim da Serra... Val: 1h. 199/193.
```

Segunda mensagem:

```text
Link: https://www.defesacivil.sc.gov.br/?p=XXXXX
```

## Mensagens diretas

Se outro node Meshtastic enviar mensagem direta ao gateway com:

```text
ALERTAS
```

O app responde com os 3 últimos alertas armazenados, cada um no mesmo formato de duas mensagens.

## Arquivos que não devem ir para o GitHub

Não publique arquivos reais de estado ou configuração local com dados da sua malha:

```text
/config/apps/defesa_civil_sc_alertas_state.json
/config/apps/apps.yaml
/config/appdaemon.yaml
```

O `.gitignore` deste projeto já ignora esses arquivos quando usados dentro do repositório.

## Próximas versões sugeridas

### Standalone sem Home Assistant

Pasta sugerida:

```text
integrations/standalone-meshtastic/
```

Possíveis transportes:

- Python + `meshtastic` via serial/USB;
- Python + Meshtastic TCP;
- MQTT do Meshtastic;
- serviço Linux com `systemd`;
- container Docker.

### Filtros futuros

- Filtrar por município.
- Filtrar por região da Defesa Civil SC.
- Filtrar por severidade: `AL:`, `AT:`, `OBS:`.
- Enviar somente alertas que mencionem regiões configuradas.
- Usar CAP/Common Alerting Protocol quando houver fonte pública estruturada.

## Aviso operacional

Meshtastic usa rádio LoRa e tem capacidade limitada de payload e airtime. Evite flood:

- mantenha mensagens curtas;
- evite reenviar histórico completo na inicialização;
- use canais privados/comunitários;
- respeite boas práticas de uso da malha local.

## Licença

MIT. Veja `LICENSE`.
