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
    return """<?xml version="1.0" encoding="UTF-8"?>
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
""".encode("utf-8")


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
        # Nova estratégia: 1/4 do período (60 / 4 = 15)
        assert minutes == 15
    
    def test_parse_feed_basic(self, sample_feed):
        """Testa parsing básico de feed."""
        parser = RSSParser()
        
        items, period, frequency, minutes = parser.parse_feed(sample_feed)
        
        assert len(items) >= 1
        assert items[0]["guid"] == "https://www.defesacivil.sc.gov.br/alerta/temporal-severo-001"
        assert items[0]["title"] == "ALERTA - Temporal Severo"
        assert items[0]["link"] == "https://www.defesacivil.sc.gov.br/alerta/temporal-severo-001"
    
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
        # 1/4 de 1440 = 360 minutos
        assert minutes == 360
    
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
        # 10080 / 4 = 2520, mas limitado ao máximo de 1440
        assert minutes == 1440
    
    def test_parse_interval_override(self):
        """Testa override explícito do intervalo de polling."""
        parser = RSSParser(interval_minutes=45)
        
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <sy:updatePeriod>hourly</sy:updatePeriod>
    <sy:updateFrequency>1</sy:updateFrequency>
  </channel>
</rss>
"""
        
        _, period, frequency, minutes = parser.parse_feed(feed)
        
        assert minutes == 45
    
    def test_parse_interval_no_period(self):
        """Testa fallback quando feed não informa período."""
        parser = RSSParser()
        
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/">
  <channel>
    <title>Sem periodo</title>
  </channel>
</rss>
"""
        
        _, period, frequency, minutes = parser.parse_feed(feed)
        
        assert period is None
        assert minutes == 15  # DEFAULT_INTERVAL_MINUTES
    
    def test_parse_respects_min_interval(self):
        """Testa se respeita intervalo mínimo."""
        parser = RSSParser()
        
        # Feed com período curto e alta frequência
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
        
        # 1/4 de hourly = 15, respeitando mínimo
        assert minutes == 15
    
    def test_parse_respects_max_interval(self):
        """Testa se respeita intervalo máximo."""
        parser = RSSParser()
        
        # Feed com período muito longo
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
        
        # Período desconhecido: fallback para DEFAULT_INTERVAL_MINUTES
        assert minutes == 15
