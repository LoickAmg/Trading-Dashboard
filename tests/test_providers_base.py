import pytest

from trading_dashboard.providers.base import Candle


def test_candle_valid_ohlc():
    c = Candle(date="2026-01-01", open=10, high=12, low=9, close=11, volume=1000)
    assert c.high == 12


def test_candle_rejects_high_below_low():
    with pytest.raises(ValueError):
        Candle(date="2026-01-01", open=10, high=8, low=9, close=10, volume=1000)


def test_candle_rejects_open_outside_range():
    with pytest.raises(ValueError):
        Candle(date="2026-01-01", open=20, high=12, low=9, close=10, volume=1000)


def test_candle_rejects_close_outside_range():
    with pytest.raises(ValueError):
        Candle(date="2026-01-01", open=10, high=12, low=9, close=20, volume=1000)
