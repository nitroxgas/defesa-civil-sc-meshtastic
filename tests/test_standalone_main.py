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
from core import RegionFilter


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
    app.mesh.send_alert.assert_not_called()
    assert app.mesh.send_to_channel.call_count == 2  # texto + link
    assert "Texto enviado" in caplog.text


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


def test_send_alert_uses_interface_sendAlert_for_channel():
    """Verifica que send_alert usa sendText com Bell (TEXT_MESSAGE_APP) para canal."""
    from meshtastic_connector import MeshtasticConnector

    connector = MeshtasticConnector(connection_type="tcp", tcp_host="127.0.0.1")
    connector.interface = MagicMock()
    connector.interface.sendText = MagicMock(return_value=None)

    assert connector.send_alert("Alerta teste", channel_id=3) is True
    connector.interface.sendText.assert_called_once_with(
        "Alerta teste \a", destinationId="^all", channelIndex=3, wantAck=False
    )


def test_send_alert_uses_interface_sendAlert_for_direct_message():
    """Verifica que send_alert usa sendText com Bell (TEXT_MESSAGE_APP) para DM."""
    from meshtastic_connector import MeshtasticConnector

    connector = MeshtasticConnector(connection_type="tcp", tcp_host="127.0.0.1")
    connector.interface = MagicMock()
    connector.interface.sendText = MagicMock(return_value=None)

    assert connector.send_alert("Alerta teste", channel_id=0, node_id="!abc123") is True
    connector.interface.sendText.assert_called_once_with(
        "Alerta teste \a", destinationId="!abc123", channelIndex=0, wantAck=False
    )


def test_check_feed_respects_region_filter(app, caplog):
    """Verifica que check_feed ignora alertas fora das regiões configuradas."""
    app.running = True
    app.region_filter = RegionFilter(
        {
            "enabled": True,
            "mode": "both",
            "mesorregioes": ["Grande Florianópolis"],
            "municipios": [],
        }
    )
    app.rss_parser.parse_and_fetch = MagicMock(
        return_value=(
            [
                {
                    "guid": "g1",
                    "title": "ALERTA - Temporal em Chapeco",
                    "content": "Alerta para Oeste Catarinense.",
                    "link": "http://example.com/1",
                    "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "seen_at": "2024-01-01T12:00:00",
                },
                {
                    "guid": "g2",
                    "title": "ALERTA - Temporal em Florianopolis",
                    "content": "Alerta para Grande Florianopolis.",
                    "link": "http://example.com/2",
                    "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "seen_at": "2024-01-01T12:00:00",
                },
            ],
            None,
            1,
            15,
        )
    )
    app.mesh.send_alert.return_value = True
    app.mesh.send_to_channel.return_value = True

    with caplog.at_level("INFO"):
        app.check_feed()

    assert app.state_manager.is_guid_ignored("g1")
    assert app.state_manager.is_guid_sent("g2")
    assert app.mesh.send_alert.called
    assert app.mesh.send_to_channel.called
    assert "Alerta ignorado por filtro regional" in caplog.text


def test_check_feed_marks_only_first_message_as_alert(app, caplog):
    """Verifica que, em lote com vários alertas, apenas a primeira mensagem usa send_alert."""
    app.running = True
    app.region_filter = RegionFilter({"enabled": False})
    app.rss_parser.parse_and_fetch = MagicMock(
        return_value=(
            [
                {
                    "guid": "g1",
                    "title": "ALERTA - Temporal em A",
                    "content": "Alerta A.",
                    "link": "http://example.com/1",
                    "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "seen_at": "2024-01-01T12:00:00",
                },
                {
                    "guid": "g2",
                    "title": "ALERTA - Temporal em B",
                    "content": "Alerta B.",
                    "link": "http://example.com/2",
                    "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "seen_at": "2024-01-01T12:00:00",
                },
            ],
            None,
            1,
            15,
        )
    )
    app.mesh.send_alert.return_value = True
    app.mesh.send_to_channel.return_value = True

    with caplog.at_level("INFO"):
        app.check_feed()

    # 1 send_alert (sinal do lote) + 4 send_to_channel (msg+link para cada alerta)
    assert app.mesh.send_alert.call_count == 1
    assert app.mesh.send_to_channel.call_count == 4
    assert app.state_manager.is_guid_sent("g1")
    assert app.state_manager.is_guid_sent("g2")


def test_check_meshtastic_connection_resets_backoff_when_connected(app):
    """Verifica que conexão ativa reseta contador de reconexão."""
    app.mesh.is_connected.return_value = True
    app.reconnect_attempts = 2
    app.reconnect_backoff_seconds = 120

    assert app.check_meshtastic_connection() is True
    assert app.reconnect_attempts == 0
    assert app.reconnect_backoff_seconds == 30


def test_check_meshtastic_connection_returns_false_when_disconnected(app):
    """Verifica que detecta desconexão."""
    app.mesh.is_connected.return_value = False
    assert app.check_meshtastic_connection() is False


def test_reconnect_meshtastic_respects_backoff(app, monkeypatch):
    """Verifica que reconexão respeita intervalo de backoff."""
    app.mesh.is_connected.return_value = False
    app.mesh.connect.return_value = False
    app.reconnect_backoff_seconds = 30
    app.last_reconnect_attempt = 1000.0

    current_time = 1000.0
    monkeypatch.setattr(
        main_module.time, "time", lambda: current_time
    )

    # Antes do backoff, não deve tentar
    assert app.reconnect_meshtastic() is False
    app.mesh.connect.assert_not_called()

    # Depois do backoff, deve tentar
    current_time = 1035.0
    assert app.reconnect_meshtastic() is False
    app.mesh.connect.assert_called_once()


def test_reconnect_meshtastic_doubles_backoff_on_failure(app, monkeypatch):
    """Verifica que backoff dobra após falha."""
    app.mesh.is_connected.return_value = False
    app.mesh.connect.return_value = False
    app.reconnect_backoff_seconds = 30
    app.last_reconnect_attempt = 0.0

    current_time = 1000.0
    monkeypatch.setattr(main_module.time, "time", lambda: current_time)

    app.reconnect_meshtastic()
    assert app.reconnect_backoff_seconds == 60
    current_time += 60

    app.reconnect_meshtastic()
    assert app.reconnect_backoff_seconds == 120
    current_time += 120

    app.reconnect_meshtastic()
    assert app.reconnect_backoff_seconds == 240
    current_time += 240

    app.reconnect_meshtastic()
    assert app.reconnect_backoff_seconds == 300
    current_time += 300

    app.reconnect_meshtastic()
    assert app.reconnect_backoff_seconds == 300


def test_reconnect_meshtastic_reregisters_callback_on_success(app, monkeypatch):
    """Verifica que callback é re-registrado após reconexão bem-sucedida."""
    app.mesh.is_connected.return_value = False
    app.mesh.connect.return_value = True
    app.reconnect_backoff_seconds = 60
    app.reconnect_attempts = 1
    app.last_reconnect_attempt = 0.0

    monkeypatch.setattr(main_module.time, "time", lambda: 1000.0)

    assert app.reconnect_meshtastic() is True
    assert app.reconnect_attempts == 0
    assert app.reconnect_backoff_seconds == 30
    app.mesh.register_receive_callback.assert_called_with(
        app.on_message_received
    )


def test_dm_alerts_request_applies_region_filter(app):
    """Verifica que resposta a DM aplica filtro regional e não usa send_alert."""
    app.running = True
    app.region_filter = RegionFilter(
        {
            "enabled": True,
            "mode": "both",
            "mesorregioes": ["Grande Florianópolis"],
            "municipios": [],
        }
    )
    app.state_manager.add_alert(
        {
            "guid": "g1",
            "title": "ALERTA - Temporal em Chapeco",
            "content": "Alerta para Oeste Catarinense.",
            "link": "http://example.com/1",
            "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
            "seen_at": "2024-01-01T12:00:00",
        }
    )
    app.state_manager.add_alert(
        {
            "guid": "g2",
            "title": "ALERTA - Temporal em Florianopolis",
            "content": "Alerta para Grande Florianopolis.",
            "link": "http://example.com/2",
            "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
            "seen_at": "2024-01-01T12:00:00",
        }
    )

    packet = {"from": 12345, "fromId": "!abc123", "to": 12345}
    app.handle_dm_alerts_request(packet, None)

    alert_calls = app.mesh.send_alert.call_args_list
    dm_calls = app.mesh.send_direct_message.call_args_list
    # Deve enviar apenas 1 alerta (g2) em 2 mensagens normais (conteúdo + link)
    assert len(alert_calls) == 0
    assert len(dm_calls) == 2
    call_text = " ".join(str(c) for c in dm_calls)
    assert "Florianopolis" in call_text
    assert "Link: g2" in call_text
    assert "Chapeco" not in call_text
