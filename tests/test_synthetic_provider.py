from datetime import date

import pytest

from trading_dashboard.providers.synthetic import SyntheticProvider, generate_candles


def test_generate_candles_is_deterministic_for_same_ticker_and_end_date():
    a = generate_candles("AAPL.US", days=30, end_date=date(2026, 6, 1))
    b = generate_candles("AAPL.US", days=30, end_date=date(2026, 6, 1))
    assert a == b


def test_generate_candles_differs_per_ticker():
    a = generate_candles("AAPL.US", days=30, end_date=date(2026, 6, 1))
    b = generate_candles("MSFT.US", days=30, end_date=date(2026, 6, 1))
    assert [c.close for c in a] != [c.close for c in b]


def test_generate_candles_correct_length_and_dates_ascending():
    candles = generate_candles("AAPL.US", days=10, end_date=date(2026, 6, 1))
    assert len(candles) == 10
    dates = [c.date for c in candles]
    assert dates == sorted(dates)
    assert dates[-1] == "2026-06-01"


def test_generate_candles_rejects_invalid_days():
    with pytest.raises(ValueError):
        generate_candles("AAPL.US", days=0, end_date=date(2026, 6, 1))


def test_generate_candles_ohlc_invariants_hold():
    candles = generate_candles("TSLA.US", days=50, end_date=date(2026, 6, 1))
    for c in candles:
        assert c.low <= c.open <= c.high
        assert c.low <= c.close <= c.high
        assert c.volume > 0


async def test_provider_get_history_returns_requested_days():
    provider = SyntheticProvider()
    candles = await provider.get_history("AAPL.US", 15)
    assert len(candles) == 15
    assert "AAPL.US" in provider.seen_tickers


async def test_provider_get_quote_matches_last_candle_close():
    provider = SyntheticProvider()
    candles = await provider.get_history("AAPL.US", 5)
    quote = await provider.get_quote("AAPL.US")
    assert quote.price == candles[-1].close
    assert quote.ticker == "AAPL.US"
