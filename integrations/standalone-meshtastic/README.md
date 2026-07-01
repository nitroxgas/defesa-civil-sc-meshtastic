# Versão Standalone Meshtastic

Integração sem dependência do Home Assistant que lê alertas RSS da Defesa Civil SC e redistribui para uma malha Meshtastic via conexão serial ou TCP.

## Arquitetura

```text
RSS Defesa Civil SC
        ↓
   RSSParser
        ↓
   MessageFormatter (compactação)
        ↓
   StateManager (deduplicação + histórico JSON)
        ↓
   MeshtasticConnector (serial/TCP)
        ↓
   Canal Meshtastic "Alertas-SC"
```

## Pré-requisitos

- Python 3.8+
- Gateway Meshtastic (rodando, acessível via USB/Serial ou TCP)
- Conexão com a internet para acessar feed RSS

## Instalação

### 1. Criar ambiente virtual

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar aplicação

Copie `config.example.yaml` para `config.yaml` e customize:

```bash
cp config.example.yaml config.yaml
```

Edite `config.yaml`:

```yaml
meshtastic:
  connection_type: serial  # ou "tcp"
  serial_port: ""          # deixar vazio para auto-detect
  # OU para TCP:
  # tcp_host: "192.168.1.100"
  # tcp_port: 4403

channel:
  name: "Alertas-SC"       # nome do canal
  number: 0                # índice do canal

feed:
  url: "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"
  default_interval_minutes: 60

state:
  file: "./state.json"     # arquivo JSON para histórico

direct_message:
  enabled: true
  trigger_word: "ALERTAS"  # palavra para solicitar últimos alertas

test_mode: false           # true para enviar 1 alerta de teste

logging:
  level: INFO              # DEBUG, INFO, WARNING, ERROR
  file: null               # deixar null para apenas console
```

## Execução

### Modo normal

```bash
python main.py config.yaml
```

### Modo de teste

Edite `config.yaml` e defina `test_mode: true`, depois execute. O app enviará o alerta mais recente armazenado ou buscará um do feed.

### Executar em background (Linux/Mac)

```bash
nohup python main.py config.yaml > app.log 2>&1 &
```

## Funcionalidades

### 1. Polling automático do feed
- Lê feed RSS a cada intervalo (padrão 60 min, respeitando `sy:updatePeriod`/`sy:updateFrequency`)
- Compacta mensagens para caber em LoRa (~150-180 chars)
- Evita reenvio usando deduplicação por GUID

### 2. Compactação de texto
Reduz tamanho de alertas:
- Prefixos: `ALERTA` → `AL:`, `ATENÇÃO` → `AT:`, `OBSERVAÇÃO` → `OBS:`
- Termos: `TEMPESTADE SEVERA` → `tempestade severa`, `RAJADAS DE VENTO` → `vento`
- Regiões: `Grande Florianópolis` → `Gde Fpolis`
- Validades: `nas próximas 2 horas` → `Val: 2h`

### 3. Mensagens em canal
Envia 2 mensagens por alerta:
1. Conteúdo compactado (max 150 chars): `DC-SC AL: ...`
2. Link (max 180 chars): `Link: https://...`

### 4. Resposta a mensagens diretas
Se outro node enviar `ALERTAS`, responde com os 3 últimos alertas armazenados.

### 5. Histórico persistente
Mantém últimos 10 alertas em JSON (`state.json`) para consultas offline.

## Estrutura de arquivos

```text
integrations/standalone-meshtastic/
├── main.py                   # Script principal
├── requirements.txt          # Dependências Python
├── config.example.yaml       # Exemplo de configuração
├── config.yaml              # Configuração (criar a partir do .example)
├── state.json               # Histórico de alertas (auto-criado)
├── defesa_civil_sc_alertas.log  # Log da aplicação (opcional)
└── src/
    ├── __init__.py
    ├── config_manager.py     # Gerenciar config YAML
    ├── state_manager.py      # Persistir estado JSON
    ├── rss_parser.py         # Parser RSS
    ├── message_formatter.py  # Compactação de mensagens
    └── meshtastic_connector.py  # Integração Meshtastic
```

## Conexão serial

### Linux/Mac (auto-detect)

```yaml
meshtastic:
  connection_type: serial
  serial_port: ""  # deixar vazio
```

### Windows (específico)

```yaml
meshtastic:
  connection_type: serial
  serial_port: "COM3"  # verificar em Gerenciador de Dispositivos
```

### Linux (específico)

```bash
# Listar portas disponíveis
ls /dev/tty* | grep USB
# Configurar em config.yaml:
# serial_port: "/dev/ttyUSB0"
```

## Conexão TCP

Para gateways que suportam TCP (ex: T-Deck):

```yaml
meshtastic:
  connection_type: tcp
  tcp_host: "192.168.1.100"  # IP do gateway
  tcp_port: 4403
```

## Troubleshooting

### "Porta serial não encontrada"
- Conectar gateway USB
- Linux: Executar `sudo usermod -a -G dialout $USER` para permissões
- Windows: Verificar Gerenciador de Dispositivos

### "Falha ao conectar TCP"
- Verificar IP e porta do gateway
- Verificar firewall/rede

### "Feed RSS não carrega"
- Verificar conexão de internet
- Verificar URL do feed em config.yaml

### "Mensagens não estão chegando"
- Verificar se canal está configurado corretamente
- Testar modo de teste (`test_mode: true`)
- Aumentar nível de logging para DEBUG

## Modo daemon (Linux/Systemd)

Criar arquivo `/etc/systemd/system/defesa-civil-sc-meshtastic.service`:

```ini
[Unit]
Description=Defesa Civil SC Meshtastic Alerts
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/integrations/standalone-meshtastic
ExecStart=/path/to/venv/bin/python main.py config.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar e iniciar:

```bash
sudo systemctl enable defesa-civil-sc-meshtastic
sudo systemctl start defesa-civil-sc-meshtastic
sudo systemctl status defesa-civil-sc-meshtastic
```

Ver logs:

```bash
sudo journalctl -u defesa-civil-sc-meshtastic -f
```

## Cuidados

- **Limitar tamanho de mensagens**: LoRa tem payload limitado
- **Evitar flood inicial**: Primeira execução apenas carrega histórico
- **Implementar backoff**: App aguarda 20s entre mensagens
- **Não publicar chaves**: Não incluir chaves de canal em configs públicas
- **Respeitar boas práticas de malha**: Não bombardear canal com muitas mensagens

## Próximas versões sugeridas

- [ ] MQTT como alternativa
- [ ] Container Docker
- [ ] Filtros por município/região
- [ ] Interface web para monitoramento
- [ ] Sincronização com Home Assistant

## Licença

MIT. Veja `LICENSE`.
