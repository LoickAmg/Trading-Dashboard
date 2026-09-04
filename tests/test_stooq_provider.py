import pytest

from trading_dashboard.providers.stooq import StooqDataUnavailable, StooqProvider, parse_csv

SAMPLE_CSV = (
    "Date,Open,High,Low,Close,Volume\n"
    "2026-05-28,190.00,192.50,189.00,191.00,50000000\n"
    "2026-05-29,191.00,193.00,190.50,192.75,48000000\n"
    "2026-05-30,192.75,194.00,191.00,193.50,52000000\n"
)

NO_DATA_CSV = "Date,Open,High,Low,Close,Volume\nN/D,N/D,N/D,N/D,N/D,N/D\n"


def test_parse_csv_extracts_all_rows():
    candles = parse_csv("AAPL.US", SAMPLE_CSV)
    assert len(candles) == 3
    assert candles[0].date == "2026-05-28"
    assert candles[-1].close == pytest.approx(193.50)


def test_parse_csv_raises_when_no_usable_rows():
    with pytest.raises(StooqDataUnavailable):
        parse_csv("UNKNOWN.US", NO_DATA_CSV)


async def test_stooq_provider_get_history_uses_injected_fetch():
    async def fake_fetch(ticker: str, days: int) -> str:
        assert ticker == "AAPL.US"
        return SAMPLE_CSV

    provider = StooqProvider(fetch_csv=fake_fetch)
    candles = await provider.get_history("AAPL.US", days=2)
    assert len(candles) == 2
    assert candles[-1].close == pytest.approx(193.50)


async def test_stooq_provider_get_quote_uses_injected_fetch():
    async def fake_fetch(ticker: str, days: int) -> str:
        return SAMPLE_CSV

    provider = StooqProvider(fetch_csv=fake_fetch)
    quote = await provider.get_quote("AAPL.US")
    assert quote.price == pytest.approx(193.50)
    expected_change = round((193.50 - 192.75) / 192.75 * 100, 2)
    assert quote.change_percent == pytest.approx(expected_change)
