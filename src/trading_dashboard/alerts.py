"""Alertes de seuil sur le prix d'un ticker (logique pure, aucune notification réelle).

Ce module se contente de comparer des prix à des seuils ; l'envoi effectif
d'une notification (email, push, etc.) n'est pas implémenté ici — voir
``price-tracker-bot`` (roadmap #16) pour un exemple de ce genre
d'intégration si besoin, on ne le duplique pas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Direction(StrEnum):
    ABOVE = "above"
    BELOW = "below"


@dataclass(frozen=True)
class Alert:
    """Se déclenche quand le prix de ``ticker`` passe au-dessus/en-dessous de ``threshold``."""

    ticker: str
    threshold: float
    direction: Direction


@dataclass(frozen=True)
class TriggeredAlert:
    alert: Alert
    current_price: float


def check_alerts(alerts: list[Alert], prices: dict[str, float]) -> list[TriggeredAlert]:
    """Renvoie les alertes déclenchées par les prix courants.

    Un ticker absent de ``prices`` est simplement ignoré (pas d'erreur).
    """
    triggered: list[TriggeredAlert] = []
    for alert in alerts:
        price = prices.get(alert.ticker)
        if price is None:
            continue
        if alert.direction == Direction.ABOVE and price >= alert.threshold:
            triggered.append(TriggeredAlert(alert, price))
        elif alert.direction == Direction.BELOW and price <= alert.threshold:
            triggered.append(TriggeredAlert(alert, price))
    return triggered
