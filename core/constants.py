"""Constantes compartilhadas entre integrações Defesa Civil SC."""

# URLs
FEED_URL = "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"

# Limites de mensagem (Meshtastic LoRa)
MAX_ALERT_MESSAGE_LEN = 150
MAX_LINK_MESSAGE_LEN = 180

# Histórico
MAX_HISTORY = 10
MAX_ALERTS_REPLY = 3

# Delays entre envios (segundos)
CHANNEL_LINK_DELAY_SECONDS = 20
CHANNEL_ALERT_BATCH_DELAY_SECONDS = 60

# Configuração do feed RSS
DEFAULT_INTERVAL_MINUTES = 60
MIN_INTERVAL_MINUTES = 15
MAX_INTERVAL_MINUTES = 1440
DEFAULT_TIMEOUT_SECONDS = 30

# Prefixos de nível de alerta (compactação)
LEVEL_PREFIX_MAP = {
    "ALERTA": "AL:",
    "ATENÇÃO": "AT:",
    "ATENCAO": "AT:",
    "OBSERVAÇÃO": "OBS:",
    "OBSERVACAO": "OBS:",
}
