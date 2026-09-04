"""Fournisseur de données de marché synthétiques (démo + tests).

Aucun réseau, aucune dépendance externe : chaque ticker a sa propre série de
prix déterministe, dérivée d'un ``random.Random`` initialisé avec un seed
stable calculé à partir du nom du ticker (``zlib.crc32``, stable entre
exécutions — contrairement à ``hash()`` sur une chaîne, qui est salé
aléatoirement par processus). Deux appels avec le même ticker et la même
date de fin produisent exactement la même série : c'est ce qui permet de
tester cette classe et tout ce qui en dépend sans aucun mock supplémentaire.
"""

from __future__ import annotations

import random
import zlib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from trading_dashboard.providers.base import Candle, Quote

DEFAULT_BASE_PRICE = 100.0
DAILY_DRIFT = 0.0003
DAILY_VOLATILITY = 0.015
INTRADAY_RANGE_VOLATILITY = 0.004
EPOCH = date(2020, 1, 1)
"""Point de départ fixe de la simulation de prix (voir ``generate_candles``)."""


def _seed_for(ticker: str) -> int:
    """Seed stable (indépendant du process) dérivé du nom du ticker."""
    return zlib.crc32(ticker.encode("utf-8"))


def generate_candles(ticker: str, days: int, end_date: date) -> list[Candle]:
    """Génère ``days`` bougies journalières se terminant le ``end_date`` inclus.

    Fonction pure (à seed égal, sortie identique) : c'est le cœur testable
    du générateur, séparé de ``SyntheticProvider`` qui y ajoute juste la
    date du jour par défaut.

    Important : le chemin de prix est simulé **depuis une date fixe**
    (``EPOCH``) jusqu'à ``end_date``, puis seules les ``days`` dernières
    bougies sont renvoyées — pas simulé en partant à rebours depuis
    ``end_date``. Cela garantit que le prix d'un jour donné est toujours le
    même quel que soit ``days`` demandé (``get_quote`` qui ne regarde que
    les 2 derniers jours reste cohérent avec un historique de 90 jours) :
    sans ça, deux fenêtres différentes consommeraient le générateur
    aléatoire dans un ordre différent et produiraient des valeurs
    incohérentes pour le "même" jour.
    """
    if days < 1:
        raise ValueError("days doit être >= 1")
    if end_date < EPOCH:
        raise ValueError(f"end_date doit être >= {EPOCH.isoformat()}")

    total_days = (end_date - EPOCH).days + 1
    rng = random.Random(_seed_for(ticker))
    price = max(0.01, DEFAULT_BASE_PRICE + (rng.random() - 0.5) * 40)

    candles: list[Candle] = []
    for i in range(total_days):
        current_date = EPOCH + timedelta(days=i)
        daily_return = rng.gauss(DAILY_DRIFT, DAILY_VOLATILITY)
        open_price = price
        close_price = max(0.01, open_price * (1 + daily_return))
        high = max(open_price, close_price) * (1 + abs(rng.gauss(0, INTRADAY_RANGE_VOLATILITY)))
        low = min(open_price, close_price) * (1 - abs(rng.gauss(0, INTRADAY_RANGE_VOLATILITY)))
        low = min(low, open_price, close_price)  # garde-fou contre les arrondis flottants
        volume = rng.randint(100_000, 5_000_000)
        candles.append(
            Candle(
                date=current_date.isoformat(),
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close_price, 2),
                volume=volume,
            )
        )
        price = close_price

    return candles[-days:]


@dataclass
class SyntheticProvider:
    """Implémente :class:`~trading_dashboard.providers.base.PriceProvider` sans réseau."""

    seen_tickers: set[str] = field(default_factory=set)
    """Tickers déjà interrogés (utile pour l'API : lister les tickers connus)."""

    async def get_history(self, ticker: str, days: int) -> list[Candle]:
        self.seen_tickers.add(ticker)
        return generate_candles(ticker, days, date.today())

    async def get_quote(self, ticker: str) -> Quote:
        candles = await self.get_history(ticker, 2)
        last = candles[-1]
        prev = candles[-2] if len(candles) > 1 else last
        change_percent = 0.0 if prev.close == 0 else (last.close - prev.close) / prev.close * 100
        return Quote(
            ticker=ticker,
            price=last.close,
            change_percent=round(change_percent, 2),
            as_of=datetime.now(UTC).isoformat(),
        )
