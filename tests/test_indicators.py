import pytest

from trading_dashboard.indicators import (
    compute_snapshot,
    exponential_moving_average,
    relative_strength_index,
    simple_moving_average,
    volatility,
)
from trading_dashboard.providers.base import Candle


def make_candle(date: str, close: float) -> Candle:
    return Candle(date=date, open=close, high=close, low=close, close=close, volume=1000)


def test_sma_none_until_window_filled():
    closes = [1, 2, 3, 4, 5]
    result = simple_moving_average(closes, window=3)
    assert result[:2] == [None, None]
    assert result[2] == pytest.approx(2.0)  # (1+2+3)/3
    assert result[3] == pytest.approx(3.0)  # (2+3+4)/3
    assert result[4] == pytest.approx(4.0)  # (3+4+5)/3


def test_sma_rejects_invalid_window():
    with pytest.raises(ValueError):
        simple_moving_average([1, 2, 3], window=0)


def test_ema_initial_value_is_sma():
    closes = [10, 12, 14, 16, 18]
    result = exponential_moving_average(closes, window=3)
    assert result[:2] == [None, None]
    assert result[2] == pytest.approx((10 + 12 + 14) / 3)


def test_ema_reacts_faster_than_sma_to_recent_move():
    closes = [10, 10, 10, 10, 10, 100]  # gros saut sur le dernier point
    sma = simple_moving_average(closes, window=5)
    ema = exponential_moving_average(closes, window=5)
    assert ema[-1] > sma[-1]  # l'EMA pondère davantage les points récents


def test_rsi_all_gains_is_100():
    closes = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]  # 14 hausses
    result = relative_strength_index(closes, window=14)
    assert result[-1] == pytest.approx(100.0)


def test_rsi_all_losses_is_0():
    closes = list(range(30, 30 - 15, -1))  # 14 baisses
    result = relative_strength_index(closes, window=14)
    assert result[-1] == pytest.approx(0.0)


def test_rsi_none_before_enough_history():
    closes = [10, 11, 12]
    result = relative_strength_index(closes, window=14)
    assert all(v is None for v in result)


def test_volatility_zero_for_constant_prices():
    closes = [100.0, 100.0, 100.0, 100.0]
    assert volatility(closes) == pytest.approx(0.0)


def test_volatility_none_with_too_few_points():
    assert volatility([100.0, 101.0]) is None


def test_volatility_higher_for_more_erratic_series():
    stable = [100, 101, 100, 101, 100, 101]
    erratic = [100, 130, 90, 140, 80, 150]
    assert volatility(erratic) > volatility(stable)


def test_compute_snapshot_aggregates_all_indicators():
    candles = [make_candle(f"2026-01-{i:02d}", 100 + i) for i in range(1, 60)]
    snapshot = compute_snapshot("TEST", candles)
    assert snapshot.ticker == "TEST"
    assert snapshot.sma_20 is not None
    assert snapshot.rsi_14 == pytest.approx(100.0)  # série strictement croissante
    assert snapshot.volatility_pct is not None
