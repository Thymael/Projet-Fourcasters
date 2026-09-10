# Machine Learning — Fourcasters

## Objectif

Prévoir le niveau de danger publié par Météo-France à J1 et J2.

Le modèle ne prédit pas un incendie réel : nous n'avons pas de données de feux
observés. Nous cherchons simplement à retrouver une classe de danger de 1 à 4.

## Fonctionnement

- 2024 et 2025 servent à entraîner le modèle ;
- 2026 sert à le tester ;
- un modèle est entraîné pour J1 et un autre pour J2 ;
- les lignes sans sept jours complets de météo sont retirées ;
- les variables utilisées sont la température, l'humidité, la pluie, le vent et
  le déficit de pression de vapeur.

La météo est prise sept jours avant la publication pour éviter d'utiliser une
information trop récente. ERA5 est publié avec un retard indiqué par
[Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api).

## Lancer le modèle

~~~
uv sync --extra ml --frozen
uv run dbt build --project-dir fourcasters --select +ml_train_incendie
uv run --extra ml python scripts/entrainer_ml_incendie.py
~~~

Le notebook notebooks/02_ml_danger_incendie.ipynb reprend les mêmes étapes
avec des graphiques simples.

## Résultats

On regarde principalement :

- l'accuracy : part des prédictions correctes ;
- le F1 macro : moyenne des résultats des quatre niveaux ;
- la matrice de confusion : niveaux souvent confondus.

Les résultats servent à comprendre le projet. Ils ne constituent pas un outil
d'alerte opérationnel.
