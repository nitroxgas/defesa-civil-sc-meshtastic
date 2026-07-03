"""Testes para core.constants."""

import pytest
from core import constants


def test_feed_url():
    """Verifica se FEED_URL está configurado."""
    assert constants.FEED_URL
    assert "defesacivil.sc.gov.br" in constants.FEED_URL


def test_message_lengths():
    """Verifica limites de comprimento de mensagens."""
    assert constants.MAX_ALERT_MESSAGE_LEN == 180
    assert constants.MAX_LINK_MESSAGE_LEN == 180


def test_max_history():
    """Verifica limite de histórico."""
    assert constants.MAX_HISTORY == 10


def test_max_alerts_reply():
    """Verifica limite de alertas por resposta."""
    assert constants.MAX_ALERTS_REPLY == 2


def test_interval_limits():
    """Verifica limites de intervalo."""
    assert constants.DEFAULT_INTERVAL_MINUTES == 15
    assert constants.MIN_INTERVAL_MINUTES == 15
    assert constants.MAX_INTERVAL_MINUTES == 1440


def test_poll_interval_divisor():
    """Verifica divisor da estratégia de polling."""
    assert constants.POLL_INTERVAL_DIVISOR == 4


def test_delays():
    """Verifica delays entre mensagens."""
    assert constants.CHANNEL_LINK_DELAY_SECONDS == 10
    assert constants.CHANNEL_ALERT_BATCH_DELAY_SECONDS == 10


def test_level_prefix_map():
    """Verifica mapeamento de prefixos de nível."""
    assert constants.LEVEL_PREFIX_MAP["ALERTA"] == "AL:"
    assert constants.LEVEL_PREFIX_MAP["ATENÇÃO"] == "AT:"
    assert constants.LEVEL_PREFIX_MAP["OBSERVAÇÃO"] == "OBS:"
