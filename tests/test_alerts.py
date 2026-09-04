from trading_dashboard.alerts import Alert, Direction, check_alerts


def test_alert_above_triggers_when_price_reaches_threshold():
    alerts = [Alert("AAPL.US", threshold=200.0, direction=Direction.ABOVE)]
    triggered = check_alerts(alerts, {"AAPL.US": 200.0})
    assert len(triggered) == 1


def test_alert_above_does_not_trigger_below_threshold():
    alerts = [Alert("AAPL.US", threshold=200.0, direction=Direction.ABOVE)]
    triggered = check_alerts(alerts, {"AAPL.US": 199.99})
    assert triggered == []


def test_alert_below_triggers_when_price_drops_to_threshold():
    alerts = [Alert("AAPL.US", threshold=100.0, direction=Direction.BELOW)]
    triggered = check_alerts(alerts, {"AAPL.US": 100.0})
    assert len(triggered) == 1


def test_alert_ignored_when_ticker_missing_from_prices():
    alerts = [Alert("AAPL.US", threshold=100.0, direction=Direction.BELOW)]
    triggered = check_alerts(alerts, {})
    assert triggered == []


def test_multiple_alerts_only_matching_ones_triggered():
    alerts = [
        Alert("AAPL.US", threshold=200.0, direction=Direction.ABOVE),
        Alert("MSFT.US", threshold=300.0, direction=Direction.BELOW),
    ]
    prices = {"AAPL.US": 250.0, "MSFT.US": 350.0}
    triggered = check_alerts(alerts, prices)
    assert len(triggered) == 1
    assert triggered[0].alert.ticker == "AAPL.US"
