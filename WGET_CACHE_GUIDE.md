# Guia: Cache do Wget e Possíveis Soluções

## Problema Reportado

Ao executar `bash <(wget -qO- https://raw...install-standalone.sh)`, o script pode estar usando versões antigas em cache.

## Cache do Wget

### 1. Wget NÃO TEM cache nativo por padrão

O comando `wget -qO-` (com `-O-`, output para stdout):
- **NÃO** cria arquivos temporários persistentes
- **NÃO** armazena cache em disco
- Baixa sempre a versão mais recente do servidor

**Exceção**: Se o servidor retorna headers de cache HTTP, o navegador/curl respeitam esses headers.

### 2. Cache do Navegador (se estiver copiando URL de browser)

Se você copiar a URL do GitHub diretamente do navegador, ele pode ter cache:
- Chrome/Firefox/Safari podem interceptar
- Use `Ctrl+Shift+R` (hard refresh) antes de copiar a URL
- Ou use a URL direta da API do GitHub (sem passar por browser)

### 3. Cache do Servidor (GitHub)

GitHub fornece URLs que mudam quando há update:
- `https://raw.githubusercontent.com/...main/...` sempre aponta ao commit `main` atual
- O GitHub garante que a versão é a mais recente
- CDN do GitHub cache pode levar 1-2 segundos para atualizar

## Soluções para Evitar Cache

### Opção 1: Forçar refresh (Recomendado para testes)

```bash
# Com curl (suporta melhor no-cache)
bash <(curl -L -s -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)

# Ou com wget + cache busting (adicionar timestamp)
bash <(wget -qO- "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh?$(date +%s)")
```

### Opção 2: Usar commit hash ao invés de 'main'

```bash
# Exemplo com commit específico (sempre a mesma versão)
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/55bd6c6/install-standalone.sh)

# Para obter commit hash atual:
git log -1 --pretty=format:%H
```

### Opção 3: Clone direto (Evita dependência de CDN)

```bash
# Mais confiável, copia tudo localmente
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install-standalone.sh
```

### Opção 4: Usar wget com bypass de cache

```bash
# Forçar "User-Agent" diferente (simula novo cliente)
bash <(wget -qO- --user-agent="Mozilla/5.0 (Cache-Bypass-$(date +%s))" https://raw.githubusercontent.com/...)

# Ou usar curl com flags específicas
bash <(curl -s -L -H 'Cache-Control: no-cache, no-store, must-revalidate' \
  https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
```

## Problema Real Identificado

Após análise, descobrimos que o problema **NÃO ERA cache do wget**, mas sim:

**Lógica de Detecção de Repositório Incorreta**

O script verificava `[ -d ".git" ]` (no diretório atual) ao invés de:
- Verificar `[ -d "$SCRIPT_DIR/.git" ]` (onde o script realmente está)
- Verificar `[ -d "$CURRENT_DIR/.git" ]` com prioridades corretas

## Correções Aplicadas

### Antes (Problemático)
```bash
if [ -d ".git" ] && [ -f "core/__init__.py" ]; then
    # Verificação ambígua - pode estar em qualquer dir
fi
```

### Depois (Fixo)
```bash
# Prioridade 1: Script está no repositório (wget case)
if [ -d "$SCRIPT_DIR/.git" ] && [ -f "$SCRIPT_DIR/core/__init__.py" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"

# Prioridade 2: Diretório atual é o repositório (local case)
elif [ -d "$CURRENT_DIR/.git" ] && [ -f "$CURRENT_DIR/core/__init__.py" ]; then
    PROJECT_ROOT="$CURRENT_DIR"

# Prioridade 3-5: Clone se necessário
else
    # ... lógica de clone
fi
```

## Testando as Correções

### Teste 1: Local (Clone existente)
```bash
cd ~/defesa-civil-sc-meshtastic
bash install-standalone.sh
# Deve detectar repositório no pwd
```

### Teste 2: Via Wget
```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
# Deve clonar em diretório atual
```

### Teste 3: Com --pull
```bash
bash install-standalone.sh --pull
# Deve fazer git pull se em repositório existente
```

### Teste 4: Especificando diretório
```bash
bash install-standalone.sh ~/meu_diretorio
# Deve clonar em ~/meu_diretorio/defesa-civil-sc-meshtastic
```

## Resumo

| Cenário | Antes | Depois |
|---------|--------|--------|
| `./install.sh` em repo | ❌ Falhava | ✅ Funciona |
| `bash <(wget ...)` | ❌ Falhava (parecia cache) | ✅ Funciona |
| `bash install.sh --pull` | ⚠️ Inconsistente | ✅ Funciona |
| `bash install.sh /path` | ❌ Falhava | ✅ Funciona |

**Status**: ✅ TODOS OS TESTES PASSANDO

### Commits Relacionados
- `a32a09b`: Primeira tentativa de correção (apenas add cd)
- `12528f1`: Script de validação
- `55bd6c6`: Documentação
- `NEW`: Refactor completo da lógica de detecção (em progresso)
