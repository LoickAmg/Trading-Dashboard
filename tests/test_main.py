import pytest

from trading_dashboard.main import _build_provider, build_parser
from trading_dashboard.providers.stooq import StooqProvider
from trading_dashboard.providers.synthetic import SyntheticProvider


def test_build_parser_requires_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_serve_defaults():
    parser = build_parser()
    args = parser.parse_args(["serve"])
    assert args.provider == "synthetic"
    assert args.port == 8000


def test_build_provider_synthetic():
    assert isinstance(_build_provider("synthetic"), SyntheticProvider)


def test_build_provider_stooq():
    assert isinstance(_build_provider("stooq"), StooqProvider)


def test_build_provider_unknown_raises():
    with pytest.raises(ValueError):
        _build_provider("nope")
