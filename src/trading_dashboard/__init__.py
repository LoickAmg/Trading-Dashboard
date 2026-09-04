"""trading-dashboard — suivi de portefeuille (simulé) et indicateurs techniques.

Avertissement important :

- Ceci n'est **pas un conseil financier**. Les indicateurs calculés (moyennes
  mobiles, RSI, volatilité) sont des formules mathématiques standard
  appliquées à des données de marché, pas des recommandations d'achat/vente.
- Le portefeuille est **entièrement simulé** : les positions sont saisies
  manuellement (ticker, quantité, prix de revient) dans un fichier local.
  Cet outil **n'exécute aucun ordre réel**, ne se connecte à aucun compte de
  courtage, et ne déplace aucun argent.
- Les données de marché viennent soit d'un générateur **synthétique**
  déterministe (démo/tests, aucune connexion réseau), soit d'une source
  publique gratuite (Stooq, données quotidiennes, pas de flux temps réel
  garanti) — à but éducatif, sans garantie d'exactitude ni de fraîcheur.
  Ne prenez aucune décision financière réelle sur la seule base de cet
  outil ; ce n'est ni un service réglementé, ni un substitut à un
  conseiller financier.
"""

__version__ = "0.1.0"
