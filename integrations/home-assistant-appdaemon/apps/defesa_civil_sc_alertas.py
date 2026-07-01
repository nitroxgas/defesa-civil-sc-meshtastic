import appdaemon.plugins.hass.hassapi as hass
import xml.etree.ElementTree as ET
import urllib.request
import json
import os
import re
import html
from datetime import datetime


class DefesaCivilSCAlertas(hass.Hass):

    FEED_URL = "https://www.defesacivil.sc.gov.br/categoria/alerta/feed/"
    # AJUSTE PARA SUA INSTALAÇÃO: caminho do arquivo JSON para armazenar histórico local de alertas.
    STORAGE_FILE = "/config/apps/defesa_civil_sc_alertas_state.json"

    DEFAULT_INTERVAL_MINUTES = 60
    MAX_HISTORY = 10
    MAX_ALERTS_REPLY = 3

    MAX_ALERT_MESSAGE_LEN = 150
    MAX_LINK_MESSAGE_LEN = 180

    CHANNEL_LINK_DELAY_SECONDS = 20
    CHANNEL_ALERT_BATCH_DELAY_SECONDS = 60

    LEVEL_PREFIX_MAP = {
        "ALERTA": "AL:",
        "ATENÇÃO": "AT:",
        "ATENCAO": "AT:",
        "OBSERVAÇÃO": "OBS:",
        "OBSERVACAO": "OBS:",
    }

    def initialize(self):
        self.notify_entity = self.args.get("notify_entity")
        self.gateway_node_id = self.args.get("gateway_node_id")
        self.test_mode = str(self.args.get("test_mode", "false")).lower() == "true"

        if not self.notify_entity:
            self.error("Configure notify_entity em apps.yaml. Ex: notify.mesh_channel_alertas_sc")
            return

        self.state_data = self.load_state()

        # Corrige alertas antigos já salvos no JSON, para que o modo de teste
        # e a resposta por DM não reenviem textos com "ALERTA -", "ATENÇÃO -" etc.
        if self.sanitize_state_alerts():
            self.save_state()
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

    def load_state(self):
        if not os.path.exists(self.STORAGE_FILE):
            return {
                "sent_guids": [],
                "alerts": [],
                "update_period": None,
                "update_frequency": None
            }

        try:
            with open(self.STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.error(f"Erro lendo state file: {e}")
            return {
                "sent_guids": [],
                "alerts": [],
                "update_period": None,
                "update_frequency": None
            }

    def save_state(self):
        try:
            with open(self.STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.error(f"Erro salvando state file: {e}")

    def fetch_feed(self):
        req = urllib.request.Request(
            self.FEED_URL,
            headers={
                "User-Agent": "HomeAssistant-Meshtastic-AlertasSC/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()

    def strip_html(self, value):
        if not value:
            return ""

        value = html.unescape(str(value))

        value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"</p\s*>", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"</div\s*>", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"<[^>]+>", "", value)

        value = value.replace("\xa0", " ")
        value = re.sub(r"\n{3,}", "\n\n", value)
        value = re.sub(r"[ \t]+", " ", value)

        return value.strip()

    def normalize_dash(self, value):
        # Normaliza travessão/en dash/em dash/minus para hífen simples.
        return (
            value
            .replace("–", "-")
            .replace("—", "-")
            .replace("−", "-")
        )

    def normalize_level_prefix(self, value):
        """
        Converte prefixos iniciais:
        ALERTA -      -> AL:
        ATENÇÃO -     -> AT:
        OBSERVAÇÃO -  -> OBS:

        Também cobre variações com travessão, dois pontos, espaços e texto já abreviado.
        """
        if not value:
            return ""

        value = self.normalize_dash(value)
        value = re.sub(r"\s+", " ", value).strip()

        # Remove prefixo acidental "ALERTA:" usado pelo script antigo antes do texto do feed.
        value = re.sub(r"^ALERTA:\s+(?=(ALERTA|ATENÇÃO|ATENCAO|OBSERVAÇÃO|OBSERVACAO)\b)", "", value, flags=re.IGNORECASE)

        pattern = r"^(ALERTA|ATENÇÃO|ATENCAO|OBSERVAÇÃO|OBSERVACAO)\s*[-:]\s*"
        match = re.match(pattern, value, flags=re.IGNORECASE)

        if match:
            raw_level = match.group(1).upper()
            prefix = self.LEVEL_PREFIX_MAP.get(raw_level, raw_level + ":")
            value = prefix + " " + value[match.end():].strip()

        # Normaliza abreviações mal espaçadas.
        value = re.sub(r"^(AL|AT|OBS)\s*:\s*", lambda m: m.group(1).upper() + ": ", value, flags=re.IGNORECASE)

        return value.strip()

    def compact_alert_text(self, value):
        """
        Compacta o texto do content:encoded para caber melhor em mensagens Meshtastic.
        """

        value = self.strip_html(value)
        value = self.normalize_dash(value)
        value = re.sub(r"\s+", " ", value).strip()

        # Converte nível antes de qualquer truncamento.
        value = self.normalize_level_prefix(value)

        # Remove texto institucional/repetitivo depois dos telefones.
        value = re.sub(
            r"Ocorrências ligue\s+199\s+ou\s+193\.?.*",
            "199/193.",
            value,
            flags=re.IGNORECASE
        )

        value = re.sub(
            r"A Secretaria.*$",
            "",
            value,
            flags=re.IGNORECASE
        )

        # Compactações específicas dos alertas da Defesa Civil SC.
        replacements = {
            "TEMPESTADE SEVERA": "tempestade severa",
            "TEMPORAIS": "temporais",
            "TEMPORAL": "temporal",

            "RAJADAS DE VENTO": "vento",
            "RAJADA DE VENTO": "vento",
            "ALAGAMENTOS": "alag.",
            "ALAGAMENTO": "alag.",
            "GRANIZO": "granizo",
            "RAIOS": "raios",
            "risco de ENXURRADAS": "enxurr.",
            "risco de enxurradas": "enxurr.",
            "ENXURRADAS": "enxurr.",
            "enxurradas": "enxurr.",

            "nas próximas 3 horas": "Val: 3h",
            "nas próximas três horas": "Val: 3h",
            "nas próximas 2 horas": "Val: 2h",
            "nas próximas duas horas": "Val: 2h",
            "na próxima hora": "Val: 1h",
            "nas próximas horas": "Val: próximas horas",

            "para as regiões da": "Reg:",
            "para as regiões do": "Reg:",
            "para as regiões de": "Reg:",
            "para a região da": "Reg:",
            "para a região do": "Reg:",
            "para os municípios de": "Mun:",
            "para o município de": "Mun:",

            "Grande Florianópolis": "Gde Fpolis",
            "Baixo, Médio e Alto Vale do Itajaí": "Vale Itajaí",
            "Médio e Alto Vale do Itajaí": "Méd/Alto Vale",
            "Alto Vale do Itajaí": "Alto Vale",
            "Baixo Vale do Itajaí": "Baixo Vale",
            "Médio Vale do Itajaí": "Médio Vale",

            "Extremo Oeste": "Ext. Oeste",
            "Meio-Oeste": "Meio-Oeste",
            "Planalto Norte": "Plan. Norte",
            "Planalto Sul": "Plan. Sul",
            "Litoral Sul": "Lit. Sul",
            "Litoral Norte": "Lit. Norte",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        value = value.replace(" com ", " c/ ")

        value = re.sub(r"\s*,\s*", ", ", value)
        value = re.sub(r"\s*\.\s*", ". ", value)
        value = re.sub(r"\s*;\s*", "; ", value)
        value = re.sub(r"\s+", " ", value).strip()

        value = value.replace(" .", ".")
        value = value.replace(" ,", ",")
        value = value.replace("..", ".")

        # Segurança final: caso algum replacement anterior tenha reintroduzido o prefixo longo.
        value = self.normalize_level_prefix(value)

        return value.strip()

    def normalize_text(self, value, max_len=220):
        value = self.compact_alert_text(value)

        if len(value) > max_len:
            return value[: max_len - 3].rstrip() + "..."

        return value

    def sanitize_state_alerts(self):
        """
        Corrige dados já persistidos em STORAGE_FILE.
        Sem isso, o modo de teste e a resposta por DM podem continuar usando
        content/title antigos com "ALERTA -", "ATENÇÃO -" ou "OBSERVAÇÃO -".
        """
        changed = False

        for alert in self.state_data.get("alerts", []):
            for key, max_len in (("title", 120), ("content", 220)):
                old_value = alert.get(key, "")
                new_value = self.normalize_text(old_value, max_len)

                if new_value != old_value:
                    alert[key] = new_value
                    changed = True

        return changed

    def parse_update_interval_minutes(self, root):
        ns = {
            "sy": "http://purl.org/rss/1.0/modules/syndication/"
        }

        period = root.findtext(
            ".//sy:updatePeriod",
            default="",
            namespaces=ns
        ).strip().lower()

        frequency_raw = root.findtext(
            ".//sy:updateFrequency",
            default="1",
            namespaces=ns
        ).strip()

        try:
            frequency = int(frequency_raw)
            if frequency < 1:
                frequency = 1
        except Exception:
            frequency = 1

        if period == "hourly":
            minutes = 60 // frequency
        elif period == "daily":
            minutes = 1440 // frequency
        elif period == "weekly":
            minutes = 10080 // frequency
        elif period == "monthly":
            minutes = 43200 // frequency
        else:
            minutes = self.DEFAULT_INTERVAL_MINUTES

        if minutes < 15:
            minutes = 15

        if minutes > 1440:
            minutes = 1440

        return period or None, frequency, minutes

    def parse_feed(self, xml_bytes):
        ns = {
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/"
        }

        root = ET.fromstring(xml_bytes)

        update_period, update_frequency, interval_minutes = self.parse_update_interval_minutes(root)

        items = []

        for item in root.findall(".//channel/item"):
            title = item.findtext("title", default="").strip()
            guid = item.findtext("guid", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()

            content_encoded = item.findtext(
                "content:encoded",
                default="",
                namespaces=ns
            )

            if not guid:
                guid = link or title

            alert = {
                "guid": guid,
                "title": self.normalize_text(title, 120),
                "content": self.normalize_text(content_encoded, 220),
                "link": guid,
                "pub_date": pub_date,
                "seen_at": datetime.now().isoformat(timespec="seconds")
            }

            items.append(alert)

        return items, update_period, update_frequency, interval_minutes

    def truncate_text(self, value, max_len):
        value = value.strip()

        if len(value) <= max_len:
            return value

        return value[: max_len - 3].rstrip() + "..."

    def build_alert_messages(self, alert):
        content = alert.get("content", "").strip()
        link = alert.get("link", "").strip()

        # Recompacta aqui para corrigir também alertas antigos já salvos no JSON.
        content = self.compact_alert_text(content)

        msg1 = f"DC-SC {content}".strip()
        msg2 = f"Link: {link}".strip()

        msg1 = self.truncate_text(msg1, self.MAX_ALERT_MESSAGE_LEN)
        msg2 = self.truncate_text(msg2, self.MAX_LINK_MESSAGE_LEN)

        return msg1, msg2

    def send_test_alert(self, kwargs):
        """
        Modo de teste:
        envia o alerta mais recente armazenado no JSON.
        Se não houver JSON/histórico, busca o feed, salva histórico e envia o item mais recente.
        """

        try:
            alerts = self.state_data.get("alerts", [])

            if not alerts:
                self.log("Modo de teste: nenhum alerta salvo. Buscando feed para popular histórico.")
                xml_bytes = self.fetch_feed()
                feed_alerts, update_period, update_frequency, interval_minutes = self.parse_feed(xml_bytes)

                self.state_data["update_period"] = update_period
                self.state_data["update_frequency"] = update_frequency
                self.update_local_history(feed_alerts)
                self.state_data["sent_guids"] = [
                    a["guid"] for a in feed_alerts[:self.MAX_HISTORY]
                    if a.get("guid")
                ]
                self.save_state()

                alerts = self.state_data.get("alerts", [])

            if not alerts:
                self.error("Modo de teste: nenhum alerta disponível para envio.")
                return

            alert = alerts[0]

            self.log(f"Modo de teste: enviando alerta mais recente: {alert.get('guid')}")
            self.send_channel_alert(alert, delay_seconds=0)

        except Exception as e:
            self.error(f"Erro no modo de teste: {e}")

    def send_channel_alert(self, alert, delay_seconds=0):
        msg1, msg2 = self.build_alert_messages(alert)

        self.run_in(
            self.send_channel_message,
            delay_seconds,
            message=msg1,
            guid=alert.get("guid")
        )

        self.run_in(
            self.send_channel_message,
            delay_seconds + self.CHANNEL_LINK_DELAY_SECONDS,
            message=msg2,
            guid=alert.get("guid")
        )

    def send_channel_message(self, kwargs):
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

    def send_direct_alert(self, gateway, destination_node, alert, delay_seconds=0):
        msg1, msg2 = self.build_alert_messages(alert)

        self.run_in(
            self.send_direct_message,
            delay_seconds,
            gateway=gateway,
            destination_node=destination_node,
            text=msg1
        )

        self.run_in(
            self.send_direct_message,
            delay_seconds + self.CHANNEL_LINK_DELAY_SECONDS,
            gateway=gateway,
            destination_node=destination_node,
            text=msg2
        )

    def send_direct_message(self, kwargs):
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

    def update_local_history(self, feed_alerts):
        current_by_guid = {
            a["guid"]: a
            for a in self.state_data.get("alerts", [])
            if a.get("guid")
        }

        for alert in feed_alerts:
            current_by_guid[alert["guid"]] = alert

        alerts = list(current_by_guid.values())

        def sort_key(a):
            return a.get("pub_date") or a.get("seen_at") or ""

        alerts.sort(key=sort_key, reverse=True)

        self.state_data["alerts"] = alerts[:self.MAX_HISTORY]

    def check_feed(self, kwargs):
        next_interval = self.DEFAULT_INTERVAL_MINUTES

        try:
            xml_bytes = self.fetch_feed()

            feed_alerts, update_period, update_frequency, interval_minutes = self.parse_feed(xml_bytes)

            next_interval = interval_minutes

            old_period = self.state_data.get("update_period")
            old_frequency = self.state_data.get("update_frequency")

            if old_period != update_period or old_frequency != update_frequency:
                self.log(
                    f"Intervalo do feed alterado: "
                    f"{old_period}/{old_frequency} -> {update_period}/{update_frequency}. "
                    f"Próxima leitura em {next_interval} min."
                )

            self.state_data["update_period"] = update_period
            self.state_data["update_frequency"] = update_frequency

            sent_guids = self.state_data.get("sent_guids", [])

            self.update_local_history(feed_alerts)

            if not sent_guids:
                self.state_data["sent_guids"] = [
                    a["guid"] for a in feed_alerts[:self.MAX_HISTORY]
                    if a.get("guid")
                ]

                self.save_state()

                self.log(
                    f"Primeira execução: {len(feed_alerts)} alertas armazenados como conhecidos. "
                    f"Nenhum envio inicial realizado para evitar flood."
                )

                return

            new_alerts = [
                alert for alert in reversed(feed_alerts)
                if alert["guid"] not in sent_guids
            ]

            delay = 0

            for alert in new_alerts:
                self.send_channel_alert(alert, delay_seconds=delay)

                sent_guids.append(alert["guid"])
                sent_guids = sent_guids[-self.MAX_HISTORY:]

                self.state_data["sent_guids"] = sent_guids
                self.save_state()

                delay += self.CHANNEL_ALERT_BATCH_DELAY_SECONDS

            self.save_state()

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

            if to_channel is not None and to_node is None:
                self.log("Mensagem ALERTAS ignorada porque parece ter vindo de canal, não DM.")
                return

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

            alerts = self.state_data.get("alerts", [])[:self.MAX_ALERTS_REPLY]

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

                delay += self.CHANNEL_ALERT_BATCH_DELAY_SECONDS

        except Exception as e:
            self.error(f"Erro processando mensagem Meshtastic: {e}")
