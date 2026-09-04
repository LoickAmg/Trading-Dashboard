"""API FastAPI du tableau de bord.

``create_app(provider, portfolio_path)`` prend le fournisseur de données de
marché et le chemin du fichier de portefeuille **en paramètres** (même
philosophie d'injection que le reste du projet) : les tests construisent
l'app avec un ``SyntheticProvider`` et un fichier temporaire, sans jamais
toucher au réseau ni au disque réel de l'utilisateur.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from trading_dashboard.alerts import Alert, Direction, check_alerts
from trading_dashboard.indicators import compute_snapshot
from trading_dashboard.portfolio import Holding, PortfolioStore, compute_summary
from trading_dashboard.providers.base import PriceProvider

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"


class HoldingIn(BaseModel):
    ticker: str
    quantity: float
    cost_basis: float


class AlertIn(BaseModel):
    ticker: str
    threshold: float
    direction: Direction


def create_app(provider: PriceProvider, portfolio_path: str | Path) -> FastAPI:
    app = FastAPI(title="trading-dashboard", version="0.1.0")
    store = PortfolioStore(portfolio_path)
    app.state.provider = provider
    app.state.store = store
    app.state.alerts: list[Alert] = []

    @app.get("/api/quote/{ticker}")
    async def get_quote(ticker: str) -> dict:
        quote = await provider.get_quote(ticker)
        return asdict(quote)

    @app.get("/api/history/{ticker}")
    async def get_history(ticker: str, days: int = 90) -> list[dict]:
        if days < 1:
            raise HTTPException(400, "days doit être >= 1")
        candles = await provider.get_history(ticker, days)
        return [asdict(c) for c in candles]

    @app.get("/api/indicators/{ticker}")
    async def get_indicators(ticker: str, days: int = 90) -> dict:
        candles = await provider.get_history(ticker, days)
        return asdict(compute_snapshot(ticker, candles))

    @app.get("/api/portfolio")
    async def get_portfolio() -> dict:
        holdings = store.load()
        prices = {}
        for h in holdings:
            quote = await provider.get_quote(h.ticker)
            prices[h.ticker] = quote.price
        summary = compute_summary(holdings, prices)
        return {
            "positions": [
                asdict(p)
                | {
                    "market_value": p.market_value,
                    "pnl": p.pnl,
                    "pnl_percent": p.pnl_percent,
                }
                for p in summary.positions
            ],
            "total_market_value": summary.total_market_value,
            "total_cost_value": summary.total_cost_value,
            "total_pnl": summary.total_pnl,
            "allocation": summary.allocation(),
        }

    @app.post("/api/portfolio/holdings")
    async def upsert_holding(holding_in: HoldingIn) -> list[dict]:
        try:
            holding = Holding(holding_in.ticker, holding_in.quantity, holding_in.cost_basis)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        holdings = store.upsert(holding)
        return [asdict(h) for h in holdings]

    @app.delete("/api/portfolio/holdings/{ticker}")
    async def delete_holding(ticker: str) -> list[dict]:
        holdings = store.remove(ticker)
        return [asdict(h) for h in holdings]

    @app.get("/api/alerts")
    async def list_alerts() -> list[dict]:
        return [asdict(a) for a in app.state.alerts]

    @app.post("/api/alerts")
    async def add_alert(alert_in: AlertIn) -> list[dict]:
        app.state.alerts.append(Alert(alert_in.ticker, alert_in.threshold, alert_in.direction))
        return [asdict(a) for a in app.state.alerts]

    @app.get("/api/alerts/triggered")
    async def get_triggered_alerts() -> list[dict]:
        tickers = {a.ticker for a in app.state.alerts}
        prices = {t: (await provider.get_quote(t)).price for t in tickers}
        triggered = check_alerts(app.state.alerts, prices)
        return [
            {"alert": asdict(t.alert), "current_price": t.current_price} for t in triggered
        ]

    if WEB_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(str(WEB_DIR / "index.html"))

    return app
