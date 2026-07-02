# 🚀 Guia de Instalação - Defesa Civil SC Meshtastic

Este documento ajuda você a escolher e executar o script de instalação correto.

## 📋 Formas de Instalar

### Opção 1: Clone + Script Local (Recomendado)

Clone o repositório e execute o script localmente:

**Linux/Mac:**
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install-home-assistant.sh      # Ou install-standalone.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
powershell -ExecutionPolicy Bypass -File install-home-assistant.ps1      # Ou install-standalone.ps1
```

**Windows (CMD):**
```batch
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
install-home-assistant.bat
```

### Opção 2: Download + Execução Rápida (Sem Clone Prévio)

Baixe e execute o script direto, ele fará o clone automaticamente:

**Linux/Mac:**
```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.sh)
# Ou para Standalone:
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
# Ou para Standalone:
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.ps1" -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

### Opção 3: Menu Interativo (Linux/Mac)

Escolha qual integração instalar através de um menu:

```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install.sh)
# Ou se já clonou:
cd defesa-civil-sc-meshtastic
bash install.sh
```

## 🎯 Escolha Rápida por Tipo

### Para Home Assistant + AppDaemon

**Linux/Mac:**
```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.sh)
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-home-assistant.ps1' -OutFile install.ps1; .\install.ps1"
```

**Windows (CMD):**
```batch
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
install-home-assistant.bat
```

### Para Standalone Python

**Linux/Mac:**
```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh)
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.ps1' -OutFile install.ps1; .\install.ps1"
```

## 📚 Scripts Disponíveis

| Script | SO | Método | Função |
|--------|----|----|--------|
| `install.sh` | Linux/Mac | wget/local | Menu interativo para escolher integração |
| `install-home-assistant.sh` | Linux/Mac | wget/local | Instalar HA + AppDaemon |
| `install-home-assistant.ps1` | Windows | Invoke-WebRequest/local | Instalar HA + AppDaemon |
| `install-home-assistant.bat` | Windows | local | Instalar HA + AppDaemon |
| `install-standalone.sh` | Linux/Mac | wget/local | Instalar Standalone Python |
| `install-standalone.ps1` | Windows | Invoke-WebRequest/local | Instalar Standalone Python |

## 🔍 Como os Scripts Funcionam

### Detecção Automática

Cada script **automaticamente detecta** se você está:

1. **Dentro do repositório clonado** → Usa a versão local
2. **Executando via wget/Invoke-WebRequest** → Clona o repositório automaticamente

**Vantagem:** Sem duplicação de diretórios! ✅

### Atualizações (--pull)

Se você já clonou e quer atualizar antes de instalar:

**Linux/Mac:**
```bash
cd defesa-civil-sc-meshtastic
bash install-standalone.sh --pull
```

**Windows (PowerShell):**
```powershell
cd defesa-civil-sc-meshtastic
powershell -ExecutionPolicy Bypass -File install-standalone.ps1 -Pull
```

## 🎯 O que cada script faz

### `install-home-assistant.sh` / `.ps1` / `.bat`

✅ Detecta AppDaemon (ou permite digitar caminho)
✅ Copia app para `/config/apps/`
✅ Copia módulos `core/` para AppDaemon
✅ Gera arquivo `apps.yaml` (exemplo)
✅ Fornece instruções finais

**Tempo estimado:** 2-3 minutos

### `install-standalone.sh` / `.ps1`

✅ Cria ambiente virtual Python (`venv`)
✅ Instala dependências (`requirements.txt`)
✅ Cria arquivo `config.yaml` (exemplo)
✅ Cria arquivo `state.json` (exemplo)
✅ Verifica integração com `core/`
✅ Fornece instruções finais

**Tempo estimado:** 5-10 minutos (instalação de dependências)

## 🔍 Verificar Instalação

### Home Assistant

1. Após o script terminar, edite `/config/apps.yaml`:
   - Substitua `notify.mesh_channel_*` por sua entidade real
   - Substitua `gateway_node_id` pelo ID numérico do seu gateway

2. Reinicie o AppDaemon

3. Verifique os logs:
   ```
   Settings → Add-ons → AppDaemon → Logs
   ```

### Standalone

1. Após o script terminar, edite `config.yaml`:
   - Configure `connection_type` (serial ou tcp)
   - Configure `serial_port` ou `tcp_host`

2. Teste a conexão:
   ```bash
   source venv/bin/activate
   python main.py config.yaml
   ```

3. Procure por: `Feed verificado` nos logs

## 🆘 Problemas na Instalação

### AppDaemon não encontrado
Se o script não localizar o AppDaemon:
1. Certifique-se de que AppDaemon está instalado em Home Assistant
2. Execute o script novamente e forneça o caminho manual

### Permissão negada (Linux)
Se receber erro de permissão ao executar via wget:
```bash
bash <(wget -qO- https://raw.githubusercontent.com/nitroxgas/defesa-civil-sc-meshtastic/main/install-standalone.sh) 2>&1
```

Ou execute localmente:
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
chmod +x install-standalone.sh
bash install-standalone.sh
```

### Python não encontrado
Se o script diz que Python 3 não está instalado:
- Linux/Mac: `brew install python3` (ou `apt install python3`)
- Windows: Baixe em `python.org` e adicione ao PATH

### Git não encontrado
Se o script diz que Git não está instalado:
- Linux: `sudo apt install git`
- Mac: `brew install git`
- Windows: Baixe em `git-scm.com`

### Script não funciona via wget (sem permissão/timeout)
Alternativa - Clone e execute localmente:
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install-standalone.sh
```

## 📖 Próximas Etapas

Após a instalação, consulte:

- **Home Assistant**: [integrations/home-assistant-appdaemon/README.md](integrations/home-assistant-appdaemon/README.md)
- **Standalone**: [integrations/standalone-meshtastic/README.md](integrations/standalone-meshtastic/README.md)
- **Arquitetura**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## ❓ Precisa de Ajuda?

- Consulte o `README.md` da sua integração
- Procure por erro no `TROUBLESHOOTING` do README específico
- Verifique [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para entender a estrutura
- Abra uma issue no GitHub

