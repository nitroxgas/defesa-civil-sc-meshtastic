"""Modelos de dados compartilhados entre integrações."""

from dataclasses import dataclass, asdict, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Alert:
    """Representa um alerta da Defesa Civil SC."""
    
    guid: str
    title: str
    content: str
    link: str
    pub_date: str
    seen_at: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        """Cria Alert a partir de dicionário."""
        return cls(
            guid=data.get("guid", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            link=data.get("link", ""),
            pub_date=data.get("pub_date", ""),
            seen_at=data.get("seen_at", "")
        )
    
    def to_dict(self) -> dict:
        """Converte Alert para dicionário."""
        return asdict(self)


@dataclass
class State:
    """Estado persistido de alertas enviados."""
    
    sent_guids: List[str] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    update_period: Optional[str] = None
    update_frequency: int = 1
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    
    @classmethod
    def from_dict(cls, data: dict) -> "State":
        """Cria State a partir de dicionário (carregado do JSON)."""
        alerts = [Alert.from_dict(a) for a in data.get("alerts", [])]
        return cls(
            sent_guids=data.get("sent_guids", []),
            alerts=alerts,
            update_period=data.get("update_period"),
            update_frequency=data.get("update_frequency", 1),
            last_updated=data.get("last_updated", datetime.now().isoformat(timespec="seconds")),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds"))
        )
    
    def to_dict(self) -> dict:
        """Converte State para dicionário (para salvar no JSON)."""
        return {
            "sent_guids": self.sent_guids,
            "alerts": [a.to_dict() for a in self.alerts],
            "update_period": self.update_period,
            "update_frequency": self.update_frequency,
            "last_updated": self.last_updated,
            "created_at": self.created_at
        }
