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

## Pré-requisitos

- ✅ Home Assistant funcionando
- ✅ Integração Meshtastic instalada e conectada
- ✅ Canal Meshtastic criado (ex: `Alertas-SC`)
- ✅ Entidade `notify.mesh_channel_*` disponível
- ✅ Add-on AppDaemon instalado
- ✅ Git instalado (para clone do repositório)

## 🚀 Instalação Rápida (Recomendado)

### Linux/Mac

```bash
# 1. Clonar repositório
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic

# 2. Executar script de instalação
bash install-home-assistant.sh
```

O script irá:
- Detectar automaticamente o diretório do AppDaemon
- Copiar o app para `/config/apps/`
- Copiar módulos `core/` para o AppDaemon
- Gerar arquivo `apps.yaml` (exemplo)

### Windows (PowerShell)

```powershell
# 1. Clonar repositório
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic

# 2. Executar script de instalação
powershell -ExecutionPolicy Bypass -File install-home-assistant.ps1
```

## 📋 Instalação Manual

### Passo 1: Pré-requisitos do Home Assistant

Instale o add-on AppDaemon se ainda não tiver:

1. Abra **Home Assistant → Settings → Add-ons**
2. Procure por "AppDaemon"
3. Clique em instalar e ativar

> No Home Assistant OS, os arquivos ficam em:
> `/root/addon_config/<ALGUMACOISA>_appdaemon/`
> 
> Referenciamos como `/config/` nos exemplos a seguir.

### Passo 2: Clonar o Repositório

```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
```

### Passo 3: Copiar Arquivos para AppDaemon

#### 3a. App Principal

Copie o arquivo da integração:

```bash
# Linux/Mac
cp integrations/home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py \
   /config/apps/defesa_civil_sc_alertas.py

# Ou encontre manualmente o caminho e copie
```

#### 3b. Módulos Compartilhados (Core)

**Importante**: A integração precisa acessar os módulos `core/`:

```bash
# Opção 1: Copiar core/ para AppDaemon
cp -r core /config/

# Opção 2: Criar symlink (melhor para atualizações)
ln -s /path/to/defesa-civil-sc-meshtastic/core /config/core
```

**Verificar se está correto**: O app consegue importar os módulos?

```python
import sys
sys.path.insert(0, '/config')
from core import RSSParser, MessageFormatter, State, Alert
```

### Passo 4: Configurar o AppDaemon

Copie e edite o arquivo de configuração:

```bash
cp integrations/home-assistant-appdaemon/config/apps.yaml.example \
   /config/apps.yaml
```

Edite `/config/apps.yaml`:

```yaml
defesa_civil_sc_alertas:
  module: defesa_civil_sc_alertas
  class: DefesaCivilSCAlertas
  notify_entity: notify.mesh_channel_alertas_sc    # ← Sua entidade
  gateway_node_id: 3735928559                       # ← ID do seu gateway
  test_mode: false
```

**Como encontrar seus valores:**

**notify_entity**: No Home Assistant, procure em Settings → Devices & Services → Entities. Procure por "mesh_channel" ou similar.

**gateway_node_id**: No seu gateway Meshtastic:
- Abra a interface Meshtastic Web (`meshtastic.org/client/`)
- Procure por "Node ID" ou "My Info"
- Use o número decimal (não hexadecimal)

### Passo 5: Reiniciar AppDaemon

1. Home Assistant → Settings → Add-ons
2. Clique em AppDaemon
3. Clique em "Restart"

Verifique os logs para erros:

```
Settings → Add-ons → AppDaemon → Logs
```

## 🧪 Testando a Integração

### Modo de Teste

Para enviar um alerta sem esperar por novos alertas:

**Edite `/config/apps.yaml`:**

```yaml
defesa_civil_sc_alertas:
  # ... outras configs ...
  test_mode: true
```

**Reinicie o AppDaemon**. Ele enviará um alerta de teste.

Depois, volte para:

```yaml
test_mode: false
```

### Verificar Logs

```
Home Assistant → Settings → Add-ons → AppDaemon → Logs
```

Procure por:
- `Defesa Civil SC Alertas iniciado`
- `Feed verificado`
- Mensagens de erro

## 📊 Operação

- **Leitura do feed**: A cada hora ou conforme `sy:updatePeriod`/`sy:updateFrequency` do feed RSS
- **Histórico**: Armazena os últimos 10 alertas
- **Deduplicação**: Evita reenviar alertas repetidos usando `guid`
- **Primeira execução**: Carrega histórico sem enviar (evita flood)
- **Resposta DM**: Quando alguém enviar `ALERTAS` por mensagem direta, responde com 3 últimos alertas

## 🔄 Atualizando

Para atualizar a integração com novas versões:

```bash
cd defesa-civil-sc-meshtastic
git pull origin main
cp integrations/home-assistant-appdaemon/apps/defesa_civil_sc_alertas.py /config/apps/
cp -r core /config/  # Ou atualizar se usar symlink
```

Reinicie o AppDaemon.

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: core` | Verifique se `/config/core/` existe com os módulos |
| App não inicia | Procure por `ImportError` nos logs do AppDaemon |
| Mensagens não chegam | Verifique se `notify_entity` está correto em `apps.yaml` |
| Sem alertas | Verifique conexão de internet e URL do feed RSS |

## 📚 Arquivos

```text
integrations/home-assistant-appdaemon/
├── README.md                          # Este arquivo
├── apps/
│   └── defesa_civil_sc_alertas.py    # App AppDaemon (refatorado)
└── config/
    ├── apps.yaml.example             # Configuração (copiar para /config/apps.yaml)
    └── appdaemon.yaml.example        # Configuração AppDaemon (opcional)
```

## 📖 Documentação

- [Arquitetura e Design](../../docs/ARCHITECTURE.md)
- [README Principal](../../README.md)
- [Home Assistant AppDaemon Docs](https://appdaemon.readthedocs.io/)
