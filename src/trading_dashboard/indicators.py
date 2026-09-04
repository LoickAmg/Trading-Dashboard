"""Indicateurs techniques classiques, en fonctions pures sur une série de prix.

Ce sont des formules mathématiques standard (moyennes mobiles, RSI,
volatilité) — **pas des recommandations d'achat/vente**. Voir l'avertissement
dans ``__init__.py``.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from trading_dashboard.providers.base import Candle


def simple_moving_average(closes: list[float], window: int) -> list[float | None]:
    """SMA glissante : ``None`` tant qu'il n'y a pas assez de points pour la fenêtre."""
    if window < 1:
        raise ValueError("window doit être >= 1")
    result: list[float | None] = []
    for i in range(len(closes)):
        if i + 1 < window:
            result.append(None)
        else:
            window_slice = closes[i + 1 - window : i + 1]
            result.append(sum(window_slice) / window)
    return result


def exponential_moving_average(closes: list[float], window: int) -> list[float | None]:
    """EMA : initialisée par la SMA des ``window`` premiers points, puis lissage exponentiel."""
    if window < 1:
        raise ValueError("window doit être >= 1")
    if len(closes) < window:
        return [None] * len(closes)

    alpha = 2 / (window + 1)
    result: list[float | None] = [None] * (window - 1)
    ema = sum(closes[:window]) / window
    result.append(ema)
    for price in closes[window:]:
        ema = price * alpha + ema * (1 - alpha)
        result.append(ema)
    return result


def relative_strength_index(closes: list[float], window: int = 14) -> list[float | None]:
    """RSI (Wilder) sur ``window`` périodes. ``None`` tant qu'il n'y a pas assez d'historique.

    Convention usuelle : RSI = 100 si aucune perte sur la fenêtre (marché
    strictement haussier), 0 si aucun gain.
    """
    if window < 1:
        raise ValueError("window doit être >= 1")
    if len(closes) < window + 1:
        return [None] * len(closes)

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    result: list[float | None] = [None] * window  # pas de RSI avant d'avoir `window` deltas

    gains = [max(d, 0.0) for d in deltas[:window]]
    losses = [max(-d, 0.0) for d in deltas[:window]]
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window
    result.append(_rsi_from_averages(avg_gain, avg_loss))

    for delta in deltas[window:]:
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = (avg_gain * (window - 1) + gain) / window
        avg_loss = (avg_loss * (window - 1) + loss) / window
        result.append(_rsi_from_averages(avg_gain, avg_loss))

    return result


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def volatility(closes: list[float]) -> float | None:
    """Écart-type (échantillon) des rendements journaliers, en pourcentage.

    ``None`` si moins de 2 rendements disponibles (donc au moins 3 prix).
    """
    if len(closes) < 3:
        return None
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1] * 100
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]
    if len(returns) < 2:
        return None
    return statistics.stdev(returns)


@dataclass(frozen=True)
class IndicatorSnapshot:
    """Dernières valeurs des indicateurs pour un ticker, à afficher tel quel."""

    ticker: str
    sma_20: float | None
    sma_50: float | None
    rsi_14: float | None
    volatility_pct: float | None


def compute_snapshot(ticker: str, candles: list[Candle]) -> IndicatorSnapshot:
    """Calcule l'ensemble des indicateurs par défaut à partir d'un historique de bougies."""
    closes = [c.close for c in candles]
    return IndicatorSnapshot(
        ticker=ticker,
        sma_20=_last(simple_moving_average(closes, 20)),
        sma_50=_last(simple_moving_average(closes, 50)),
        rsi_14=_last(relative_strength_index(closes, 14)),
        volatility_pct=volatility(closes),
    )


def _last(values: list[float | None]) -> float | None:
    return values[-1] if values else None
