# 🚀 Guia de Instalação - Defesa Civil SC Meshtastic

Este documento ajuda você a escolher e executar o script de instalação correto.

## 📋 Escolha Rápida

### Para Home Assistant + AppDaemon

**Se você é usuário de Home Assistant e quer usar AppDaemon:**

**Linux/Mac:**
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install-home-assistant.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
powershell -ExecutionPolicy Bypass -File install-home-assistant.ps1
```

**Windows (CMD):**
```batch
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
install-home-assistant.bat
```

### Para Standalone Python

**Se você quer uma integração independente sem Home Assistant:**

**Linux/Mac:**
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install-standalone.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
powershell -ExecutionPolicy Bypass -File install-standalone.ps1
```

### Para Ambas as Integrações

**Usar o menu interativo (Linux/Mac):**
```bash
git clone https://github.com/nitroxgas/defesa-civil-sc-meshtastic.git
cd defesa-civil-sc-meshtastic
bash install.sh
```

## 📚 Scripts Disponíveis

| Script | SO | Tipo | Função |
|--------|----|----- |--------|
| `install.sh` | Linux/Mac | Menu | Escolher entre HA ou Standalone |
| `install-home-assistant.sh` | Linux/Mac | Automático | Instalar HA + AppDaemon |
| `install-home-assistant.ps1` | Windows | PowerShell | Instalar HA + AppDaemon |
| `install-home-assistant.bat` | Windows | CMD | Instalar HA + AppDaemon |
| `install-standalone.sh` | Linux/Mac | Automático | Instalar Standalone Python |
| `install-standalone.ps1` | Windows | PowerShell | Instalar Standalone Python |

## 🎯 O que cada script faz?

### `install-home-assistant.sh` / `.ps1` / `.bat`

✅ Clona o repositório (se necessário)
✅ Localiza AppDaemon automaticamente
✅ Copia app para `/config/apps/`
✅ Copia módulos `core/` para AppDaemon
✅ Gera arquivo `apps.yaml` (exemplo)
✅ Fornece instruções finais

**Tempo estimado:** 2-3 minutos

### `install-standalone.sh` / `.ps1`

✅ Clona o repositório (se necessário)
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
Se receber erro de permissão ao executar `.sh`:
```bash
chmod +x install*.sh
bash install-home-assistant.sh
```

### Python não encontrado
Se o script diz que Python 3 não está instalado:
- Linux/Mac: `brew install python3`
- Windows: Baixe em `python.org` e adicione ao PATH

### Git não encontrado
Se o script diz que Git não está instalado:
- Linux: `sudo apt install git`
- Mac: `brew install git`
- Windows: Baixe em `git-scm.com`

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
