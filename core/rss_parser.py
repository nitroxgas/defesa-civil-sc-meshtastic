"""
Parser de feed RSS da Defesa Civil SC.
Responsável por fazer download, parsing e normalização de alertas.
"""

import xml.etree.ElementTree as ET
import urllib.request
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from .constants import FEED_URL, DEFAULT_INTERVAL_MINUTES, MIN_INTERVAL_MINUTES, MAX_INTERVAL_MINUTES


class RSSParser:
    """Parser do feed RSS da Defesa Civil SC."""
    
    # Namespaces do feed
    NAMESPACES = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "sy": "http://purl.org/rss/1.0/modules/syndication/"
    }
    
    def __init__(self, timeout_seconds: int = 30, custom_url: Optional[str] = None):
        """
        Inicializa o parser RSS.
        
        Args:
            timeout_seconds: Timeout para requisição HTTP
            custom_url: URL customizada do feed (opcional, para testes)
        """
        self.timeout_seconds = timeout_seconds
        self.feed_url = custom_url or FEED_URL
    
    def fetch_feed(self) -> bytes:
        """
        Faz download do feed RSS.
        
        Returns:
            Conteúdo XML do feed em bytes
            
        Raises:
            Exception: Se falhar o download
        """
        req = urllib.request.Request(
            self.feed_url,
            headers={"User-Agent": "Defesa-Civil-SC-Meshtastic/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            return response.read()
    
    def parse_update_interval(self, root: ET.Element) -> Tuple[Optional[str], int, int]:
        """
        Extrai intervalo de atualização do feed RSS.
        
        Returns:
            Tupla (period, frequency, minutes_to_wait)
        """
        period = root.findtext(
            ".//sy:updatePeriod",
            default="",
            namespaces=self.NAMESPACES
        ).strip().lower()
        
        frequency_raw = root.findtext(
            ".//sy:updateFrequency",
            default="1",
            namespaces=self.NAMESPACES
        ).strip()
        
        try:
            frequency = int(frequency_raw)
            if frequency < 1:
                frequency = 1
        except Exception:
            frequency = 1
        
        # Calcular minutos baseado no período
        if period == "hourly":
            minutes = 60 // frequency
        elif period == "daily":
            minutes = 1440 // frequency
        elif period == "weekly":
            minutes = 10080 // frequency
        elif period == "monthly":
            minutes = 43200 // frequency
        else:
            minutes = DEFAULT_INTERVAL_MINUTES
        
        # Garantir limites mínimo e máximo
        if minutes < MIN_INTERVAL_MINUTES:
            minutes = MIN_INTERVAL_MINUTES
        if minutes > MAX_INTERVAL_MINUTES:
            minutes = MAX_INTERVAL_MINUTES
        
        return period or None, frequency, minutes
    
    def parse_feed(self, xml_bytes: bytes) -> Tuple[List[Dict], Optional[str], int, int]:
        """
        Faz parsing do feed RSS e extrai alertas.
        
        Args:
            xml_bytes: Conteúdo XML do feed em bytes
            
        Returns:
            Tupla (items, period, frequency, minutes)
        """
        root = ET.fromstring(xml_bytes)
        
        update_period, update_frequency, interval_minutes = self.parse_update_interval(root)
        
        items = []
        
        for item in root.findall(".//channel/item"):
            title = item.findtext("title", default="").strip()
            guid = item.findtext("guid", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            
            # Conteúdo HTML do alerta
            content_encoded = item.findtext(
                "content:encoded",
                default="",
                namespaces=self.NAMESPACES
            )
            
            # GUID é identificador único
            if not guid:
                guid = link or title
            
            alert = {
                "guid": guid,
                "title": title,
                "content": content_encoded,
                "link": link,
                "pub_date": pub_date,
                "seen_at": datetime.now().isoformat(timespec="seconds")
            }
            
            items.append(alert)
        
        return items, update_period, update_frequency, interval_minutes
    
    def parse_and_fetch(self) -> Tuple[List[Dict], Optional[str], int, int]:
        """
        Faz fetch do feed e retorna alertas parseados.
        
        Returns:
            Tupla (items, period, frequency, minutes)
            
        Raises:
            Exception: Se falhar o fetch ou parsing
        """
        xml_bytes = self.fetch_feed()
        return self.parse_feed(xml_bytes)
