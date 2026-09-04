import pytest
from fastapi.testclient import TestClient

from trading_dashboard.api import create_app
from trading_dashboard.providers.synthetic import SyntheticProvider


@pytest.fixture
def client(tmp_path):
    provider = SyntheticProvider()
    app = create_app(provider, tmp_path / "portfolio.json")
    return TestClient(app)


def test_get_quote(client):
    res = client.get("/api/quote/AAPL.US")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "AAPL.US"
    assert isinstance(data["price"], float)


def test_get_history_default_days(client):
    res = client.get("/api/history/AAPL.US")
    assert res.status_code == 200
    assert len(res.json()) == 90


def test_get_history_custom_days(client):
    res = client.get("/api/history/AAPL.US?days=10")
    assert res.status_code == 200
    assert len(res.json()) == 10


def test_get_history_rejects_invalid_days(client):
    res = client.get("/api/history/AAPL.US?days=0")
    assert res.status_code == 400


def test_get_indicators(client):
    res = client.get("/api/indicators/AAPL.US")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "AAPL.US"
    assert "sma_20" in data


def test_portfolio_empty_by_default(client):
    res = client.get("/api/portfolio")
    assert res.status_code == 200
    data = res.json()
    assert data["positions"] == []
    assert data["total_market_value"] == 0


def test_add_and_list_holding(client):
    res = client.post(
        "/api/portfolio/holdings", json={"ticker": "AAPL.US", "quantity": 10, "cost_basis": 150.0}
    )
    assert res.status_code == 200
    holdings = res.json()
    assert holdings[0]["ticker"] == "AAPL.US"

    res = client.get("/api/portfolio")
    data = res.json()
    assert len(data["positions"]) == 1
    assert data["positions"][0]["quantity"] == 10
    assert "market_value" in data["positions"][0]


def test_add_holding_rejects_invalid_quantity(client):
    res = client.post(
        "/api/portfolio/holdings", json={"ticker": "AAPL.US", "quantity": -1, "cost_basis": 150.0}
    )
    assert res.status_code == 400


def test_delete_holding(client):
    client.post(
        "/api/portfolio/holdings", json={"ticker": "AAPL.US", "quantity": 10, "cost_basis": 150.0}
    )
    res = client.delete("/api/portfolio/holdings/AAPL.US")
    assert res.status_code == 200
    assert res.json() == []


def test_alerts_lifecycle(client):
    res = client.get("/api/alerts")
    assert res.json() == []

    res = client.post(
        "/api/alerts", json={"ticker": "AAPL.US", "threshold": 0.0, "direction": "above"}
    )
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Seuil à 0 : n'importe quel prix synthétique positif déclenche l'alerte.
    res = client.get("/api/alerts/triggered")
    assert res.status_code == 200
    triggered = res.json()
    assert len(triggered) == 1
    assert triggered[0]["alert"]["ticker"] == "AAPL.US"


def test_index_page_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "trading-dashboard" in res.text
