"""
Gerenciador de estado persistente para o integrador Defesa Civil SC - Meshtastic.
Responsável por carregar, salvar e gerenciar estado em arquivo JSON.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class StateManager:
    """Gerencia persistência de estado em JSON."""
    
    def __init__(self, file_path: str):
        """
        Inicializa o gerenciador de estado.
        
        Args:
            file_path: Caminho do arquivo JSON para persistir estado
        """
        self.file_path = Path(file_path)
        self.state_data = self._load()
    
    def _load(self) -> Dict:
        """Carrega estado do arquivo JSON ou retorna estado vazio."""
        if not self.file_path.exists():
            return self._create_empty_state()
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validar estrutura mínima
                if "sent_guids" not in data or "alerts" not in data:
                    return self._create_empty_state()
                return data
        except Exception as e:
            print(f"Erro ao carregar estado: {e}. Criando novo estado.")
            return self._create_empty_state()
    
    def _create_empty_state(self) -> Dict:
        """Cria estrutura de estado vazia."""
        return {
            "sent_guids": [],
            "alerts": [],
            "update_period": None,
            "update_frequency": None,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "last_updated": datetime.now().isoformat(timespec="seconds")
        }
    
    def save(self) -> bool:
        """
        Salva estado em arquivo JSON.
        
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_data["last_updated"] = datetime.now().isoformat(timespec="seconds")
            
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.state_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
            return False
    
    def add_sent_guid(self, guid: str) -> None:
        """Adiciona GUID à lista de alertas já enviados."""
        if guid not in self.state_data["sent_guids"]:
            self.state_data["sent_guids"].append(guid)
    
    def is_guid_sent(self, guid: str) -> bool:
        """Verifica se um GUID já foi enviado."""
        return guid in self.state_data["sent_guids"]
    
    def add_alert(self, alert: Dict, max_history: int = 10) -> None:
        """
        Adiciona alerta ao histórico, mantendo apenas os mais recentes.
        
        Args:
            alert: Dicionário com dados do alerta
            max_history: Número máximo de alertas a armazenar
        """
        self.state_data["alerts"].insert(0, alert)
        # Manter apenas os últimos N alertas
        self.state_data["alerts"] = self.state_data["alerts"][:max_history]
    
    def get_alerts(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retorna alertas armazenados.
        
        Args:
            limit: Número máximo de alertas a retornar. Se None, retorna todos.
            
        Returns:
            Lista de alertas
        """
        alerts = self.state_data.get("alerts", [])
        if limit:
            return alerts[:limit]
        return alerts
    
    def get_latest_alerts(self, count: int = 3) -> List[Dict]:
        """Retorna os N alertas mais recentes."""
        return self.get_alerts(limit=count)
    
    def set_update_interval(self, period: Optional[str], frequency: int, minutes: int) -> None:
        """Define intervalo de atualização do feed."""
        self.state_data["update_period"] = period
        self.state_data["update_frequency"] = frequency
    
    def clear_sent_guids(self) -> None:
        """Limpa lista de GUIDs enviados (útil para reprocessar alertas)."""
        self.state_data["sent_guids"] = []
