"""Testes para core.region_filter."""

import pytest
from core.region_filter import RegionFilter


@pytest.fixture
def filter_config():
    """Configuração padrão de teste."""
    return {
        "enabled": True,
        "mode": "both",
        "mesorregioes": ["Grande Florianópolis", "Vale do Itajaí"],
        "municipios": ["Florianópolis", "Joinville"],
    }


@pytest.fixture
def region_filter(filter_config):
    """Instância do filtro com configuração de teste."""
    return RegionFilter(filter_config)


class TestRegionFilter:
    """Testes para RegionFilter."""

    def test_disabled_filter_allows_all(self):
        """Filtro desativado permite qualquer alerta."""
        rf = RegionFilter({"enabled": False})
        alert = {
            "title": "ALERTA - Temporal",
            "content": "Alerta para região não configurada.",
        }
        assert rf.should_send(alert) is True

    def test_match_by_mesorregiao(self, region_filter):
        """Match por nome de mesorregião no título."""
        alert = {
            "title": "ALERTA - Temporal em Grande Florianópolis",
            "content": "Conteúdo do alerta.",
        }
        assert region_filter.should_send(alert) is True

    def test_match_by_municipio(self, region_filter):
        """Match por nome de município no conteúdo."""
        alert = {
            "title": "ATENÇÃO - Chuva forte",
            "content": "Município de Joinville atingido nas próximas horas.",
        }
        assert region_filter.should_send(alert) is True

    def test_no_match_returns_false(self, region_filter):
        """Alerta sem região/cidade configurada é rejeitado."""
        alert = {
            "title": "ATENÇÃO - Temporal",
            "content": "Alerta para Chapecó e região Oeste.",
        }
        assert region_filter.should_send(alert) is False

    def test_match_multiple_regions(self, region_filter):
        """Encontra múltiplas regiões no mesmo alerta."""
        alert = {
            "title": "OBSERVAÇÃO - Temporais",
            "content": "Para Grande Florianópolis e Vale do Itajaí.",
        }
        matches = region_filter.get_matches(alert)
        assert "Grande Florianópolis" in matches["mesorregioes"]
        assert "Vale do Itajaí" in matches["mesorregioes"]

    def test_accent_insensitive_match(self, region_filter):
        """Matching ignora acentos."""
        alert = {
            "title": "ALERTA - Temporal em Florianopolis",
            "content": "Conteúdo.",
        }
        assert region_filter.should_send(alert) is True

    def test_abbreviation_expansion(self, region_filter):
        """Abreviações são expandidas para matching."""
        alert = {
            "title": "ATENÇÃO - Temporal Gde Fpolis",
            "content": "Conteúdo.",
        }
        assert region_filter.should_send(alert) is True

    def test_mesorregiao_only_mode(self):
        """Modo mesorregiao ignora municípios."""
        rf = RegionFilter(
            {
                "enabled": True,
                "mode": "mesorregiao",
                "mesorregioes": ["Grande Florianópolis"],
                "municipios": ["Joinville"],
            }
        )
        alert = {
            "title": "ATENÇÃO - Temporal em Joinville",
            "content": "Conteúdo.",
        }
        assert rf.should_send(alert) is False

    def test_municipio_only_mode(self):
        """Modo municipio ignora mesorregiões."""
        rf = RegionFilter(
            {
                "enabled": True,
                "mode": "municipio",
                "mesorregioes": ["Grande Florianópolis"],
                "municipios": ["Joinville"],
            }
        )
        alert = {
            "title": "ATENÇÃO - Temporal em Grande Florianópolis",
            "content": "Conteúdo.",
        }
        assert rf.should_send(alert) is False

    def test_validate_config_unknown_region(self, filter_config):
        """Validação detecta mesorregião inexistente."""
        filter_config["mesorregioes"] = ["Região Inexistente"]
        rf = RegionFilter(filter_config)
        valid, errors = rf.validate_config()
        assert valid is False
        assert any("Mesorregião" in e for e in errors)

    def test_validate_config_unknown_municipio(self, filter_config):
        """Validação detecta município inexistente."""
        filter_config["municipios"] = ["Cidade Inexistente"]
        rf = RegionFilter(filter_config)
        valid, errors = rf.validate_config()
        assert valid is False
        assert any("Município" in e for e in errors)

    def test_validate_config_ok(self, region_filter):
        """Configuração válida passa na validação."""
        valid, errors = region_filter.validate_config()
        assert valid is True
        assert errors == []

    def test_available_mesorregioes(self, region_filter):
        """Retorna lista de mesorregiões disponíveis."""
        mesos = region_filter.get_available_mesorregioes()
        assert "Grande Florianópolis" in mesos
        assert "Vale do Itajaí" in mesos
        assert len(mesos) == 6
