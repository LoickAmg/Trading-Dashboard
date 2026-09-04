import pytest

from trading_dashboard.portfolio import Holding, PortfolioStore, compute_positions, compute_summary


def test_holding_rejects_non_positive_quantity():
    with pytest.raises(ValueError):
        Holding("AAPL.US", quantity=0, cost_basis=100)


def test_holding_rejects_negative_cost_basis():
    with pytest.raises(ValueError):
        Holding("AAPL.US", quantity=1, cost_basis=-1)


def test_compute_positions_uses_current_price():
    holdings = [Holding("AAPL.US", 10, 150.0)]
    positions = compute_positions(holdings, {"AAPL.US": 180.0})
    assert positions[0].market_value == pytest.approx(1800.0)
    assert positions[0].pnl == pytest.approx(300.0)
    assert positions[0].pnl_percent == pytest.approx(20.0)


def test_compute_positions_defaults_to_zero_price_if_missing():
    holdings = [Holding("UNKNOWN.US", 5, 10.0)]
    positions = compute_positions(holdings, {})
    assert positions[0].current_price == 0.0
    assert positions[0].market_value == 0.0


def test_compute_summary_totals_and_allocation():
    holdings = [Holding("A", 10, 100.0), Holding("B", 5, 200.0)]
    prices = {"A": 100.0, "B": 200.0}  # valeur de marché égale : 1000 chacun
    summary = compute_summary(holdings, prices)
    assert summary.total_market_value == pytest.approx(2000.0)
    allocation = summary.allocation()
    assert allocation["A"] == pytest.approx(50.0)
    assert allocation["B"] == pytest.approx(50.0)


def test_portfolio_store_roundtrip(tmp_path):
    store = PortfolioStore(tmp_path / "portfolio.json")
    assert store.load() == []

    store.upsert(Holding("AAPL.US", 10, 150.0))
    holdings = store.load()
    assert len(holdings) == 1
    assert holdings[0].ticker == "AAPL.US"


def test_portfolio_store_upsert_replaces_existing_ticker():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = PortfolioStore(Path(tmp) / "p.json")
        store.upsert(Holding("AAPL.US", 10, 150.0))
        store.upsert(Holding("AAPL.US", 20, 160.0))
        holdings = store.load()
        assert len(holdings) == 1
        assert holdings[0].quantity == 20


def test_portfolio_store_remove(tmp_path):
    store = PortfolioStore(tmp_path / "portfolio.json")
    store.upsert(Holding("AAPL.US", 10, 150.0))
    store.upsert(Holding("MSFT.US", 5, 300.0))
    remaining = store.remove("AAPL.US")
    assert [h.ticker for h in remaining] == ["MSFT.US"]
