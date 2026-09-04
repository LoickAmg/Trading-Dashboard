"""CLI ``trading-dashboard`` : lance le serveur (synthétique par défaut, ou Stooq)."""

from __future__ import annotations

import argparse

import uvicorn

from trading_dashboard.api import create_app
from trading_dashboard.providers.base import PriceProvider
from trading_dashboard.providers.stooq import StooqProvider
from trading_dashboard.providers.synthetic import SyntheticProvider


def _build_provider(name: str) -> PriceProvider:
    if name == "synthetic":
        return SyntheticProvider()
    if name == "stooq":
        return StooqProvider()
    raise ValueError(f"fournisseur inconnu : {name!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading-dashboard")
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="Lancer le serveur web")
    p_serve.add_argument("--provider", choices=["synthetic", "stooq"], default="synthetic")
    p_serve.add_argument("--portfolio", default="portfolio.json")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        provider = _build_provider(args.provider)
        app = create_app(provider, args.portfolio)
        print(
            "⚠️  Portefeuille simulé, aucun ordre réel exécuté. "
            "Les indicateurs affichés ne sont pas des conseils financiers."
        )
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    raise SystemExit(f"commande inconnue : {args.command}")  # pragma: no cover


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
