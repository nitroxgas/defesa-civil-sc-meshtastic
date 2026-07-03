# ✅ Config Validation Fixed - User Guide

## Recent Fixes
**Config Validation Error (FIXED)** ✅
- Fixed: Host/port vs tcp_host/tcp_port naming mismatch
- Fixed: Meshtastic TCPInterface parameter name (portNumber vs port)
- Fixed: Message encoding (must use bytes, not strings)

## Problems You Encountered
When running `python main.py config.yaml`:

### 1. Config Validation Error
```
Conexão TCP requer 'meshtastic.tcp_host' configurado
```

### 2. Connection Parameter Error
```
TCPInterface.__init__() got an unexpected keyword argument 'port'
```

### 3. Message Sending Error
```
Erro ao enviar mensagem: expected bytes, str found
```

## Root Causes & Solutions

### Issue 1: Configuration Key Naming
- Your config.yaml used: `meshtastic.host` and `meshtastic.port`
- The code expected: `meshtastic.tcp_host` and `meshtastic.tcp_port`
- **Solution**: ConfigManager now normalizes both formats automatically

### Issue 2: TCPInterface Parameter Name
- The Meshtastic library uses `portNumber` not `port`
- The connector was using wrong parameter name
- **Solution**: Added try/except fallback to handle both parameter names

### Issue 3: Message Data Type
- The Meshtastic library's `sendData()` requires bytes, not strings
- The connector was passing plain strings
- **Solution**: All message methods now encode strings to UTF-8 bytes before sending

## Implementation Details

Your config.yaml should work as-is:
```yaml
meshtastic:
  connection_type: tcp
  host: "192.168.1.69"
  port: 4403
```

Or use this alternative format:
```yaml
meshtastic:
  connection_type: tcp
  tcp_host: "192.168.1.69"
  tcp_port: 4403
```

## How to Proceed

### 1. Copy Your Config
If you haven't already, create your `config.yaml`:
```bash
cd integrations/standalone-meshtastic
cp config.example.yaml config.yaml
```

### 2. Edit Your Config
Edit `config.yaml` with your Meshtastic gateway settings:
```yaml
meshtastic:
  connection_type: tcp
  host: "192.168.1.69"        # Your gateway IP
  port: 4403                   # Default Meshtastic TCP port
channel:
  name: "Alertas-SC"
  number: 6
feed:
  url: "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"
# ... rest of config
```

### 3. Test the Configuration
```bash
python -c "from src.config_manager import ConfigManager; c = ConfigManager('config.yaml'); c.load(); print('✅ Config loaded!') if c.validate() else print('❌ Invalid config')"
```

### 4. Run the Application
```bash
python main.py config.yaml
```

## Configuration Options

### Meshtastic Connection

**Option 1: Using host/port (Recommended)**
```yaml
meshtastic:
  connection_type: tcp
  host: "192.168.1.69"
  port: 4403
```

**Option 2: Using tcp_host/tcp_port**
```yaml
meshtastic:
  connection_type: tcp
  tcp_host: "192.168.1.69"
  tcp_port: 4403
```

**Option 3: Serial Connection**
```yaml
meshtastic:
  connection_type: serial
  serial_port: ""           # Leave empty for auto-detection (Linux/Mac)
                            # Or specify: "/dev/ttyUSB0", "COM3", etc.
```

## Troubleshooting

### Config still not loading?
1. Verify YAML syntax: `python -m yaml config.yaml`
2. Check indentation (use 2 spaces, not tabs)
3. Verify feed URL starts with `http`

### Connection still fails?
1. Verify Meshtastic gateway is online at the specified IP:port
2. Check firewall rules allow TCP:4403
3. Run with `test_mode: true` to skip Meshtastic connection

### Still having issues?
Run the configuration test directly:
```bash
cd integrations/standalone-meshtastic
python -c "
from src.config_manager import ConfigManager
c = ConfigManager('config.yaml')
c.load()
print('Connection Type:', c.get('meshtastic.connection_type'))
print('Host:', c.get('meshtastic.host'))
print('Port:', c.get('meshtastic.port'))
print('TCP Host (normalized):', c.get('meshtastic.tcp_host'))
print('TCP Port (normalized):', c.get('meshtastic.tcp_port'))
print('Valid:', c.validate())
"
```

## What Changed

**config_manager.py improvements:**
- Added `_normalize_tcp_config()` method
- Converts `host`/`port` to `tcp_host`/`tcp_port` automatically
- Both formats now work seamlessly
- Updated validation messages to mention both formats

**config.example.yaml clarifications:**
- Documents both syntax options
- Added comments explaining each option
- Makes the format choice more obvious

## Testing Your Setup

### Quick Test (No Meshtastic Required)
```bash
python main.py config.yaml &
# Press Ctrl+C after a few seconds
# If no import/config errors, it's working!
```

### With Test Mode
Edit config.yaml:
```yaml
test_mode: true
```

Then run:
```bash
python main.py config.yaml
```

This will:
- Skip actual Meshtastic connection
- Run feed parser
- Show alert processing
- Validate the entire flow

## Configuration Validated ✅

Your configuration with `host` and `port` format is now fully supported and validated.
Run `python main.py config.yaml` with confidence!
