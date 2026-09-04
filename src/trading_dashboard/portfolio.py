"""Portefeuille **simulé** : positions saisies manuellement, persistées en JSON.

Aucune connexion à un compte de courtage réel, aucun ordre exécuté — voir
l'avertissement dans ``__init__.py``. Ce module ne fait que suivre des
quantités et des prix de revient que l'utilisateur entre lui-même.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Holding:
    """Une position : ``quantity`` unités de ``ticker`` au prix unitaire ``cost_basis``."""

    ticker: str
    quantity: float
    cost_basis: float

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity doit être > 0")
        if self.cost_basis < 0:
            raise ValueError("cost_basis doit être >= 0")


@dataclass(frozen=True)
class Position:
    """Une position enrichie du prix courant : valeur de marché et plus/moins-value."""

    ticker: str
    quantity: float
    cost_basis: float
    current_price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_value(self) -> float:
        return self.quantity * self.cost_basis

    @property
    def pnl(self) -> float:
        return self.market_value - self.cost_value

    @property
    def pnl_percent(self) -> float:
        if self.cost_value == 0:
            return 0.0
        return self.pnl / self.cost_value * 100


@dataclass(frozen=True)
class PortfolioSummary:
    """Vue d'ensemble du portefeuille : positions enrichies + totaux."""

    positions: list[Position]

    @property
    def total_market_value(self) -> float:
        return sum(p.market_value for p in self.positions)

    @property
    def total_cost_value(self) -> float:
        return sum(p.cost_value for p in self.positions)

    @property
    def total_pnl(self) -> float:
        return self.total_market_value - self.total_cost_value

    def allocation(self) -> dict[str, float]:
        """Poids de chaque ticker dans le portefeuille, en pourcentage de la valeur totale."""
        total = self.total_market_value
        if total == 0:
            return {p.ticker: 0.0 for p in self.positions}
        return {p.ticker: p.market_value / total * 100 for p in self.positions}


def compute_positions(holdings: list[Holding], prices: dict[str, float]) -> list[Position]:
    """Enrichit chaque ``Holding`` avec son prix courant (0.0 si absent de ``prices``)."""
    return [
        Position(h.ticker, h.quantity, h.cost_basis, prices.get(h.ticker, 0.0)) for h in holdings
    ]


def compute_summary(holdings: list[Holding], prices: dict[str, float]) -> PortfolioSummary:
    return PortfolioSummary(positions=compute_positions(holdings, prices))


class PortfolioStore:
    """Persistance JSON simple d'une liste de :class:`Holding`, indexée par ticker."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[Holding]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as fh:
            raw = json.load(fh)
        return [Holding(**item) for item in raw]

    def save(self, holdings: list[Holding]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump([asdict(h) for h in holdings], fh, ensure_ascii=False, indent=2)

    def upsert(self, holding: Holding) -> list[Holding]:
        """Ajoute ou remplace la position sur ``holding.ticker``, puis persiste."""
        holdings = [h for h in self.load() if h.ticker != holding.ticker]
        holdings.append(holding)
        self.save(holdings)
        return holdings

    def remove(self, ticker: str) -> list[Holding]:
        holdings = [h for h in self.load() if h.ticker != ticker]
        self.save(holdings)
        return holdings
