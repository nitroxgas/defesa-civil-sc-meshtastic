# Plano de Refatoração: Centralizar Módulos Compartilhados

> **Status:** 📋 Planejado (não implementado)  
> **Versão:** v1.0  
> **Data:** 2026-07-01  
> **Objetivo:** Eliminar código duplicado entre integrações HA e Standalone

---

## 📋 Resumo Executivo

Atualmente existe código duplicado entre as duas integrações:
- Parser RSS duplicado
- Lógica de compactação de mensagens duplicada
- Constantes duplicadas

Este plano centraliza esses módulos em um package `core/` compartilhado, reduzindo ~650 linhas de código duplicado e facilitando manutenção futura.

---

## 🎯 Objetivos

| Objetivo | Benefício |
|----------|-----------|
| **Eliminar duplicação** | Mesmo código em 1 lugar, 2 implementações usam |
| **Facilitar manutenção** | Bug fix beneficia ambas integrações |
| **Padronizar qualidade** | Testes centralizados cobrem ambas |
| **Versionamento claro** | Core é a versão do projeto |
| **Extensibilidade** | Novas integrações (MQTT, Docker) herdam código testado |

---

## 🔄 Arquitetura Proposta

### Atual (com duplicação)

```
home-assistant-appdaemon/
├── defesa_civil_sc_alertas.py (500 linhas: parser + formatter + HA logic)

standalone-meshtastic/src/
├── rss_parser.py (200 linhas: parser RSS)
├── message_formatter.py (150 linhas: compactação)
├── config_manager.py (específico)
├── state_manager.py (específico)
└── meshtastic_connector.py (específico)
```

### Nova (centralizada)

```
core/
├── __init__.py
├── constants.py              # ✨ NOVO: constantes compartilhadas
├── models.py                 # ✨ NOVO: Alert, State dataclasses
├── rss_parser.py            # 📦 Mover de standalone-meshtastic/src/
└── message_formatter.py     # 📦 Mover de standalone-meshtastic/src/

home-assistant-appdaemon/
├── defesa_civil_sc_alertas.py (200 linhas: apenas HA logic)

standalone-meshtastic/src/
├── config_manager.py (específico)
├── state_manager.py (específico)
└── meshtastic_connector.py (específico)

tests/
├── test_rss_parser.py
├── test_message_formatter.py
├── test_models.py
└── fixtures/
    └── sample_feed.xml
```

---

## 📦 Módulos a Centralizar

### 1. `core/constants.py` (NOVO)

```python
"""Constantes compartilhadas entre integrações."""

# URLs
FEED_URL = "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"

# Limites de mensagem (Meshtastic LoRa)
MAX_ALERT_MESSAGE_LEN = 180
MAX_LINK_MESSAGE_LEN = 180

# Histórico
MAX_HISTORY = 10
MAX_ALERTS_REPLY = 2

# Delays entre envios
CHANNEL_LINK_DELAY_SECONDS = 10
CHANNEL_ALERT_BATCH_DELAY_SECONDS = 10

# Configuração do feed RSS
POLL_INTERVAL_DIVISOR = 4        # Polling a cada 1/4 do período do feed
DEFAULT_INTERVAL_MINUTES = 15    # Fallback quando feed não informa período
MIN_INTERVAL_MINUTES = 15        # Limite mínimo de intervalo
MAX_INTERVAL_MINUTES = 1440      # Limite máximo de intervalo
DEFAULT_TIMEOUT_SECONDS = 30

# Prefixos de nível de alerta
LEVEL_PREFIX_MAP = {
    "ALERTA": "AL:",
    "ATENÇÃO": "AT:",
    "ATENCAO": "AT:",
    "OBSERVAÇÃO": "OBS:",
    "OBSERVACAO": "OBS:",
}
```

### 2. `core/models.py` (NOVO)

Classes dataclass para tipagem forte e serialização:

```python
"""Modelos de dados compartilhados."""

from dataclasses import dataclass, asdict, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Alert:
    """Representa um alerta da Defesa Civil SC."""
    
    guid: str
    title: str
    content: str
    link: str
    pub_date: str
    seen_at: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        """Cria Alert a partir de dicionário."""
        return cls(**{k: data.get(k, "") for k in cls.__dataclass_fields__})
    
    def to_dict(self) -> dict:
        """Converte Alert para dicionário."""
        return asdict(self)


@dataclass
class State:
    """Estado persistido de alertas enviados."""
    
    sent_guids: List[str] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    update_period: Optional[str] = None
    update_frequency: int = 1
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    
    @classmethod
    def from_dict(cls, data: dict) -> "State":
        """Cria State a partir de dicionário (carregado do JSON)."""
        alerts = [Alert.from_dict(a) for a in data.get("alerts", [])]
        return cls(
            sent_guids=data.get("sent_guids", []),
            alerts=alerts,
            update_period=data.get("update_period"),
            update_frequency=data.get("update_frequency", 1),
            last_updated=data.get("last_updated", datetime.now().isoformat(timespec="seconds")),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds"))
        )
    
    def to_dict(self) -> dict:
        """Converte State para dicionário (para salvar no JSON)."""
        return {
            "sent_guids": self.sent_guids,
            "alerts": [a.to_dict() for a in self.alerts],
            "update_period": self.update_period,
            "update_frequency": self.update_frequency,
            "last_updated": self.last_updated,
            "created_at": self.created_at
        }
```

### 3. `core/rss_parser.py` (MOVER)

Mover de `integrations/standalone-meshtastic/src/rss_parser.py`

### 4. `core/message_formatter.py` (MOVER)

Mover de `integrations/standalone-meshtastic/src/message_formatter.py`

### 5. `core/__init__.py` (NOVO)

```python
"""Módulos compartilhados da integração Defesa Civil SC."""

from .constants import (
    FEED_URL,
    MAX_ALERT_MESSAGE_LEN,
    MAX_LINK_MESSAGE_LEN,
    MAX_HISTORY,
    MAX_ALERTS_REPLY,
    LEVEL_PREFIX_MAP,
)
from .models import Alert, State
from .rss_parser import RSSParser
from .message_formatter import MessageFormatter

__all__ = [
    "FEED_URL",
    "MAX_ALERT_MESSAGE_LEN",
    "MAX_LINK_MESSAGE_LEN",
    "MAX_HISTORY",
    "MAX_ALERTS_REPLY",
    "LEVEL_PREFIX_MAP",
    "Alert",
    "State",
    "RSSParser",
    "MessageFormatter",
]
```

---

## 📋 Fases de Implementação

### Fase 1: Criar `core/` Package

- [ ] Criar diretório `core/`
- [ ] Criar `core/__init__.py` com exports
- [ ] Criar `core/constants.py` com todas as constantes
- [ ] Criar `core/models.py` com dataclasses Alert, State

**Tempo estimado:** 30 minutos

---

### Fase 2: Mover Módulos Compartilhados

- [ ] Mover `integrations/standalone-meshtastic/src/rss_parser.py` → `core/rss_parser.py`
- [ ] Mover `integrations/standalone-meshtastic/src/message_formatter.py` → `core/message_formatter.py`
- [ ] Atualizar imports no código movido (se houver)
- [ ] Verificar que não há referências circulares

**Tempo estimado:** 20 minutos

---

### Fase 3: Refatorar Standalone

- [ ] Atualizar `integrations/standalone-meshtastic/main.py`
  - Trocar `from src.rss_parser import RSSParser` → `from core import RSSParser`
  - Trocar `from src.message_formatter import MessageFormatter` → `from core import MessageFormatter`
  - Importar constantes de `core`: `from core import MAX_HISTORY, MAX_ALERT_MESSAGE_LEN, ...`

- [ ] Atualizar `integrations/standalone-meshtastic/src/state_manager.py`
  - Importar `State, Alert` do `core`
  - Usar `State.from_dict()` para carregar
  - Usar `state.to_dict()` para salvar

- [ ] Atualizar `integrations/standalone-meshtastic/src/__init__.py`
  - Importar de `core` ao invés de módulos locais

- [ ] Deletar arquivos movidos:
  - ❌ `integrations/standalone-meshtastic/src/rss_parser.py`
  - ❌ `integrations/standalone-meshtastic/src/message_formatter.py`

**Tempo estimado:** 45 minutos

---

### Fase 4: Refatorar Home Assistant

- [ ] Adicionar imports em `integrations/home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py`
  ```python
  from core import RSSParser, MessageFormatter, State, Alert
  from core import LEVEL_PREFIX_MAP, MAX_HISTORY, MAX_ALERT_MESSAGE_LEN, ...
  ```

- [ ] Remover métodos duplicados:
  - ❌ `strip_html()`
  - ❌ `normalize_dash()`
  - ❌ `normalize_level_prefix()`
  - ❌ `compact_alert_text()`
  - ❌ `normalize_text()`
  - ❌ `sanitize_state_alerts()`
  - ❌ `parse_feed()`
  - ❌ `fetch_feed()`
  - ❌ `parse_update_interval_minutes()`

- [ ] Criar instâncias de `RSSParser` e `MessageFormatter`
  ```python
  self.parser = RSSParser()
  self.formatter = MessageFormatter()
  ```

- [ ] Usar métodos de `self.formatter` e `self.parser` nos lugares apropriados

- [ ] Testar que funcionalidade HA mantém 100% de compatibilidade

**Tempo estimado:** 60 minutos

---

### Fase 5: Criar Testes Centralizados

- [ ] Criar diretório `tests/`
- [ ] Criar `tests/__init__.py`
- [ ] Criar `tests/test_constants.py`
  - Validar que todas constantes existem
  - Validar tipos (int, str, dict)
  - Validar valores esperados

- [ ] Criar `tests/test_models.py`
  - Testar `Alert.from_dict()` e `to_dict()`
  - Testar `State.from_dict()` e `to_dict()`
  - Testar que serialização é reversível

- [ ] Criar `tests/test_rss_parser.py`
  - Testar parsing de XML válido
  - Testar extraction de campos
  - Testar handle de XML malformado

- [ ] Criar `tests/test_message_formatter.py`
  - Testar compactação de prefixos
  - Testar normalizações
  - Testar truncamento de mensagens
  - Testar build_alert_messages

- [ ] Criar `tests/fixtures/sample_feed.xml`
  - XML real (ou simulado) do feed da Defesa Civil

**Tempo estimado:** 90 minutos

---

### Fase 6: Atualizar Documentação

- [ ] Atualizar `README.md` na raiz
  - Documentar arquitetura de `core/`
  - Explicar como adicionar nova integração

- [ ] Atualizar `integrations/home-assistant-appdaemon/README.md`
  - Mencionar que usa `core/`
  - Não precisa mencionar parser/formatter (está em core)

- [ ] Atualizar `integrations/standalone-meshtastic/README.md`
  - Mencionar que usa `core/`
  - Remover informações de parser/formatter (está em core)

- [ ] Criar `docs/ARCHITECTURE.md` (NOVO)
  - Explicar estrutura geral
  - Mostrar fluxo entre core e integrações
  - Diagramas de dependência

**Tempo estimado:** 45 minutos

---

## ✅ Checklist de Conclusão

### Código
- [ ] `core/` package criado e testado
- [ ] Standalone importa de `core/`
- [ ] Home Assistant importa de `core/`
- [ ] Testes passam (100% dos cenários)
- [ ] Não há imports circulares

### Documentação
- [ ] README atualizado
- [ ] Exemplos funcionam
- [ ] Diagrama de arquitetura adicionado

### Validação
- [ ] HA continua funcionando igual
- [ ] Standalone continua funcionando igual
- [ ] CI/CD passa (se configurado)
- [ ] Sem regressões em funcionalidade

### Git
- [ ] Branch de feature criado
- [ ] Commits organizados por fase
- [ ] Pull request criado
- [ ] Aprovado e merged

---

## 📊 Impacto Esperado

### Linhas de Código

**Antes:**
```
standalone-meshtastic/src/: 350 linhas (rss_parser + formatter)
home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py: 500 linhas
TOTAL: 850 linhas de lógica principal
```

**Depois:**
```
core/: 350 linhas (centralizado)
standalone-meshtastic/src/: 200 linhas (sem rss_parser/formatter)
home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py: 200 linhas
tests/: 300+ linhas (cobertura nova)
TOTAL: 1050 linhas (mas 200 são testes novos)
REDUÇÃO DE DUPLICAÇÃO: -650 linhas ✓
```

### Manutenção

| Métrica | Impacto |
|---------|---------|
| **Bug fixes** | 1 lugar → ambas integrações |
| **Novos features** | 1 lugar → ambas integrações |
| **Testes** | Centralizados, cobertura melhor |
| **Onboarding** | Novo dev entende core primeiro |

---

## 🚨 Riscos e Mitigações

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Regressão em HA | Alta | Testes abrangentes antes de merge |
| Regressão em Standalone | Alta | Testes abrangentes antes de merge |
| Imports circulares | Média | Code review atento a import paths |
| Breaking changes | Média | Versionamento semântico do `core` |
| Dificuldade em rollback | Baixa | Commits pequenos por fase |

---

## 📝 Notas

- Este plano é não-linear: fases podem ser ajustadas durante implementação
- Testar incrementalmente: após cada fase principal
- Se algo quebrar, rollback é possível via git
- Manter branch separado durante todo processo

---

## 👤 Próximos Passos

1. **Revisão:** Validar este plano com stakeholders
2. **Aprovação:** Confirmar que segue com implementação
3. **Implementação:** Seguir fases em ordem
4. **Review:** Code review antes de merge
5. **Merge:** Fazer merge de volta para `main`

---

**Última atualização:** 2026-07-01  
**Status:** ⏳ Aguardando aprovação para implementação
