# Fourcasters

[![Actualisation quotidienne](https://github.com/Thymael/Projet-Fourcasters/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Thymael/Projet-Fourcasters/actions/workflows/pipeline.yml)

Projet de fin de formation Data Analyst à la Wild Code School.

Fourcasters rapproche des données météorologiques historiques et le niveau de danger incendie en France métropolitaine.

Le projet permet de travailler sur plusieurs parties vues pendant la formation :

* collecte de données ;
* Python ;
* BigQuery ;
* dbt ;
* tests ;
* automatisation avec GitHub Actions ;
* analyse exploratoire ;
* Power BI ;
* premier modèle de Machine Learning.

## Données utilisées

| Source                     | Contenu                                 | Une ligne représente                            |
| -------------------------- | --------------------------------------- | ----------------------------------------------- |
| Open-Meteo / ERA5-Seamless | Données météorologiques historiques     | un point géographique et un jour                |
| Météo-France               | Niveau de danger de la Météo des forêts | un département, une publication et une échéance |

Le projet utilise 360 points répartis en France métropolitaine.

Les données Open-Meteo utilisées sont des données issues de réanalyses. Les 360 points ne correspondent donc pas à 360 stations météorologiques physiques.

Pour le danger incendie, Météo-France fournit quatre niveaux de danger à J1 et J2 pour les 96 départements métropolitains.

Ces niveaux représentent un **danger prévu** et non les départs de feu réellement observés.

## Organisation du projet

```text
Projet_Fourcasters/
│
├── .github/
│   └── workflows/
│       ├── pipeline.yml
│       └── tests.yml
│
├── DOCUMENTATION/
│   ├── CONTROLES_BIGQUERY_FOURCASTERS.sql
│   ├── Dépendance technologique.md
│   ├── Face à l'IA Act.md
│   ├── L'audit de sobriété.md
│   ├── La note de vigilance éthique.md
│   └── Machine Learning.md
│
├── fourcasters/
│   ├── models/
│   ├── seeds/
│   └── tests/
│
├── notebooks/
│   └── 01_eda_fourcasters.ipynb
│
├── scripts/
│   ├── actualiser_fourcasters.py
│   ├── importer_archives_meteofrance.py
│   ├── entrainer_ml_incendie.py
│   ├── comparer_modeles_ml.py
│   └── mesurer_co2_ml.py
│
├── src/
│   └── fourcasters_dbt/
│
├── tests/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

### Rôle des principaux dossiers

| Dossier                | Utilité                                     |
| ---------------------- | ------------------------------------------- |
| `scripts/`             | commandes principales du projet             |
| `src/fourcasters_dbt/` | fonctions Python utilisées par les scripts  |
| `fourcasters/`         | projet dbt, modèles SQL, seeds et tests dbt |
| `tests/`               | tests Python                                |
| `notebooks/`           | analyse exploratoire                        |
| `DOCUMENTATION/`       | documents complémentaires du projet         |

## Fonctionnement général

Le pipeline suit globalement les étapes suivantes :

```text
API
↓
Python
↓
CSV / Parquet temporaire
↓
Google Cloud Storage
↓
BigQuery
↓
dbt
↓
Power BI / Machine Learning
```

Les fichiers intermédiaires permettent notamment de contrôler les données avant de modifier les tables historiques.

## Installation

Le projet utilise Python 3.12 et `uv`.

Depuis la racine du projet :

```bash
uv sync --frozen
```

Créer ensuite le fichier `.env` à partir de l'exemple :

```bash
cp .env.example .env
```

Puis renseigner les accès nécessaires :

* Google Cloud ;
* API Météo-France.

Pour dbt :

```bash
mkdir -p ~/.dbt
cp fourcasters/profiles.example.yml ~/.dbt/profiles.yml
```

Le projet BigQuery utilise actuellement la région `US`.

## Actualisation des données

Pour lancer les deux collectes :

```bash
uv run python scripts/actualiser_fourcasters.py
```

Pour lancer uniquement Open-Meteo :

```bash
uv run python scripts/actualiser_fourcasters.py --openmeteo-only
```

Pour lancer uniquement Météo-France :

```bash
uv run python scripts/actualiser_fourcasters.py --incendie-only
```

Il est également possible de tester la collecte Météo-France sans envoyer les données dans Google Cloud :

```bash
uv run python scripts/actualiser_fourcasters.py --incendie-only --local-only
```

Open-Meteo recherche la première journée absente ou incomplète dans BigQuery.

Un décalage volontaire de six jours est conservé avant de récupérer une nouvelle journée.

La collecte est réalisée par lots de communes et peut reprendre à partir d'un CSV temporaire si elle est interrompue.

## Archives Météo-France

L'import des anciennes données Météo-France est séparé du pipeline quotidien.

```bash
uv run python scripts/importer_archives_meteofrance.py --annees 2024 2025 2026
```

Ce script n'a normalement pas besoin d'être exécuté chaque jour.

## dbt

Après la collecte, dbt prépare les données utilisées pour l'analyse, Power BI et le Machine Learning.

```bash
uv run dbt build --project-dir fourcasters
```

Le projet contient notamment :

* des modèles de staging ;
* des tables intermédiaires ;
* des dimensions ;
* des tables de faits ;
* des tables préparées pour Power BI ;
* des tables préparées pour le Machine Learning.

Les tests dbt sont exécutés pendant le `dbt build`.

## Machine Learning

Le projet contient un premier modèle permettant d'essayer de reproduire le niveau de danger Météo-France.

Le modèle principal est un Random Forest.

Pour l'entraîner :

```bash
uv run python scripts/entrainer_ml_incendie.py
```

Lors du test réalisé le 11 septembre 2026 :

| Indicateur             | Résultat |
| ---------------------- | -------: |
| Accuracy Random Forest |  52,59 % |
| Classe majoritaire     |  32,35 % |
| F1 macro               |    0,311 |

Le modèle fonctionne surtout sur les niveaux 1 et 2.

Les niveaux 3 et 4 restent difficiles à reconnaître. Il s'agit donc uniquement d'un prototype et non d'un modèle destiné à une utilisation opérationnelle.

### Comparaison avec des modèles plus simples

Un script permet de comparer le Random Forest avec plusieurs modèles plus simples :

```bash
uv run python scripts/comparer_modeles_ml.py
```

Résultats obtenus :

| Modèle                |    Accuracy |  F1 macro |
| --------------------- | ----------: | --------: |
| Classe majoritaire    |     32,35 % |     0,122 |
| Régression logistique |     29,06 % |     0,253 |
| Arbre de décision     |     37,46 % |     0,275 |
| Random Forest         | **52,59 %** | **0,311** |

Le Random Forest a donc été conservé comme modèle principal.

## Sobriété du Machine Learning

CodeCarbon a été utilisé ponctuellement pour mesurer l'impact de l'entraînement.

```bash
uv run --group analyse python scripts/mesurer_co2_ml.py
```

La mesure réalisée le 11 septembre 2026 a donné environ :

```text
0,000002 kg de CO2
```

Cette valeur reste une estimation dépendante de la machine et du contexte d'exécution.

## Analyse exploratoire

Le notebook principal se trouve dans :

```text
notebooks/01_eda_fourcasters.ipynb
```

Pour le lancer :

```bash
uv sync --frozen --group analyse
uv run jupyter notebook notebooks/01_eda_fourcasters.ipynb
```

## Power BI

Power BI utilise les tables préparées dans BigQuery par dbt.

Le rapport final contient cinq pages autour :

* de la météo générale ;
* des territoires ;
* de l'évolution temporelle ;
* du danger incendie ;
* du détail par département.

Les données météo et incendie n'ont pas la même granularité.

La météo est disponible par point géographique et par jour, tandis que le danger incendie est fourni au niveau du département.

## Tests

Les tests Python peuvent être lancés avec :

```bash
uv run pytest -q
```

Le dossier `tests/` contrôle principalement :

* Open-Meteo ;
* les appels HTTP ;
* les archives Météo-France ;
* la collecte incendie ;
* le Machine Learning.

Le dossier `fourcasters/tests/` contient les tests SQL spécifiques à dbt.

Pour vérifier uniquement la structure du projet dbt :

```bash
uv run dbt parse --project-dir fourcasters
```

## Automatisation

Deux workflows GitHub Actions sont utilisés.

### Actualisation quotidienne

`pipeline.yml` lance automatiquement :

1. la collecte Open-Meteo ;
2. la collecte Météo-France ;
3. le chargement dans Google Cloud et BigQuery ;
4. le `dbt build`.

Le workflow peut également être lancé manuellement depuis GitHub.

### Vérification du projet

`tests.yml` est lancé lors des Pull Requests et des modifications de `main`.

Il exécute :

```text
pytest
dbt parse
```

Il permet de détecter rapidement une erreur dans le code ou dans le projet dbt sans modifier les données BigQuery.

## Documentation complémentaire

Le dossier `DOCUMENTATION/` contient notamment :

* un audit de sobriété numérique ;
* une note de vigilance éthique ;
* une réflexion sur la dépendance technologique ;
* un point sur l'IA Act ;
* les résultats de comparaison des modèles de Machine Learning ;
* des requêtes de contrôle BigQuery.

## Équipe

Projet réalisé par :

* Angèle ;
* Christophe ;
* Eddy ;
* Loïck.

Projet développé dans le cadre de la formation Data Analyst de la Wild Code School.
