# Modèle de danger incendie

Le modèle cherche à reproduire le niveau de danger Météo-France à J1 et J2,
une classe de 1 à 4. Nous ne disposons pas ici de cible décrivant les feux réels.

## Préparation

`ml_features_incendie` rassemble la météo par département. Pour une publication
au jour D, les variables utilisent le jour D−7 et une fenêtre allant de D−13
à D−7 inclus. `meteo_disponible` vaut vrai si les sept jours ont les mesures
nécessaires. Une journée manquante ne doit pas être remplacée par zéro.

La pluie utilisée par le modèle est la moyenne des points du département.
`precipitations_moyennes_7j` est le **cumul sur sept jours de ces moyennes**,
en mm. La somme de tous les points favoriserait les départements qui en ont
le plus.

`ml_train_incendie` ajoute l'échéance et la cible. Pour chaque date de publication,
département et échéance, elle garde le dernier bulletin disponible ce jour-là.
Les versions précédentes restent présentes dans `fact_danger_incendie`.

## Apprentissage et test

Un seul `RandomForestClassifier` apprend J1 et J2, avec `horizon_jours` parmi
les 14 variables. Il utilise 200 arbres, une graine fixée à 42 et des poids
équilibrés entre classes. Il n'y a pas de recherche automatique de paramètres.

Les 20 % de dates les plus récentes servent au test. Tous les départements
et les deux échéances d'un jour restent dans le même groupe. Les deux jours
qui précèdent le test sont écartés pour que les cibles J1/J2 d'apprentissage
ne chevauchent pas sa période. Ce découpage ne fixe pas une année précise.

Les valeurs manquantes sont retirées et comptées. Une cible hors des quatre
classes, une date absente ou une valeur infinie provoque une erreur.

## Exécution et résultats

```bash
uv run dbt build --project-dir fourcasters --select +ml_train_incendie
uv run python scripts/entrainer_ml_incendie.py
```

Le script affiche les dates de séparation, les volumes, l'accuracy, le F1 macro,
le rapport par classe, la matrice de confusion et l'importance des variables.
L'accuracy est comparée à une référence qui prédit toujours la classe la plus
fréquente dans l'apprentissage. Le modèle reste en mémoire : aucun modèle
n'est déployé ni enregistré automatiquement.

### Résultats du 11 septembre 2026

L'évaluation utilise 66 432 lignes issues de BigQuery. L'apprentissage contient
52 608 lignes jusqu'au 30 juin 2026. Les 13 440 lignes de test commencent le
3 juillet 2026 ; les 384 lignes des deux jours intermédiaires sont écartées.

| Indicateur | Résultat |
|---|---:|
| Accuracy du modèle | 52,59 % |
| Accuracy de la classe majoritaire | 32,35 % |
| Gain par rapport à la référence | 20,24 points |
| F1 macro | 0,311 |

Le modèle distingue correctement une partie des niveaux 1 et 2, avec des F1
respectifs de 0,49 et 0,63. Il reconnaît encore mal le niveau 3 (F1 de 0,10)
et le niveau 4 (F1 de 0,02). Une seule des 96 lignes de niveau 4 est bien
classée. L'accuracy globale est donc encourageante pour un prototype, mais
insuffisante pour une utilisation opérationnelle sur les dangers élevés.

Les trois premières importances sont l'humidité moyenne sur sept jours,
la température moyenne sur sept jours et le déficit maximal de pression de
vapeur sur sept jours. Elles décrivent l'utilisation faite par le modèle et
ne prouvent pas une relation de cause à effet.

## Limites

Le décalage de sept jours est une hypothèse de disponibilité. Il ne prouve pas
que la réanalyse téléchargée aujourd'hui était identique à celle connue au
moment de chaque bulletin. Cette évaluation est rétrospective. Un essai en
conditions réelles demanderait des données archivées telles qu'elles étaient
publiées et plusieurs périodes de validation.

Les niveaux 3 et 4 demandent davantage d'exemples et plusieurs périodes de
validation avant d'envisager une amélioration ou un réglage du modèle.

Références : [réanalyses Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api)
et [séparation temporelle dans scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split).
