"""Testes para core.rss_parser."""

import pytest
from core.rss_parser import RSSParser
from pathlib import Path


@pytest.fixture
def sample_feed():
    """Carrega amostra de feed RSS para testes."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_feed.xml"
    if fixture_path.exists():
        with open(fixture_path, "rb") as f:
            return f.read()
    
    # Feed de fallback para testes iniciais
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <title>Defesa Civil SC - Alertas</title>
    <sy:updatePeriod>hourly</sy:updatePeriod>
    <sy:updateFrequency>2</sy:updateFrequency>
    <item>
      <title>ALERTA - Temporal</title>
      <guid>alert-001</guid>
      <link>http://example.com/alert1</link>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
      <content:encoded><![CDATA[ALERTA - Temporal severo nas próximas 3 horas. Ocorrências ligue 199 ou 193.]]></content:encoded>
    </item>
  </channel>
</rss>
"""


class TestRSSParser:
    """Testes para RSSParser."""
    
    def test_parser_creation(self):
        """Testa criação do parser."""
        parser = RSSParser()
        
        assert parser.feed_url
        assert parser.timeout_seconds == 30
    
    def test_parse_update_interval_hourly(self, sample_feed):
        """Testa parsing de intervalo de atualização horário."""
        parser = RSSParser()
        
        items, period, frequency, minutes = parser.parse_feed(sample_feed)
        
        assert period == "hourly"
        assert frequency == 2
        assert minutes == 30  # 60 / 2
    
    def test_parse_feed_basic(self, sample_feed):
        """Testa parsing básico de feed."""
        parser = RSSParser()
        
        items, period, frequency, minutes = parser.parse_feed(sample_feed)
        
        assert len(items) >= 1
        assert items[0]["guid"] == "alert-001"
        assert items[0]["title"] == "ALERTA - Temporal"
        assert items[0]["link"] == "http://example.com/alert1"
    
    def test_parse_feed_has_timestamps(self, sample_feed):
        """Verifica se os alertas têm timestamps."""
        parser = RSSParser()
        
        items, _, _, _ = parser.parse_feed(sample_feed)
        
        assert len(items) > 0
        assert "seen_at" in items[0]
        assert items[0]["seen_at"]
    
    def test_parse_interval_daily(self):
        """Testa parsing de intervalo diário."""
        parser = RSSParser()
        
        daily_feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <sy:updatePeriod>daily</sy:updatePeriod>
    <sy:updateFrequency>1</sy:updateFrequency>
  </channel>
</rss>
"""
        
        _, period, frequency, minutes = parser.parse_feed(daily_feed)
        
        assert period == "daily"
        assert minutes == 1440  # 24 horas
    
    def test_parse_interval_weekly(self):
        """Testa parsing de intervalo semanal."""
        parser = RSSParser()
        
        weekly_feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <sy:updatePeriod>weekly</sy:updatePeriod>
    <sy:updateFrequency>1</sy:updateFrequency>
  </channel>
</rss>
"""
        
        _, period, frequency, minutes = parser.parse_feed(weekly_feed)
        
        assert period == "weekly"
        assert minutes == 10080  # 7 dias
    
    def test_parse_respects_min_interval(self):
        """Testa se respeita intervalo mínimo."""
        parser = RSSParser()
        
        # Feed com intervalo muito curto
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <sy:updatePeriod>hourly</sy:updatePeriod>
    <sy:updateFrequency>60</sy:updateFrequency>
  </channel>
</rss>
"""
        
        _, period, frequency, minutes = parser.parse_feed(feed)
        
        # Mínimo é 15 minutos
        assert minutes >= 15
    
    def test_parse_respects_max_interval(self):
        """Testa se respeita intervalo máximo."""
        parser = RSSParser()
        
        # Feed com intervalo muito longo
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <sy:updatePeriod>yearly</sy:updatePeriod>
    <sy:updateFrequency>1</sy:updateFrequency>
  </channel>
</rss>
"""
        
        _, period, frequency, minutes = parser.parse_feed(feed)
        
        # Máximo é 1440 minutos (24 horas)
        assert minutes <= 1440
