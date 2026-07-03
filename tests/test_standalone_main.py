"""Testes para o orquestrador standalone."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
import pytest

MAIN_DIR = Path(__file__).parent.parent / "integrations" / "standalone-meshtastic"
sys.path.insert(0, str(MAIN_DIR))
sys.path.insert(0, str(MAIN_DIR / "src"))

with patch("logging.basicConfig"):
    import main as main_module
    from main import DefesaCivilAlertasStandalone


@pytest.fixture(autouse=True)
def fast_delays(monkeypatch):
    """Reduz delays entre envios para tornar os testes rápidos."""
    monkeypatch.setattr(main_module, "CHANNEL_LINK_DELAY_SECONDS", 0.1)
    monkeypatch.setattr(main_module, "CHANNEL_ALERT_BATCH_DELAY_SECONDS", 0.1)


def _write_config(tmp_path: Path, **overrides) -> Path:
    config = {
        "meshtastic": {"connection_type": "tcp", "tcp_host": "127.0.0.1"},
        "channel": {"name": "Alertas-SC", "number": 0},
        "feed": {"url": "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"},
        "state": {"file": str(tmp_path / "state.json"), "max_history": 10},
        "direct_message": {
            "enabled": True,
            "trigger_word": "ALERTAS",
            "max_alerts_reply": 3,
        },
        "test_mode": False,
        "logging": {"level": "DEBUG", "file": None},
    }
    config.update(overrides)
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return config_file


@pytest.fixture
def app(tmp_path):
    config_file = _write_config(tmp_path)
    with patch("logging.basicConfig"):
        instance = DefesaCivilAlertasStandalone(str(config_file))
    instance.mesh = MagicMock()
    instance.mesh.resolve_channel_id.return_value = 0
    instance.mesh.get_my_info.return_value = {"my_node_num": 12345}
    return instance


def test_on_message_received_accepts_text_message_app(app, caplog):
    app.handle_dm_alerts_request = MagicMock()

    packet = {
        "from": 67890,
        "to": 12345,
        "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "ALERTAS"},
    }
    app.on_message_received(packet, None)

    app.handle_dm_alerts_request.assert_called_once()


def test_on_message_received_accepts_int_portnum(app, caplog):
    app.handle_dm_alerts_request = MagicMock()

    packet = {
        "from": 67890,
        "to": 12345,
        "decoded": {"portnum": 1, "payload": b"alertas"},
    }
    app.on_message_received(packet, None)

    app.handle_dm_alerts_request.assert_called_once()


def test_on_message_received_ignores_broadcast(app, caplog):
    app.handle_dm_alerts_request = MagicMock()

    packet = {
        "from": 67890,
        "to": 0xFFFFFFFF,
        "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "ALERTAS"},
    }
    app.on_message_received(packet, None)

    app.handle_dm_alerts_request.assert_not_called()


def test_on_message_received_logs_error_for_dm_without_trigger(app, caplog):
    app.handle_dm_alerts_request = MagicMock()

    packet = {
        "from": 67890,
        "to": 12345,
        "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "OLA"},
    }
    app.on_message_received(packet, None)

    app.handle_dm_alerts_request.assert_not_called()
    assert "não contém comando 'ALERTAS'" in caplog.text


def test_on_message_received_logs_error_for_non_text_portnum(app, caplog):
    app.handle_dm_alerts_request = MagicMock()

    packet = {
        "from": 67890,
        "to": 12345,
        "decoded": {"portnum": "POSITION_APP", "payload": b"..."},
    }
    app.on_message_received(packet, None)

    app.handle_dm_alerts_request.assert_not_called()


def test_send_alert_to_channel_returns_false_when_not_running(app):
    app.running = False
    result = app.send_alert_to_channel({"content": "foo", "link": "http://x"})
    assert result is False


def test_send_alert_to_channel_logs_success(app, caplog):
    app.running = True
    app.mesh.send_to_channel.return_value = True

    with caplog.at_level("DEBUG"):
        result = app.send_alert_to_channel({"content": "ALERTA - Teste", "link": "http://x"})

    assert result is True
    app.mesh.send_to_channel.assert_called()
    assert "Alerta enviado" in caplog.text


def test_meshtastic_connector_subscribes_to_pubsub(tmp_path):
    """Verifica que o conector se inscreve no tópico pubsub de texto."""
    from pubsub import pub
    from meshtastic_connector import MeshtasticConnector

    received = []

    def listener(packet, interface):
        received.append(packet)

    connector = MeshtasticConnector(
        connection_type="tcp",
        tcp_host="127.0.0.1",
        tcp_port=4403,
    )

    # Simular interface já conectada
    connector.interface = MagicMock()
    connector.register_receive_callback(listener)

    # Publicar uma mensagem de texto
    pub.sendMessage(
        "meshtastic.receive.text",
        packet={"from": 1, "to": 2, "decoded": {"text": "alertas"}},
        interface=MagicMock(),
    )

    assert len(received) == 1
    pub.unsubscribe(listener, "meshtastic.receive.text")


def test_resolve_channel_id_returns_index_by_name():
    """Verifica que resolve_channel_id converte nome do canal em índice."""
    from meshtastic_connector import MeshtasticConnector

    connector = MeshtasticConnector(connection_type="tcp", tcp_host="127.0.0.1")
    connector.interface = MagicMock()
    ch1 = MagicMock()
    ch1.settings.name = "Alertas-SC"
    ch1.index = 6
    ch2 = MagicMock()
    ch2.settings.name = "BitDevs"
    ch2.index = 2
    connector.interface._localChannels = [ch1, ch2]

    assert connector.resolve_channel_id("BitDevs") == 2
    assert connector.resolve_channel_id("Alertas-SC") == 6
    assert connector.resolve_channel_id(3) == 3
    assert connector.resolve_channel_id("Inexistente", default=0) == 0


def test_resolve_channel_id_returns_default_when_not_connected():
    """Verifica fallback quando não conectado."""
    from meshtastic_connector import MeshtasticConnector

    connector = MeshtasticConnector(connection_type="tcp", tcp_host="127.0.0.1")
    assert connector.resolve_channel_id("BitDevs", default=5) == 5
