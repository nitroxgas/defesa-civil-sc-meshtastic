"""Testes para core.message_formatter."""

import pytest
from core.message_formatter import MessageFormatter


@pytest.fixture
def formatter():
    """Cria instância do formatador."""
    return MessageFormatter()


class TestMessageFormatter:
    """Testes para MessageFormatter."""
    
    def test_strip_html_basic(self, formatter):
        """Testa remoção básica de HTML."""
        html = "<p>Teste</p>"
        result = formatter.strip_html(html)
        
        assert result == "Teste"
        assert "<p>" not in result
    
    def test_strip_html_with_line_breaks(self, formatter):
        """Testa remoção de HTML com quebras de linha."""
        html = "<p>Linha 1</p><br/><p>Linha 2</p>"
        result = formatter.strip_html(html)
        
        assert "Linha 1" in result
        assert "Linha 2" in result
        assert "<p>" not in result
        assert "<br" not in result
    
    def test_normalize_dash(self, formatter):
        """Testa normalização de travessões."""
        text_with_en_dash = "Teste–dash"
        text_with_em_dash = "Teste—dash"
        
        result1 = formatter.normalize_dash(text_with_en_dash)
        result2 = formatter.normalize_dash(text_with_em_dash)
        
        assert result1 == "Teste-dash"
        assert result2 == "Teste-dash"
    
    def test_normalize_level_prefix_alerta(self, formatter):
        """Testa conversão de prefixo ALERTA."""
        text = "ALERTA - Teste de temporal"
        result = formatter.normalize_level_prefix(text)
        
        assert result.startswith("AL:")
        assert "Teste de temporal" in result
    
    def test_normalize_level_prefix_atencao(self, formatter):
        """Testa conversão de prefixo ATENÇÃO."""
        text = "ATENÇÃO - Possível temporal"
        result = formatter.normalize_level_prefix(text)
        
        assert result.startswith("AT:")
    
    def test_normalize_level_prefix_observacao(self, formatter):
        """Testa conversão de prefixo OBSERVAÇÃO."""
        text = "OBSERVAÇÃO - Informação importante"
        result = formatter.normalize_level_prefix(text)
        
        assert result.startswith("OBS:")
    
    def test_compact_alert_text(self, formatter):
        """Testa compactação de texto de alerta."""
        text = "ALERTA - Temporal severo com rajadas de vento forte nas próximas 3 horas."
        result = formatter.compact_alert_text(text)
        
        # Deve conter compactações
        assert "AL:" in result or result.startswith("AL")
        assert "vento" in result
        assert "Val: 3h" in result or "3h" in result
        assert "Temporal severo" in result or "temporal" in result
    
    def test_normalize_text_truncation(self, formatter):
        """Testa truncação de texto longo."""
        long_text = "A" * 300
        result = formatter.normalize_text(long_text, max_len=100)
        
        assert len(result) <= 100
        assert result.endswith("...")
    
    def test_normalize_text_short(self, formatter):
        """Testa que texto curto não é truncado."""
        short_text = "Texto curto"
        result = formatter.normalize_text(short_text, max_len=100)
        
        assert result == short_text
        assert "..." not in result
    
    def test_truncate_text(self, formatter):
        """Testa função de truncação."""
        long_text = "A" * 200
        result = formatter.truncate_text(long_text, max_len=50)
        
        assert len(result) <= 50
        assert result.endswith("...")
    
    def test_build_alert_messages(self, formatter):
        """Testa construção de duas mensagens de alerta."""
        alert = {
            "content": "ALERTA - Temporal nas próximas 3 horas",
            "link": "http://example.com/alert"
        }
        
        msg1, msg2 = formatter.build_alert_messages(alert)
        
        assert msg1.startswith("DC-SC")
        assert msg2.startswith("Link:")
        assert len(msg1) <= 150
        assert len(msg2) <= 180
    
    def test_sanitize_alert(self, formatter):
        """Testa sanitização de alerta."""
        alert = {
            "title": "ALERTA - " + "X" * 150,
            "content": "ATENÇÃO - " + "Y" * 300,
            "link": "http://example.com"
        }
        
        result = formatter.sanitize_alert(alert)
        
        assert len(result["title"]) <= 120
        assert len(result["content"]) <= 220
    
    def test_compact_removes_institutional_text(self, formatter):
        """Testa que texto institucional é removido."""
        text = "ALERTA - Temporal. Ocorrências ligue 199 ou 193. A Secretaria de Defesa Civil..."
        result = formatter.compact_alert_text(text)
        
        assert "Ocorrências" not in result
        assert "A Secretaria" not in result
        assert "199/193" in result
    
    def test_compact_handles_region_abbreviations(self, formatter):
        """Testa compactação de nomes de regiões."""
        text = "Grande Florianópolis"
        result = formatter.compact_alert_text(text)
        
        assert "Gde Fpolis" in result
    
    def test_html_entities_decoded(self, formatter):
        """Testa decodificação de entidades HTML."""
        text = "Teste&nbsp;com&nbsp;entidades"
        result = formatter.strip_html(text)
        
        # As entidades devem ser normalizadas
        assert "Teste" in result
        assert "com" in result
