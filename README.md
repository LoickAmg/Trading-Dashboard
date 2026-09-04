# trading-dashboard

Tableau de bord de suivi de portefeuille **simulé** et d'indicateurs
techniques, en Python (FastAPI + `asyncio`) avec un frontend statique
(vanilla JS, graphique sur `<canvas>`, sans dépendance externe).

## ⚠️ Avertissement

- **Pas un conseil financier.** Les indicateurs (SMA, EMA, RSI, volatilité)
  sont des formules mathématiques standard, pas des recommandations
  d'achat/vente.
- **Portefeuille entièrement simulé.** Les positions sont saisies à la
  main (ticker, quantité, prix de revient) dans un fichier JSON local. Cet
  outil **n'exécute aucun ordre réel** et ne se connecte à **aucun compte
  de courtage**.
- Les données de marché viennent soit d'un **générateur synthétique**
  déterministe (démo, aucun réseau), soit de **Stooq** (source publique
  gratuite, données quotidiennes — pas un flux temps réel garanti). But
  éducatif, sans garantie d'exactitude. Ne prenez aucune décision
  financière réelle sur la seule base de cet outil.

## Fonctionnalités

```bash
# Démo (données synthétiques, aucun réseau requis)
trading-dashboard serve --provider synthetic

# Avec des données réelles (quotidiennes) via Stooq
trading-dashboard serve --provider stooq --portfolio mon_portefeuille.json
```

Puis ouvrir `http://127.0.0.1:8000/` : suivi d'un ticker (prix, graphique,
indicateurs) et portefeuille simulé (ajout/suppression de positions, P&L,
allocation).

### API REST

| Endpoint | Description |
| --- | --- |
| `GET /api/quote/{ticker}` | Dernier prix connu + variation |
| `GET /api/history/{ticker}?days=90` | Historique de bougies OHLC |
| `GET /api/indicators/{ticker}?days=90` | SMA20/SMA50/RSI14/volatilité |
| `GET /api/portfolio` | Positions enrichies + totaux + allocation |
| `POST /api/portfolio/holdings` | Ajouter/mettre à jour une position |
| `DELETE /api/portfolio/holdings/{ticker}` | Retirer une position |
| `GET/POST /api/alerts` | Lister/ajouter une alerte de seuil |
| `GET /api/alerts/triggered` | Alertes actuellement déclenchées |

## Installation

```bash
pip install -e ".[test]"
```

## Architecture

- `providers/base.py` — types communs (`Candle`, `Quote`) et le `Protocol`
  `PriceProvider` (`get_quote`/`get_history`), implémenté par deux
  fournisseurs interchangeables.
- `providers/synthetic.py` — génération déterministe de prix : simule le
  chemin de prix **depuis une date fixe (2020-01-01)** jusqu'à la date
  demandée, puis ne renvoie que la fenêtre voulue. C'est ce qui garantit
  que le prix d'un jour donné est identique quel que soit le nombre de
  jours d'historique demandé (`get_quote`, qui ne regarde que les 2
  derniers jours, reste cohérent avec un historique de 90 jours).
- `providers/stooq.py` — fournisseur réel (CSV public Stooq, sans clé
  API) ; le parsing (`parse_csv`, pur) est séparé du fetch réseau
  (`real_fetch_csv`), avec un `fetch_csv` injectable pour les tests.
- `indicators.py` — SMA, EMA, RSI (méthode de Wilder), volatilité :
  fonctions pures sur une liste de prix.
- `portfolio.py` — `Holding` (saisie utilisateur), `Position` (enrichie du
  prix courant), `PortfolioStore` (persistance JSON).
- `alerts.py` — alertes de seuil (au-dessus/en-dessous), logique pure.
- `api.py` — `create_app(provider, portfolio_path)` : FastAPI dont le
  fournisseur de données et le chemin de portefeuille sont **injectés en
  paramètres**, ce qui rend toute l'API testable avec `TestClient` sans
  réseau ni fichier réel.
- `web/` — frontend statique (HTML/CSS/JS vanilla), servi directement par
  FastAPI (`StaticFiles`).

## Tests

```bash
pytest -v      # 55 tests
ruff check .
```

Tous les tests sont déterministes : `SyntheticProvider` pour les données
de marché, fichiers temporaires (`tmp_path`) pour le portefeuille, et
`fetch_csv` injecté pour `StooqProvider` — aucun test ne touche le réseau
réel ni un fichier permanent.

## Limites connues

- **Pas de vrai temps réel** : Stooq fournit des données quotidiennes, pas
  un flux tick-by-tick. Le frontend rafraîchit périodiquement (polling),
  ce qui donne une impression de "live" mais reste borné par la fraîcheur
  des données sources.
- **Aucune authentification** : pensé pour un usage local mono-utilisateur
  (comme les autres projets "tracker" de la roadmap), pas pour être exposé
  publiquement tel quel.
- **`web/` non empaqueté** : le frontend statique est résolu par chemin
  relatif au dépôt (`Path(__file__).parent.parent.parent / "web"`) ; un
  packaging pip non-éditable (`pip install .` hors dépôt) ne l'inclurait
  pas sans configuration `package_data` additionnelle — hors du besoin
  actuel (usage local depuis le dépôt).
- **Stooq peut être indisponible ou limiter les requêtes** : c'est un
  service tiers gratuit sans SLA ; en cas d'échec, utiliser
  `--provider synthetic` pour la démo.

## Licence

MIT — voir [LICENSE](./LICENSE).
