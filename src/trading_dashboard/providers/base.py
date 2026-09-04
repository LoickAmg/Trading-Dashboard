"""Types communs à tous les fournisseurs de données de marché."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Candle:
    """Une bougie journalière (Open/High/Low/Close/Volume)."""

    date: str  # ISO 8601, ex. "2026-01-15"
    open: float
    high: float
    low: float
    close: float
    volume: int

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) < low ({self.low}) pour {self.date}")
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"open ({self.open}) hors de [low, high] pour {self.date}")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"close ({self.close}) hors de [low, high] pour {self.date}")


@dataclass(frozen=True)
class Quote:
    """Cotation instantanée (dernier prix connu + variation journalière)."""

    ticker: str
    price: float
    change_percent: float
    as_of: str  # ISO 8601


class PriceProvider(Protocol):
    """Contrat que doivent respecter tous les fournisseurs (synthétique ou réel)."""

    async def get_quote(self, ticker: str) -> Quote: ...

    async def get_history(self, ticker: str, days: int) -> list[Candle]: ...
