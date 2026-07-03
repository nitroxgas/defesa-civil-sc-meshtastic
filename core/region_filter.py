"""
Filtro regional para alertas da Defesa Civil SC.

Permite configurar quais mesorregiões ou municípios devem receber alertas.
O filtro analisa o texto completo do alerta (título + conteúdo) e decide
se ele deve ser enviado ou ignorado.
"""

import json
import os
import re
import unicodedata
from typing import Dict, List, Optional, Set, Tuple


class RegionFilter:
    """Filtra alertas por mesorregião ou município de Santa Catarina."""

    DEFAULT_JSON_PATH = os.path.join(
        os.path.dirname(__file__),
        "sc_mesorregioes_microrregioes_municipios.json",
    )

    # Expansões de abreviações comuns usadas no feed e no formatter
    ABBREVIATION_EXPANSIONS = {
        "gde fpolis": "grande florianopolis",
        "gde florianopolis": "grande florianopolis",
        "ext oeste": "extremo oeste",
        "exto oeste": "extremo oeste",
        "plan norte": "planalto norte",
        "plan sul": "planalto sul",
        "lit sul": "litoral sul",
        "lit norte": "litoral norte",
        "alto vale": "alto vale do itajai",
        "alto vale itajai": "alto vale do itajai",
        "medio vale": "medio vale do itajai",
        "medio vale itajai": "medio vale do itajai",
        "baixo vale": "baixo vale do itajai",
        "baixo vale itajai": "baixo vale do itajai",
        "vale itajai": "vale do itaja",
        "meio oeste": "meio oeste",
        "fpolis": "florianopolis",
    }

    def __init__(
        self,
        config: Optional[Dict] = None,
        json_path: Optional[str] = None,
    ):
        """
        Inicializa o filtro regional.

        Args:
            config: Dicionário com:
                - enabled: bool (padrão False)
                - mode: "mesorregiao", "municipio" ou "both" (padrão "both")
                - mesorregioes: lista de nomes de mesorregiões
                - municipios: lista de nomes de municípios
            json_path: Caminho alternativo para o JSON de regiões.
        """
        self.config = config or {}
        self.enabled = bool(self.config.get("enabled", False))
        self.mode = (self.config.get("mode") or "both").lower()
        self.selected_mesorregioes = self.config.get("mesorregioes", []) or []
        self.selected_municipios = self.config.get("municipios", []) or []

        self._data = self._load_data(json_path or self.DEFAULT_JSON_PATH)
        self._mesorregioes_by_name = self._build_mesorregiao_index()
        self._municipios_by_name = self._build_municipio_index()

        self._normalized_mesorregioes = self._normalize_names(
            self.selected_mesorregioes
        )
        self._normalized_municipios = self._normalize_names(
            self.selected_municipios
        )

    def _load_data(self, json_path: str) -> Dict:
        """Carrega dados regionais do JSON."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar dados regionais: {e}")

    def _build_mesorregiao_index(self) -> Dict[str, str]:
        """Cria índice normalizado de mesorregiões."""
        index = {}
        for meso in self._data.get("mesorregioes", []):
            nome = meso.get("nome", "")
            if nome:
                normalized = self._normalize_text(nome)
                index[normalized] = nome
        return index

    def _build_municipio_index(self) -> Dict[str, Tuple[str, str]]:
        """Cria índice normalizado de municípios -> (mesorregiao, microrregiao)."""
        index = {}
        for meso in self._data.get("mesorregioes", []):
            meso_nome = meso.get("nome", "")
            for micro in meso.get("microrregioes", []):
                micro_nome = micro.get("nome", "")
                for municipio in micro.get("municipios", []):
                    normalized = self._normalize_text(municipio)
                    if normalized:
                        index[normalized] = (meso_nome, micro_nome)
        return index

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normaliza texto para comparação:
        - remove acentos
        - minúsculas
        - remove pontuação excessiva
        - espaços simples
        """
        if not text:
            return ""

        text = str(text)
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalize_names(self, names: List[str]) -> List[str]:
        """Normaliza uma lista de nomes, removendo duplicados e vazios."""
        seen = set()
        result = []
        for name in names:
            normalized = self._normalize_text(name)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    def _expand_abbreviations(self, text: str) -> str:
        """Expande abreviações regionais no texto para melhorar matching."""
        for abbr, full in self.ABBREVIATION_EXPANSIONS.items():
            text = text.replace(abbr, f" {full} ")
        return re.sub(r"\s+", " ", text).strip()

    def _prepare_text(self, alert: Dict) -> str:
        """Combina título e conteúdo do alerta e aplica normalizações."""
        title = alert.get("title", "")
        content = alert.get("content", "")
        raw_text = f"{title} {content}"
        normalized = self._normalize_text(raw_text)
        expanded = self._expand_abbreviations(normalized)
        return expanded

    def get_matches(self, alert: Dict) -> Dict[str, List[str]]:
        """
        Retorna mesorregiões e municípios configurados encontrados no alerta.

        Returns:
            {"mesorregioes": [...], "municipios": [...]}
        """
        matches = {"mesorregioes": [], "municipios": []}
        if not self.enabled:
            return matches

        text = self._prepare_text(alert)

        if self.mode in ("mesorregiao", "both"):
            for norm in self._normalized_mesorregioes:
                if norm in text:
                    matches["mesorregioes"].append(
                        self._mesorregioes_by_name.get(norm, norm)
                    )

        if self.mode in ("municipio", "both"):
            for norm in self._normalized_municipios:
                if norm in text:
                    matches["municipios"].append(norm.title())

        return matches

    def should_send(self, alert: Dict) -> bool:
        """
        Decide se o alerta deve ser enviado com base nas regiões configuradas.

        Returns:
            True se houver correspondência ou se o filtro estiver desativado.
        """
        if not self.enabled:
            return True

        matches = self.get_matches(alert)
        return bool(matches["mesorregioes"] or matches["municipios"])

    def get_available_mesorregioes(self) -> List[str]:
        """Retorna lista de mesorregiões disponíveis no JSON."""
        return [
            meso.get("nome", "")
            for meso in self._data.get("mesorregioes", [])
            if meso.get("nome")
        ]

    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Valida se as mesorregiões/municípios configurados existem no JSON.

        Returns:
            (válido, lista de erros)
        """
        errors = []
        available_mesos = set(self._mesorregioes_by_name.keys())
        available_munis = set(self._municipios_by_name.keys())

        for meso in self._normalized_mesorregioes:
            if meso not in available_mesos:
                errors.append(f"Mesorregião não encontrada: {meso}")

        for muni in self._normalized_municipios:
            if muni not in available_munis:
                errors.append(f"Município não encontrado: {muni}")

        return (not errors, errors)
