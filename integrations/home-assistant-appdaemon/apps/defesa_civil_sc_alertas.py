import appdaemon.plugins.hass.hassapi as hass
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Configurar path para imports de core
# Este arquivo pode estar em:
#   - defesa-civil-sc-meshtastic/integrations/home-assistant-appdaemon/apps/ (desenvolvimento)
#   - <AppDaemon>/config/apps/ (instalado)
# Core pode estar em:
#   - defesa-civil-sc-meshtastic/core/ (desenvolvimento)
#   - <AppDaemon>/config/core/ (instalado)

def _find_project_root():
    app_file = Path(__file__).resolve()
    candidates = [
        app_file.parent.parent.parent.parent,  # desenvolvimento: 4 níveis acima
        app_file.parent.parent,                # instalado: 2 níveis acima (apps -> config)
    ]
    for candidate in candidates:
        if (candidate / "core" / "__init__.py").exists():
            return candidate
    # Fallback para desenvolvimento se nenhum encontrado
    return candidates[0]

PROJECT_ROOT = _find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Imports de core
from core import (
    RSSParser,
    MessageFormatter,
    State,
    Alert,
    FEED_URL,
    MAX_HISTORY,
    MAX_ALERTS_REPLY,
    CHANNEL_LINK_DELAY_SECONDS,
    CHANNEL_ALERT_BATCH_DELAY_SECONDS,
    DEFAULT_INTERVAL_MINUTES,
    LEVEL_PREFIX_MAP,
)


class DefesaCivilSCAlertas(hass.Hass):
    """
    Integração Home Assistant AppDaemon para alertas da Defesa Civil SC via Meshtastic.
    Refatorado para usar módulos compartilhados de core/.
    """
    
    # AJUSTE PARA SUA INSTALAÇÃO: caminho do arquivo JSON para armazenar histórico local de alertas.
    STORAGE_FILE = "/config/apps/defesa_civil_sc_alertas_state.json"

    def initialize(self):
        """Inicializa a integração."""
        self.notify_entity = self.args.get("notify_entity")
        self.gateway_node_id = self.args.get("gateway_node_id")
        self.test_mode = str(self.args.get("test_mode", "false")).lower() == "true"

        if not self.notify_entity:
            self.error("Configure notify_entity em apps.yaml. Ex: notify.mesh_channel_alertas_sc")
            return

        # Inicializar parsers e formatador
        self.rss_parser = RSSParser()
        self.formatter = MessageFormatter()
        
        # Carregar estado
        self.state = self._load_state()

        # Sanitizar alertas antigos se necessário
        if self._sanitize_state_alerts():
            self._save_state()
            self.log("Histórico local normalizado: prefixos AL/AT/OBS corrigidos no JSON.")

        self.listen_event(
            self.on_meshtastic_message,
            "meshtastic_api_text_message"
        )

        self.log("Defesa Civil SC Alertas iniciado.")
        self.log(f"Destino de envio para canal: {self.notify_entity}")
        self.log(f"Modo de teste: {self.test_mode}")

        if self.test_mode:
            self.run_in(self.send_test_alert, 5)
        else:
            self.run_in(self.check_feed, 5)

    def _load_state(self) -> State:
        """Carrega estado do arquivo JSON."""
        if not os.path.exists(self.STORAGE_FILE):
            return State()

        try:
            with open(self.STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return State.from_dict(data)
        except Exception as e:
            self.error(f"Erro lendo state file: {e}")
            return State()

    def _save_state(self) -> None:
        """Salva estado em arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.STORAGE_FILE), exist_ok=True)
            with open(self.STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.error(f"Erro salvando state file: {e}")

    def _sanitize_state_alerts(self) -> bool:
        """
        Corrige dados já persistidos no STORAGE_FILE.
        Sem isso, o modo de teste e a resposta por DM podem continuar usando
        content/title antigos com "ALERTA -", "ATENÇÃO -" ou "OBSERVAÇÃO -".
        """
        changed = False

        for alert in self.state.alerts:
            old_title = alert.title
            old_content = alert.content

            alert.title = self.formatter.normalize_text(old_title, max_len=120)
            alert.content = self.formatter.normalize_text(old_content, max_len=220)

            if alert.title != old_title or alert.content != old_content:
                changed = True

        return changed

    def send_test_alert(self, kwargs):
        """
        Modo de teste: envia o alerta mais recente armazenado no JSON.
        Se não houver JSON/histórico, busca o feed, salva histórico e envia o item mais recente.
        """
        try:
            if not self.state.alerts:
                self.log("Modo de teste: nenhum alerta salvo. Buscando feed para popular histórico.")
                
                feed_alerts, update_period, update_frequency, interval_minutes = self.rss_parser.parse_and_fetch()

                self.state.update_period = update_period
                self.state.update_frequency = update_frequency
                self._update_local_history(feed_alerts)
                self.state.sent_guids = [a.guid for a in feed_alerts[:MAX_HISTORY]]
                self._save_state()

            if not self.state.alerts:
                self.error("Modo de teste: nenhum alerta disponível para envio.")
                return

            alert = self.state.alerts[0]
            self.log(f"Modo de teste: enviando alerta mais recente: {alert.guid}")
            self.send_channel_alert(alert, delay_seconds=0)

        except Exception as e:
            self.error(f"Erro no modo de teste: {e}")

    def send_channel_alert(self, alert: Alert, delay_seconds=0):
        """Envia alerta para canal via Meshtastic."""
        msg1, msg2 = self.formatter.build_alert_messages(alert.to_dict())

        self.run_in(
            self.send_channel_message,
            delay_seconds,
            message=msg1,
            guid=alert.guid
        )

        self.run_in(
            self.send_channel_message,
            delay_seconds + CHANNEL_LINK_DELAY_SECONDS,
            message=msg2,
            guid=alert.guid
        )

    def send_channel_message(self, kwargs):
        """Envia mensagem para o canal Meshtastic."""
        message = kwargs.get("message")
        guid = kwargs.get("guid")

        if not message:
            return

        self.log(f"Enviando mensagem via {self.notify_entity}: {guid} | {message}")

        self.call_service(
            "notify/send_message",
            entity_id=self.notify_entity,
            message=message
        )

    def send_direct_alert(self, gateway, destination_node, alert: Alert, delay_seconds=0):
        """Envia alerta via DM direto para um node."""
        msg1, msg2 = self.formatter.build_alert_messages(alert.to_dict())

        self.run_in(
            self.send_direct_message,
            delay_seconds,
            gateway=gateway,
            destination_node=destination_node,
            text=msg1
        )

        self.run_in(
            self.send_direct_message,
            delay_seconds + CHANNEL_LINK_DELAY_SECONDS,
            gateway=gateway,
            destination_node=destination_node,
            text=msg2
        )

    def send_direct_message(self, kwargs):
        """Envia DM via Meshtastic."""
        gateway = kwargs.get("gateway")
        destination_node = kwargs.get("destination_node")
        text = kwargs.get("text")

        if gateway is None or destination_node is None or not text:
            self.error(
                f"Não foi possível enviar DM. "
                f"gateway={gateway}, destination_node={destination_node}, text={text}"
            )
            return

        self.log(f"Enviando DM para node {destination_node}: {text}")

        self.call_service(
            "meshtastic/send_text",
            ack=False,
            **{
                "from": gateway,
                "to": destination_node,
                "text": text
            }
        )

    def _update_local_history(self, feed_alerts: list):
        """Atualiza histórico local com novos alertas do feed."""
        # Manter existentes
        current_by_guid = {a.guid: a for a in self.state.alerts if a.guid}

        # Adicionar novos
        for alert_dict in feed_alerts:
            alert = Alert.from_dict(alert_dict)
            current_by_guid[alert.guid] = alert

        # Ordenar por data publicação (mais recentes primeiro)
        alerts = list(current_by_guid.values())
        alerts.sort(
            key=lambda a: a.pub_date or a.seen_at or "",
            reverse=True
        )

        # Manter apenas os últimos N
        self.state.alerts = alerts[:MAX_HISTORY]

    def check_feed(self, kwargs):
        """Verifica o feed da Defesa Civil SC em intervalo configurado."""
        next_interval = DEFAULT_INTERVAL_MINUTES

        try:
            feed_alerts, update_period, update_frequency, interval_minutes = self.rss_parser.parse_and_fetch()
            next_interval = interval_minutes

            old_period = self.state.update_period
            old_frequency = self.state.update_frequency

            if old_period != update_period or old_frequency != update_frequency:
                self.log(
                    f"Intervalo do feed alterado: "
                    f"{old_period}/{old_frequency} -> {update_period}/{update_frequency}. "
                    f"Próxima leitura em {next_interval} min."
                )

            self.state.update_period = update_period
            self.state.update_frequency = update_frequency

            self._update_local_history(feed_alerts)

            if not self.state.sent_guids:
                self.state.sent_guids = [a.guid for a in feed_alerts[:MAX_HISTORY] if a.guid]
                self._save_state()

                self.log(
                    f"Primeira execução: {len(feed_alerts)} alertas armazenados como conhecidos. "
                    f"Nenhum envio inicial realizado para evitar flood."
                )
                return

            new_alerts = [
                alert for alert in reversed(feed_alerts)
                if alert["guid"] not in self.state.sent_guids
            ]

            delay = 0

            for alert_dict in new_alerts:
                alert = Alert.from_dict(alert_dict)
                self.send_channel_alert(alert, delay_seconds=delay)

                self.state.sent_guids.append(alert_dict["guid"])
                self.state.sent_guids = self.state.sent_guids[-MAX_HISTORY:]
                self._save_state()

                delay += CHANNEL_ALERT_BATCH_DELAY_SECONDS

            self.log(
                f"Feed verificado. Itens: {len(feed_alerts)}. "
                f"Novos: {len(new_alerts)}. "
                f"Próxima leitura: {next_interval} min."
            )

        except Exception as e:
            self.error(f"Erro verificando feed Defesa Civil SC: {e}")

        finally:
            self.run_in(self.check_feed, next_interval * 60)

    def on_meshtastic_message(self, event_name, data, kwargs):
        """Responde a mensagens DM de usuários pedindo alertas."""
        try:
            payload = data.get("data", {})

            message = payload.get("message", "")
            sender = payload.get("from")
            gateway = payload.get("gateway")

            to_data = payload.get("to", {})
            to_node = to_data.get("node")
            to_channel = to_data.get("channel")

            if not message:
                return

            normalized = message.strip().upper()

            if normalized != "ALERTAS":
                return

            # Ignorar se parece ter vindo de canal
            if to_channel is not None and to_node is None:
                self.log("Mensagem ALERTAS ignorada porque parece ter vindo de canal, não DM.")
                return

            # Verificar se é para o gateway configurado
            if self.gateway_node_id:
                try:
                    configured_gateway = int(self.gateway_node_id)

                    if to_node != configured_gateway:
                        self.log(
                            f"Mensagem ALERTAS ignorada. "
                            f"Destino {to_node} diferente do gateway configurado {configured_gateway}."
                        )
                        return

                except Exception as e:
                    self.error(f"gateway_node_id inválido em apps.yaml: {self.gateway_node_id}. Erro: {e}")
                    return

            # Enviar últimos alertas
            alerts = self.state.alerts[:MAX_ALERTS_REPLY]

            if not alerts:
                self.send_direct_message({
                    "gateway": gateway,
                    "destination_node": sender,
                    "text": "Nenhum alerta da Defesa Civil SC armazenado."
                })
                return

            self.log(f"Respondendo últimos {len(alerts)} alertas para node {sender}")

            delay = 2

            for alert in alerts:
                self.send_direct_alert(
                    gateway=gateway,
                    destination_node=sender,
                    alert=alert,
                    delay_seconds=delay
                )

                delay += CHANNEL_ALERT_BATCH_DELAY_SECONDS

        except Exception as e:
            self.error(f"Erro processando mensagem Meshtastic: {e}")
