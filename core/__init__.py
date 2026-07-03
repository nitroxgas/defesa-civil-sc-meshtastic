"""Módulos compartilhados da integração Defesa Civil SC."""

from .constants import (
    FEED_URL,
    MAX_ALERT_MESSAGE_LEN,
    MAX_LINK_MESSAGE_LEN,
    MAX_HISTORY,
    MAX_ALERTS_REPLY,
    CHANNEL_LINK_DELAY_SECONDS,
    CHANNEL_ALERT_BATCH_DELAY_SECONDS,
    POLL_INTERVAL_DIVISOR,
    DEFAULT_INTERVAL_MINUTES,
    MIN_INTERVAL_MINUTES,
    MAX_INTERVAL_MINUTES,
    DEFAULT_TIMEOUT_SECONDS,
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
    "CHANNEL_LINK_DELAY_SECONDS",
    "CHANNEL_ALERT_BATCH_DELAY_SECONDS",
    "POLL_INTERVAL_DIVISOR",
    "DEFAULT_INTERVAL_MINUTES",
    "MIN_INTERVAL_MINUTES",
    "MAX_INTERVAL_MINUTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "LEVEL_PREFIX_MAP",
    "Alert",
    "State",
    "RSSParser",
    "MessageFormatter",
]
