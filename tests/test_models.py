"""Testes para core.models."""

import pytest
from datetime import datetime
from core.models import Alert, State


class TestAlert:
    """Testes para a dataclass Alert."""
    
    def test_alert_creation(self):
        """Testa criação básica de alerta."""
        alert = Alert(
            guid="test-123",
            title="Teste",
            content="Conteúdo teste",
            link="http://example.com",
            pub_date="2024-01-01T12:00:00",
            seen_at="2024-01-01T12:00:00"
        )
        
        assert alert.guid == "test-123"
        assert alert.title == "Teste"
        assert alert.content == "Conteúdo teste"
        assert alert.link == "http://example.com"
    
    def test_alert_to_dict(self):
        """Testa conversão de alerta para dicionário."""
        alert = Alert(
            guid="test-123",
            title="Teste",
            content="Conteúdo teste",
            link="http://example.com",
            pub_date="2024-01-01T12:00:00",
            seen_at="2024-01-01T12:00:00"
        )
        
        d = alert.to_dict()
        
        assert d["guid"] == "test-123"
        assert d["title"] == "Teste"
        assert d["content"] == "Conteúdo teste"
        assert isinstance(d, dict)
    
    def test_alert_from_dict(self):
        """Testa criação de alerta a partir de dicionário."""
        data = {
            "guid": "test-123",
            "title": "Teste",
            "content": "Conteúdo teste",
            "link": "http://example.com",
            "pub_date": "2024-01-01T12:00:00",
            "seen_at": "2024-01-01T12:00:00"
        }
        
        alert = Alert.from_dict(data)
        
        assert alert.guid == "test-123"
        assert alert.title == "Teste"
        assert alert.content == "Conteúdo teste"


class TestState:
    """Testes para a dataclass State."""
    
    def test_state_creation(self):
        """Testa criação básica de estado."""
        state = State()
        
        assert isinstance(state.sent_guids, list)
        assert isinstance(state.alerts, list)
        assert state.update_period is None
        assert state.update_frequency is None
    
    def test_state_with_alerts(self):
        """Testa estado com alertas."""
        alert = Alert(
            guid="test-123",
            title="Teste",
            content="Conteúdo teste",
            link="http://example.com"
        )
        
        state = State(alerts=[alert])
        
        assert len(state.alerts) == 1
        assert state.alerts[0].guid == "test-123"
    
    def test_state_to_dict(self):
        """Testa conversão de estado para dicionário."""
        state = State(
            sent_guids=["guid1", "guid2"],
            update_period="hourly",
            update_frequency=2
        )
        
        d = state.to_dict()
        
        assert d["sent_guids"] == ["guid1", "guid2"]
        assert d["update_period"] == "hourly"
        assert d["update_frequency"] == 2
        assert "created_at" in d
        assert "last_updated" in d
    
    def test_state_from_dict(self):
        """Testa criação de estado a partir de dicionário."""
        data = {
            "sent_guids": ["guid1", "guid2"],
            "alerts": [
                {
                    "guid": "alert1",
                    "title": "Alerta 1",
                    "content": "Conteúdo 1",
                    "link": "http://example.com",
                    "pub_date": "2024-01-01T12:00:00",
                    "seen_at": "2024-01-01T12:00:00"
                }
            ],
            "update_period": "hourly",
            "update_frequency": 2,
            "created_at": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00"
        }
        
        state = State.from_dict(data)
        
        assert state.sent_guids == ["guid1", "guid2"]
        assert len(state.alerts) == 1
        assert state.alerts[0].guid == "alert1"
        assert state.update_period == "hourly"
