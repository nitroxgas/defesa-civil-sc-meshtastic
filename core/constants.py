"""Constantes compartilhadas entre integrações Defesa Civil SC."""

# URLs
FEED_URL = "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"

# Limites de mensagem (Meshtastic LoRa)
MAX_ALERT_MESSAGE_LEN = 180
MAX_LINK_MESSAGE_LEN = 180

# Histórico
MAX_HISTORY = 10
MAX_ALERTS_REPLY = 2

# Delays entre envios (segundos)
CHANNEL_LINK_DELAY_SECONDS = 10
CHANNEL_ALERT_BATCH_DELAY_SECONDS = 10

# Configuração do feed RSS
POLL_INTERVAL_DIVISOR = 4        # polling a cada 1/4 do intervalo sugerido pelo feed
DEFAULT_INTERVAL_MINUTES = 15    # fallback quando o feed não informa período
MIN_INTERVAL_MINUTES = 15        # limite mínimo de intervalo
MAX_INTERVAL_MINUTES = 1440      # limite máximo de intervalo
DEFAULT_TIMEOUT_SECONDS = 30

# Prefixos de nível de alerta (compactação)
LEVEL_PREFIX_MAP = {
    "ALERTA": "AL:",
    "ATENÇÃO": "AT:",
    "ATENCAO": "AT:",
    "OBSERVAÇÃO": "OBS:",
    "OBSERVACAO": "OBS:",
}
