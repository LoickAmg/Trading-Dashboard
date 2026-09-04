"""Fournisseurs de données de marché : un ``Protocol`` async, deux implémentations.

- ``synthetic.py`` — générateur déterministe, aucune dépendance réseau,
  utilisé pour la démo et pour tous les tests.
- ``stooq.py`` — source réelle publique et gratuite (pas de clé API), à
  vocation éducative uniquement (données quotidiennes, pas de temps réel
  garanti). Jamais importé par les tests.
"""
