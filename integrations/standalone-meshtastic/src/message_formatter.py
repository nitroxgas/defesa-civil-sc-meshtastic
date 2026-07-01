"""
Formatador de mensagens para Meshtastic.
Responsável por compactar e normalizar alertas para caber em mensagens LoRa.
"""

import re
import html
from typing import Tuple


class MessageFormatter:
    """Formata e compacta mensagens de alerta para Meshtastic."""
    
    MAX_ALERT_MESSAGE_LEN = 150
    MAX_LINK_MESSAGE_LEN = 180
    
    # Mapa de prefixos longos para curtos
    LEVEL_PREFIX_MAP = {
        "ALERTA": "AL:",
        "ATENÇÃO": "AT:",
        "ATENCAO": "AT:",
        "OBSERVAÇÃO": "OBS:",
        "OBSERVACAO": "OBS:",
    }
    
    # Compactações de termos frequentes
    TERM_REPLACEMENTS = {
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
    
    @staticmethod
    def strip_html(value: str) -> str:
        """Remove tags HTML e normaliza espaços."""
        if not value:
            return ""
        
        value = html.unescape(str(value))
        
        # Converter quebras HTML em quebras de linha
        value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"</p\s*>", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"</div\s*>", "\n", value, flags=re.IGNORECASE)
        
        # Remover tags HTML
        value = re.sub(r"<[^>]+>", "", value)
        
        # Normalizar espaços
        value = value.replace("\xa0", " ")
        value = re.sub(r"\n{3,}", "\n\n", value)
        value = re.sub(r"[ \t]+", " ", value)
        
        return value.strip()
    
    @staticmethod
    def normalize_dash(value: str) -> str:
        """Normaliza diferentes tipos de travessão para hífen simples."""
        return (
            value
            .replace("–", "-")
            .replace("—", "-")
            .replace("−", "-")
        )
    
    def normalize_level_prefix(self, value: str) -> str:
        """
        Converte prefixos longos para curtos:
        ALERTA - → AL:
        ATENÇÃO - → AT:
        OBSERVAÇÃO - → OBS:
        """
        if not value:
            return ""
        
        value = self.normalize_dash(value)
        value = re.sub(r"\s+", " ", value).strip()
        
        # Remove prefixo acidental "ALERTA:" usado pelo script antigo
        value = re.sub(
            r"^ALERTA:\s+(?=(ALERTA|ATENÇÃO|ATENCAO|OBSERVAÇÃO|OBSERVACAO)\b)",
            "",
            value,
            flags=re.IGNORECASE
        )
        
        # Buscar padrão de prefixo
        pattern = r"^(ALERTA|ATENÇÃO|ATENCAO|OBSERVAÇÃO|OBSERVACAO)\s*[-:]\s*"
        match = re.match(pattern, value, flags=re.IGNORECASE)
        
        if match:
            raw_level = match.group(1).upper()
            prefix = self.LEVEL_PREFIX_MAP.get(raw_level, raw_level + ":")
            value = prefix + " " + value[match.end():].strip()
        
        # Normalizar abreviações mal espaçadas
        value = re.sub(
            r"^(AL|AT|OBS)\s*:\s*",
            lambda m: m.group(1).upper() + ": ",
            value,
            flags=re.IGNORECASE
        )
        
        return value.strip()
    
    def compact_alert_text(self, value: str) -> str:
        """
        Compacta o texto do alerta para caber em mensagens Meshtastic.
        Aplica todas as normalizações e compactações.
        """
        value = self.strip_html(value)
        value = self.normalize_dash(value)
        value = re.sub(r"\s+", " ", value).strip()
        
        # Converter prefixo de nível
        value = self.normalize_level_prefix(value)
        
        # Remover texto institucional repetitivo
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
        
        # Aplicar compactações de termos
        for old, new in self.TERM_REPLACEMENTS.items():
            value = value.replace(old, new)
        
        # Abreviar "com" para "c/"
        value = value.replace(" com ", " c/ ")
        
        # Normalizar pontuação
        value = re.sub(r"\s*,\s*", ", ", value)
        value = re.sub(r"\s*\.\s*", ". ", value)
        value = re.sub(r"\s*;\s*", "; ", value)
        value = re.sub(r"\s+", " ", value).strip()
        
        # Limpar espaços antes de pontuação
        value = value.replace(" .", ".")
        value = value.replace(" ,", ",")
        value = value.replace("..", ".")
        
        # Segurança: reaplicar normalização de prefixo se necessário
        value = self.normalize_level_prefix(value)
        
        return value.strip()
    
    def normalize_text(self, value: str, max_len: int = 220) -> str:
        """
        Normaliza e compacta texto, truncando se necessário.
        """
        value = self.compact_alert_text(value)
        
        if len(value) > max_len:
            return value[:max_len - 3].rstrip() + "..."
        
        return value
    
    def truncate_text(self, value: str, max_len: int) -> str:
        """Trunca texto com "..." se exceder tamanho máximo."""
        value = value.strip()
        
        if len(value) <= max_len:
            return value
        
        return value[:max_len - 3].rstrip() + "..."
    
    def build_alert_messages(self, alert: dict) -> Tuple[str, str]:
        """
        Constrói duas mensagens para um alerta:
        1. Conteúdo compactado (max 150 chars)
        2. Link (max 180 chars)
        
        Args:
            alert: Dicionário com dados do alerta (content, link)
            
        Returns:
            Tupla (msg_conteudo, msg_link)
        """
        content = alert.get("content", "").strip()
        link = alert.get("link", "").strip()
        
        # Recompactar para corrigir também alertas antigos
        content = self.compact_alert_text(content)
        
        # Adicionar prefixo "DC-SC"
        msg1 = f"DC-SC {content}".strip()
        msg2 = f"Link: {link}".strip()
        
        # Truncar aos tamanhos máximos
        msg1 = self.truncate_text(msg1, self.MAX_ALERT_MESSAGE_LEN)
        msg2 = self.truncate_text(msg2, self.MAX_LINK_MESSAGE_LEN)
        
        return msg1, msg2
    
    def sanitize_alert(self, alert: dict) -> dict:
        """
        Sanitiza e normaliza um alerta.
        Útil para alertas já persistidos em JSON antigos.
        """
        alert_copy = alert.copy()
        
        for key, max_len in (("title", 120), ("content", 220)):
            if key in alert_copy:
                alert_copy[key] = self.normalize_text(alert_copy[key], max_len)
        
        return alert_copy
