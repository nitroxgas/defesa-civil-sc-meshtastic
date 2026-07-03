# Arquitetura - Defesa Civil SC → Meshtastic

Documento descrevendo o design arquitetural e padrões do projeto após refatoração para uso de módulos compartilhados.

## Visão Geral

O projeto foi refatorado para centralizar lógica duplicada entre integrações (Home Assistant e Standalone) em um package `core/` reutilizável.

### Antes da Refatoração
```
home-assistant-appdaemon/
  └── defesa_civil_sc_alertas.py (658 linhas com toda a lógica)

standalone-meshtastic/src/
  ├── rss_parser.py (~157 linhas)
  ├── message_formatter.py (~249 linhas)
  └── [outros módulos]
```

**Problema**: ~400 linhas de código duplicado, risco de divergência entre versões.

### Depois da Refatoração
```
core/                          (Módulos compartilhados)
├── constants.py
├── models.py
├── rss_parser.py
├── message_formatter.py
├── region_filter.py
└── __init__.py

integrations/
├── home-assistant-appdaemon/   (Importa de core)
└── standalone-meshtastic/      (Importa de core)
```

**Benefícios**:
- ✅ Código DRY (Don't Repeat Yourself)
- ✅ Manutenção centralizada
- ✅ Testes compartilhados
- ✅ Melhor type safety com dataclasses
- ✅ Redução de ~400 linhas duplicadas

## Módulos Centralizados (core/)

### constants.py

Todas as constantes do projeto em um único lugar.

```python
# URLs e Feeds
FEED_URL = "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"

# Limites de mensagem Meshtastic
MAX_ALERT_MESSAGE_LEN = 180    # Compactação de conteúdo
MAX_LINK_MESSAGE_LEN = 180     # URL

# Persistência
MAX_HISTORY = 10               # Alertas armazenados
MAX_ALERTS_REPLY = 2           # Alertas por resposta DM

# Intervalos
POLL_INTERVAL_DIVISOR = 4      # Polling a cada 1/4 do período do feed
DEFAULT_INTERVAL_MINUTES = 15  # Fallback quando feed não informa período
MIN_INTERVAL_MINUTES = 15      # Limite mínimo de intervalo
MAX_INTERVAL_MINUTES = 1440    # Limite máximo de intervalo

# Delays entre mensagens (evitar flood)
CHANNEL_LINK_DELAY_SECONDS = 10
CHANNEL_ALERT_BATCH_DELAY_SECONDS = 10

# Mapeamento de prefixos
LEVEL_PREFIX_MAP = {
    "ALERTA": "AL:",
    "ATENÇÃO": "AT:",
    "OBSERVAÇÃO": "OBS:",
}
```

**Vantagens**:
- Valores únicos de verdade
- Fácil ajuste global
- Evita magic numbers no código

### models.py

Dataclasses para type safety e serialização automática.

```python
@dataclass
class Alert:
    guid: str
    title: str
    content: str
    link: str
    pub_date: str = ""
    seen_at: str = ""
    
    def to_dict() -> Dict
    def from_dict(data: Dict) -> Alert
```

```python
@dataclass
class State:
    sent_guids: List[str]
    ignored_guids: List[str]
    alerts: List[Alert]
    update_period: Optional[str]
    update_frequency: Optional[int]
    created_at: str
    last_updated: str
    
    def to_dict() -> Dict
    def from_dict(data: Dict) -> State
    def add_ignored_guid(guid: str) -> bool
```

**Vantagens**:
- Type hints em tempo de desenvolvimento
- Serialização/deserialização automática
- Validação implícita de estrutura
- Imutabilidade opcional

### rss_parser.py

Parser RSS para Defesa Civil SC.

```python
class RSSParser:
    def fetch_feed() -> bytes
    def parse_feed(xml_bytes: bytes) -> Tuple[List[Alert], ...]
    def parse_update_interval(root) -> Tuple[period, frequency, minutes]
    def parse_and_fetch() -> Tuple[List[Alert], ...]
```

**Responsabilidades**:
- Download de feed RSS via HTTP
- Parsing de XML e extração de items
- Interpretação de `sy:updatePeriod` e `sy:updateFrequency`
- Cálculo do intervalo de polling: 1/4 do período informado pelo feed
- Sobreposição do intervalo via configuração (`interval_minutes`)
- Respeito a limites de intervalo (15 min - 24 horas)

**Tratamento de Erros**:
- Timeout configurável (padrão 30s)
- Fallback para `DEFAULT_INTERVAL_MINUTES` se parsing falhar ou feed não informar período
- Logging de exceções

### message_formatter.py

Formatação e compactação de mensagens para LoRa.

```python
class MessageFormatter:
    def strip_html(value: str) -> str
    def normalize_dash(value: str) -> str
    def normalize_level_prefix(value: str) -> str
    def compact_alert_text(value: str) -> str
    def normalize_text(value: str, max_len: int) -> str
    def truncate_text(value: str, max_len: int) -> str
    def build_alert_messages(alert: dict) -> Tuple[str, str]
    def sanitize_alert(alert: dict) -> dict
```

**Fluxo de Compactação**:
1. Remover HTML tags
2. Normalizar travessões
3. Converter prefixos longos (ALERTA → AL:)
4. Remover texto institucional repetitivo
5. Aplicar compactações de termos frequentes
6. Truncar ao limite de caracteres

**Exemplo**:
```
Input:  "ALERTA - Temporal severo com rajadas de vento nas próximas 3 horas. Ocorrências ligue 199 ou 193."
Output: "DC-SC AL: temporal severo c/ rajadas vento nas próximas 3h. Ocorrências ligue 199/193."
        (180 chars, fit em MAX_ALERT_MESSAGE_LEN=180)
```

**Compactações Aplicadas**:
- Regiões: "Grande Florianópolis" → "Gde Fpolis"
- Fenômenos: "ALAGAMENTOS" → "alag.", "ENXURRADAS" → "enxurr."
- Períodos: "nas próximas 3 horas" → "Val: 3h"
- Preposições: "com" → "c/"

### region_filter.py

Filtro regional por mesorregião e município de Santa Catarina.

```python
class RegionFilter:
    def __init__(config: Dict, json_path: Optional[str])
    def should_send(alert: Alert) -> bool
    def list_mesorregioes() -> List[str]
    def list_municipios() -> List[str]
```

**Responsabilidades**:
- Carregar dados regionais de `core/sc_mesorregioes_microrregioes_municipios.json`
- Normalizar texto (remover acentos, caixa baixa)
- Expandir abreviações comuns ("Gde Fpolis" → "Grande Florianópolis")
- Decidir se alerta deve ser enviado com base no título/conteúdo
- Registrar GUIDs ignorados para deduplicação futura

**Modos**:
- `mesorregiao`: filtra apenas por mesorregiões configuradas
- `municipio`: filtra apenas por municípios configurados
- `both`: envia se alerta mencionar mesorregião OU município configurado

**Uso**:
```python
from core.region_filter import RegionFilter

rf = RegionFilter({
    "enabled": True,
    "mode": "both",
    "mesorregioes": ["Grande Florianópolis"],
    "municipios": ["Florianópolis"]
})

if rf.should_send(alert):
    # enviar alerta
```

## Integrações

### Home Assistant + AppDaemon

```
integrations/home-assistant-appdaemon/
├── apps/
│   └── defesa_civil_sc_alertas.py (agora 380 linhas, -42% de redução)
└── config/
    ├── appdaemon.yaml.example
    └── apps.yaml.example
```

**Mudanças na Refatoração**:
- Remover ~400 linhas de lógica duplicada
- Importar `RSSParser`, `MessageFormatter` de `core`
- Usar `State`, `Alert` dataclasses
- Simplificar métodos (remove strip_html, normalize_dash, etc.)
- Manter funcionalidade idêntica

**Fluxo**:
1. AppDaemon initia integração
2. Usa `RSSParser` para buscar/parsear feed
3. Usa `MessageFormatter` para compactar mensagens
4. Usa `State` para persistir em JSON
5. Envia via `notify` service do HA ou responde DM

### Standalone Meshtastic (Python)

```
integrations/standalone-meshtastic/
├── main.py
├── requirements.txt
├── config.example.yaml
├── src/
│   ├── config_manager.py
│   ├── state_manager.py
│   └── meshtastic_connector.py
└── README.md
```

**Mudanças na Refatoração**:
- Remover `src/rss_parser.py` (agora em core)
- Remover `src/message_formatter.py` (agora em core)
- Atualizar imports em `main.py` para usar core
- Refatorar `StateManager` para usar `State` dataclass

**Fluxo**:
1. Ler config YAML (incluindo `region_filter`)
2. Conectar Meshtastic (serial/TCP)
3. Registrar callback de DM
4. Polling loop com `RSSParser`
5. Aplicar filtro regional (`RegionFilter`) quando ativado
6. Enviar alertas via `MeshtasticConnector`
7. Responder DMs com histórico filtrado
8. Persistir estado com `StateManager`
9. Monitorar conexão e reconectar automaticamente em caso de queda

**Reconexão Automática**:
- Verificação de conexão a cada 30s (conectado) ou 5s (desconectado)
- Backoff exponencial ao reconectar: 30s, 60s, 120s, 240s, 300s (máx)
- Envios que falham por `ConnectionResetError`, `BrokenPipeError` ou `OSError` marcam a interface como desconectada
- Callbacks de DM são re-registrados após reconexão
- Thread-safe via `threading.RLock`

## Testes Centralizados

```
tests/
├── conftest.py                # Fixtures pytest
├── test_constants.py          # Constantes e limites
├── test_models.py            # Dataclasses Alert/State
├── test_rss_parser.py        # Parser RSS e intervalos
├── test_message_formatter.py # Compactação de mensagens
├── test_region_filter.py     # Filtro regional
├── test_standalone_main.py   # Integração Standalone (reconexão, DM, filtro)
└── fixtures/
    └── sample_feed.xml       # Feed de amostra
```

**Cobertura**:
- ✅ 74+ testes para validar funcionalidade de core/ e integração Standalone
- ✅ Feed RSS parsing com diferentes períodos
- ✅ Compactação de mensagens em múltiplos idiomas
- ✅ Serialização/deserialização de modelos (incluindo `ignored_guids`)
- ✅ Filtro regional por mesorregião/município
- ✅ Reconexão automática e detecção de desconexão
- ✅ Resposta a DM com filtro regional
- ✅ Edge cases e limites

**Executar**:
```bash
pytest tests/ -v
pytest tests/ --cov=core
```

## Fluxo de Dados

### Checagem de Feed
```
┌─────────────────────────────────────────────────────────┐
│ 1. RSSParser.parse_and_fetch()                          │
│    - Busca feed RSS                                     │
│    - Parseia XML                                        │
│    - Retorna List[Alert], intervalo atualizado         │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 2. State.sent_guids / State.ignored_guids comparação   │
│    - Novo alerta? guid não em sent_guids/ignored_guids  │
│    - Evita reenvio e reprocessamento                    │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 3. RegionFilter.should_send(alert) (opcional)          │
│    - Verifica mesorregião/município no título/conteúdo  │
│    - Se não bater: State.add_ignored_guid() + skip      │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 4. MessageFormatter.build_alert_messages(alert)        │
│    - Compacta conteúdo (max 180 chars)                 │
│    - Formata URL (max 180 chars)                       │
│    - Retorna (msg_conteúdo, msg_link)                  │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 5. Envio via integração                                │
│    - HA: via notify service                            │
│    - Standalone: via MeshtasticConnector               │
│    - Se falhar por erro de rede: marcar desconectado  │
│      e não adicionar guid em sent_guids                 │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 6. State.add_sent_guid() + State.to_dict()             │
│    - Marca como enviado (somente se envio OK)          │
│    - Persiste em JSON                                  │
└─────────────────────────────────────────────────────────┘
```

## Padrões de Design

### Separation of Concerns
Cada módulo tem responsabilidade única:
- `constants.py` → Configuração
- `models.py` → Estrutura de dados
- `rss_parser.py` → Fonte de dados
- `message_formatter.py` → Transformação
- `region_filter.py` → Regras de negócio regional
- `meshtastic_connector.py` → Integração e lifecycle de conexão (Standalone)

### DRY (Don't Repeat Yourself)
Lógica comum centralizada em `core/`, reutilizada por ambas integrações.

### Type Safety
Dataclasses com type hints:
```python
def build_alert_messages(self, alert: dict) -> Tuple[str, str]
```

### Testability
Cada módulo é independente e testável:
```python
parser = RSSParser()
items, period, freq, minutes = parser.parse_feed(xml_bytes)

formatter = MessageFormatter()
msg1, msg2 = formatter.build_alert_messages(item)
```

## Migrando Integrações para core/

Para adicionar nova integração, reutilizar `core/`:

```python
from core import RSSParser, MessageFormatter, State, Alert
from core.region_filter import RegionFilter

# Seu código específico
parser = RSSParser()
formatter = MessageFormatter()
state = State()
region_filter = RegionFilter({"enabled": False})

# Lógica de integração
```

Exemplo: Integração MQTT, Discord, Telegram, etc.

## Evolução Futura

- [x] Filtros por região/município na core (concluído: `RegionFilter`)
- [x] Reconexão automática e detecção de desconexão (concluído: Standalone)
- [ ] Refatorar `StateManager` para usar patterns de database abstraction
- [ ] Adicionar source diversity (não só RSS)
- [ ] Métricas e monitoring centralizados
- [ ] Plugin architecture para custom formatters
- [ ] Filtros por severidade (`AL:`, `AT:`, `OBS:`)

