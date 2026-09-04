"""Fournisseur de données de marché réel, via le CSV public gratuit de Stooq.

Stooq (https://stooq.com) publie un export CSV de cours quotidiens sans
authentification ni clé API : ``https://stooq.com/q/d/l/?s={ticker}&i=d``.
Données à but éducatif uniquement — quotidiennes, pas de flux temps réel
garanti, aucune garantie d'exactitude ni de disponibilité.

Comme pour les autres projets de la roadmap, le "fetch" est **injecté**
(``FetchCsvFn``) : la logique de parsing (``parse_csv``) est pure et testée
avec des CSV canned, la fonction réseau réelle (``real_fetch_csv``) n'est
jamais utilisée par les tests.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from trading_dashboard.providers.base import Candle, Quote

FetchCsvFn = Callable[[str, int], Awaitable[str]]
"""Un callable async ``(ticker, days) -> corps CSV brut``."""

STOOQ_URL = "https://stooq.com/q/d/l/?s={ticker}&i=d"
USER_AGENT = "trading-dashboard/0.1 (outil personnel de suivi, cf. README)"


class StooqDataUnavailable(RuntimeError):
    """Levée quand Stooq ne renvoie aucune donnée exploitable pour ce ticker."""


def parse_csv(ticker: str, text: str) -> list[Candle]:
    """Parse un export CSV Stooq (``Date,Open,High,Low,Close,Volume``) en bougies.

    Ignore silencieusement les lignes malformées plutôt que de faire
    échouer tout le lot (mieux vaut un historique partiel qu'un crash sur
    une ligne isolée corrompue).
    """
    reader = csv.DictReader(io.StringIO(text.strip()))
    candles: list[Candle] = []
    for row in reader:
        try:
            candles.append(
                Candle(
                    date=row["Date"],
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(float(row["Volume"])),
                )
            )
        except (KeyError, ValueError):
            continue

    if not candles:
        raise StooqDataUnavailable(f"aucune donnée exploitable pour {ticker!r}")
    return candles


async def real_fetch_csv(ticker: str, days: int, timeout: float = 10.0) -> str:
    """Récupère le CSV brut depuis Stooq.

    ``days`` n'est pas envoyé à l'API : Stooq renvoie tout l'historique
    disponible, le filtrage sur ``days`` se fait après coup dans
    ``StooqProvider.get_history``.
    """
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        response = await client.get(STOOQ_URL.format(ticker=ticker))
        response.raise_for_status()
        return response.text


@dataclass
class StooqProvider:
    """Implémente :class:`~trading_dashboard.providers.base.PriceProvider` via Stooq."""

    fetch_csv: FetchCsvFn = real_fetch_csv

    async def get_history(self, ticker: str, days: int) -> list[Candle]:
        text = await self.fetch_csv(ticker, days)
        candles = parse_csv(ticker, text)
        return candles[-days:] if days < len(candles) else candles

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
