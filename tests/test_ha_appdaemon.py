"""Testes para a integração Home Assistant AppDaemon."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Mockar módulo appdaemon antes de importar o app
# ---------------------------------------------------------------------------
_hass_mock = MagicMock()
_hass_module = types.ModuleType("appdaemon")
_hass_plugins = types.ModuleType("appdaemon.plugins")
_hass_hass = types.ModuleType("appdaemon.plugins.hass")
_hass_hassapi = types.ModuleType("appdaemon.plugins.hass.hassapi")


class _FakeHass:
    """Base mínima que imita hass.Hass para os testes."""

    def __init__(self, args=None):
        self.args = args or {}

    def log(self, msg, level="INFO"):
        pass

    def error(self, msg):
        pass

    def run_in(self, callback, delay, **kwargs):
        pass

    def listen_event(self, callback, event_type):
        pass

    def call_service(self, service, **kwargs):
        pass


_hass_hassapi.Hass = _FakeHass
_hass_hass.hassapi = _hass_hassapi
_hass_plugins.hass = _hass_hass
_hass_module.plugins = _hass_plugins

for mod_name, mod in [
    ("appdaemon", _hass_module),
    ("appdaemon.plugins", _hass_plugins),
    ("appdaemon.plugins.hass", _hass_hass),
    ("appdaemon.plugins.hass.hassapi", _hass_hassapi),
]:
    sys.modules[mod_name] = mod

# ---------------------------------------------------------------------------
# Agora podemos importar o app
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).parent.parent / "integrations" / "home-assistant-appdaemon" / "apps"
sys.path.insert(0, str(APP_DIR))

from defesa_civil_sc_alertas import DefesaCivilSCAlertas
from core import Alert, State, MAX_HISTORY, MAX_ALERTS_REPLY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert_dict(guid, title="ALERTA - Genérico", content="Alerta genérico.", link=None):
    return {
        "guid": guid,
        "title": title,
        "content": content,
        "link": link or f"http://example.com/{guid}",
        "pub_date": "Mon, 01 Jan 2024 12:00:00 GMT",
        "seen_at": "2024-01-01T12:00:00",
    }


def _build_app(args=None, state=None):
    """Constrói uma instância da app com estado e args mockados."""
    default_args = {
        "notify_entity": "notify.mesh_channel_test",
        "gateway_node_id": 12345,
    }
    if args:
        default_args.update(args)

    app = DefesaCivilSCAlertas(args=default_args)

    with patch.object(app, "_load_state", return_value=state or State()):
        with patch.object(app, "_save_state"):
            with patch.object(app, "listen_event"):
                with patch.object(app, "run_in"):
                    app.initialize()

    app._save_state = MagicMock()
    app.send_channel_alert = MagicMock()
    app.send_direct_message = MagicMock()
    app.send_direct_alert = MagicMock()
    return app


# ---------------------------------------------------------------------------
# Testes: filtro regional no check_feed
# ---------------------------------------------------------------------------

class TestCheckFeedRegionFilter:
    def _feed_items(self):
        return [
            _make_alert_dict("g1", title="ALERTA - Temporal em Chapeco",
                             content="Alerta para Oeste Catarinense."),
            _make_alert_dict("g2", title="ALERTA - Temporal em Florianopolis",
                             content="Alerta para Grande Florianopolis."),
        ]

    def test_alerta_fora_da_regiao_e_ignorado(self):
        """Alertas fora da região configurada devem ser registrados como ignorados."""
        state = State()
        state.sent_guids = ["seed"]
        state.ignored_guids = []

        app = _build_app(
            args={
                "region_filter": {
                    "enabled": True,
                    "mode": "both",
                    "mesorregioes": ["Grande Florianópolis"],
                    "municipios": [],
                }
            },
            state=state,
        )
        app.state = state

        with patch.object(app.rss_parser, "parse_and_fetch",
                          return_value=(self._feed_items(), None, 1, 15)):
            app.check_feed({})

        assert "g1" in app.state.ignored_guids
        assert "g2" not in app.state.ignored_guids

    def test_alerta_dentro_da_regiao_e_enviado(self):
        """Alertas dentro da região configurada devem ser enviados."""
        state = State()
        state.sent_guids = ["seed"]
        state.ignored_guids = []

        app = _build_app(
            args={
                "region_filter": {
                    "enabled": True,
                    "mode": "both",
                    "mesorregioes": ["Grande Florianópolis"],
                    "municipios": [],
                }
            },
            state=state,
        )
        app.state = state

        with patch.object(app.rss_parser, "parse_and_fetch",
                          return_value=(self._feed_items(), None, 1, 15)):
            app.check_feed({})

        assert app.send_channel_alert.called
        sent_guids = [c.args[0].guid for c in app.send_channel_alert.call_args_list]
        assert "g2" in sent_guids
        assert "g1" not in sent_guids

    def test_sem_filtro_envia_todos(self):
        """Sem filtro regional, todos os alertas devem ser enviados."""
        state = State()
        state.sent_guids = ["seed"]

        app = _build_app(state=state)
        app.state = state

        with patch.object(app.rss_parser, "parse_and_fetch",
                          return_value=(self._feed_items(), None, 1, 15)):
            app.check_feed({})

        assert app.send_channel_alert.call_count == 2
        sent_guids = [c.args[0].guid for c in app.send_channel_alert.call_args_list]
        assert "g1" in sent_guids
        assert "g2" in sent_guids

    def test_guid_ignorado_nao_e_reenviado(self):
        """GUID já ignorado não deve ser processado novamente."""
        state = State()
        state.sent_guids = ["seed"]
        state.ignored_guids = ["g1"]

        app = _build_app(state=state)
        app.state = state

        with patch.object(app.rss_parser, "parse_and_fetch",
                          return_value=(self._feed_items(), None, 1, 15)):
            app.check_feed({})

        sent_guids = [c.args[0].guid for c in app.send_channel_alert.call_args_list]
        assert "g1" not in sent_guids


# ---------------------------------------------------------------------------
# Testes: trigger_word configurável
# ---------------------------------------------------------------------------

class TestTriggerWord:
    def _make_event_payload(self, message, sender=99, gateway=10, to_node=12345):
        return {
            "data": {
                "message": message,
                "from": sender,
                "gateway": gateway,
                "to": {"node": to_node, "channel": None},
            }
        }

    def test_trigger_word_padrao_responde(self):
        """Palavra-gatilho padrão 'ALERTAS' deve acionar resposta."""
        state = State(alerts=[Alert.from_dict(_make_alert_dict("g1"))])
        app = _build_app(state=state)
        app.state = state

        app.on_meshtastic_message(
            "meshtastic_api_text_message",
            self._make_event_payload("alertas"),
            {},
        )

        assert app.send_direct_alert.called or app.send_direct_message.called

    def test_trigger_word_personalizada(self):
        """Trigger word configurada deve acionar resposta."""
        state = State(alerts=[Alert.from_dict(_make_alert_dict("g1"))])
        app = _build_app(args={"trigger_word": "DEFESA"}, state=state)
        app.state = state

        app.on_meshtastic_message(
            "meshtastic_api_text_message",
            self._make_event_payload("Defesa Civil"),
            {},
        )

        assert app.send_direct_alert.called or app.send_direct_message.called

    def test_palavra_errada_nao_responde(self):
        """Mensagem sem trigger word não deve acionar resposta."""
        state = State(alerts=[Alert.from_dict(_make_alert_dict("g1"))])
        app = _build_app(state=state)
        app.state = state

        app.on_meshtastic_message(
            "meshtastic_api_text_message",
            self._make_event_payload("oi tudo bem"),
            {},
        )

        app.send_direct_alert.assert_not_called()
        app.send_direct_message.assert_not_called()

    def test_trigger_por_contem_nao_exato(self):
        """Trigger word deve fazer match por 'contém', não igualdade."""
        state = State(alerts=[Alert.from_dict(_make_alert_dict("g1"))])
        app = _build_app(state=state)
        app.state = state

        app.on_meshtastic_message(
            "meshtastic_api_text_message",
            self._make_event_payload("quero os ALERTAS de hoje"),
            {},
        )

        assert app.send_direct_alert.called or app.send_direct_message.called


# ---------------------------------------------------------------------------
# Testes: filtro regional na resposta a DM
# ---------------------------------------------------------------------------

class TestDmRegionFilter:
    def _make_event_payload(self, message="alertas", sender=99, gateway=10, to_node=12345):
        return {
            "data": {
                "message": message,
                "from": sender,
                "gateway": gateway,
                "to": {"node": to_node, "channel": None},
            }
        }

    def test_dm_aplica_filtro_regional(self):
        """Resposta a DM deve filtrar alertas fora da região configurada."""
        alert_fora = Alert.from_dict(
            _make_alert_dict("g1", title="ALERTA - Temporal em Chapeco",
                             content="Alerta para Oeste Catarinense.")
        )
        alert_dentro = Alert.from_dict(
            _make_alert_dict("g2", title="ALERTA - Temporal em Florianopolis",
                             content="Alerta para Grande Florianopolis.")
        )
        state = State(alerts=[alert_fora, alert_dentro])

        app = _build_app(
            args={
                "region_filter": {
                    "enabled": True,
                    "mode": "both",
                    "mesorregioes": ["Grande Florianópolis"],
                    "municipios": [],
                }
            },
            state=state,
        )
        app.state = state

        app.on_meshtastic_message(
            "meshtastic_api_text_message",
            self._make_event_payload(),
            {},
        )

        assert app.send_direct_alert.call_count == 1
        sent_alert = app.send_direct_alert.call_args[1]["alert"]
        assert sent_alert.guid == "g2"

    def test_dm_sem_alertas_manda_mensagem_vazia(self):
        """Quando sem alertas (ou tudo filtrado), envia mensagem informativa."""
        state = State(alerts=[
            Alert.from_dict(
                _make_alert_dict("g1", title="ALERTA - Temporal em Chapeco",
                                 content="Alerta para Oeste Catarinense.")
            )
        ])
        app = _build_app(
            args={
                "region_filter": {
                    "enabled": True,
                    "mode": "both",
                    "mesorregioes": ["Grande Florianópolis"],
                    "municipios": [],
                }
            },
            state=state,
        )
        app.state = state

        app.on_meshtastic_message(
            "meshtastic_api_text_message",
            self._make_event_payload(),
            {},
        )

        app.send_direct_alert.assert_not_called()
        app.send_direct_message.assert_called_once()
        text = app.send_direct_message.call_args[0][0].get("text", "")
        assert "Nenhum alerta" in text


# ---------------------------------------------------------------------------
# Testes: defaults preservam comportamento original
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_max_history_default(self):
        app = _build_app()
        assert app.max_history == MAX_HISTORY

    def test_max_alerts_reply_default(self):
        app = _build_app()
        assert app.max_alerts_reply == MAX_ALERTS_REPLY

    def test_trigger_word_default(self):
        app = _build_app()
        assert app.trigger_word == "ALERTAS"

    def test_region_filter_desabilitado_por_padrao(self):
        app = _build_app()
        assert not app.region_filter.enabled
