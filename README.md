# Fourcasters — Analyse météorologique avec Open-Meteo et dbt

## Présentation

**Fourcasters** est un projet réalisé dans le cadre de la formation Data Analyst de la Wild Code School.

L’objectif est d’exploiter des données météorologiques historiques en France afin d’étudier les conditions climatiques et de préparer des analyses liées notamment aux fortes chaleurs, aux précipitations et au risque d’incendie.

Les données sont collectées avec Python, stockées dans BigQuery puis transformées avec dbt pour être exploitées dans Power BI et dans de futurs travaux de Machine Learning.

## Données Open-Meteo

* Source : API Open-Meteo Historical
* Modèle : `ERA5-Seamless`
* Granularité : une observation quotidienne par point géographique
* Historique initial : du 1er janvier 2000 au 31 juillet 2026
* Actualisation : une journée à la fois
* Décalage volontaire : J-6 pour attendre la disponibilité des données ERA5
* Zone étudiée : France métropolitaine
* Référentiel : 360 points d’observation

## Architecture

```text
Open-Meteo Historical API
        │
        ▼
scripts/actualiser_openmeteo.py
        │
        ▼
BigQuery
openmeteo_raw.meteo_journaliere
        │
        ▼
dbt
        │
        ├── staging
        ├── intermediate
        └── marts
                │
                ▼
             Power BI
```

Le script Python écrit directement dans la table historique BigQuery.

Aucun fichier CSV, Parquet ou table temporaire n’est nécessaire pour l’actualisation quotidienne.

## Modèle analytique

Le modèle dbt utilise une architecture en étoile.

### `dim_commune`

Dimension contenant les informations géographiques des 360 points d’observation.

### `dim_date`

Dimension calendaire couvrant toute la période météorologique.

### `fact_meteo`

Table de faits contenant les observations météorologiques quotidiennes :

* températures et températures ressenties ;
* humidité et point de rosée ;
* précipitations, pluie et neige ;
* vitesse et direction du vent ;
* couverture nuageuse et pression atmosphérique ;
* ensoleillement et rayonnement solaire ;
* évapotranspiration ;
* déficit de pression de vapeur ;
* humidité et température du sol.

## Organisation du projet

```text
Projet_Fourcasters/
├── .github/
│   └── workflows/
│       └── pipeline.yml
├── DOCUMENTATION/
├── fourcasters/
│   ├── models/
│   ├── seeds/
│   │   └── referentiel_communes.csv
│   ├── tests/
│   └── dbt_project.yml
├── scripts/
│   └── actualiser_openmeteo.py
├── .gitignore
├── .python-version
├── pyproject.toml
└── uv.lock
```

## Actualisation quotidienne

Le script récupère automatiquement la prochaine journée disponible.

```bash
uv run python scripts/actualiser_openmeteo.py
```

Il :

1. cherche la dernière journée présente dans BigQuery ;
2. reprend une journée incomplète si nécessaire ;
3. récupère les communes manquantes auprès d’Open-Meteo ;
4. écrit directement les nouvelles lignes dans BigQuery ;
5. évite les doublons grâce à `row_hash`.

## dbt

Tester la connexion :

```bash
uv run dbt debug --project-dir fourcasters
```

Construire les modèles :

```bash
uv run dbt build --project-dir fourcasters
```

Construire uniquement la partie météo :

```bash
uv run dbt build --project-dir fourcasters --select stg_meteo_journaliere+
```

## Contrôles

Le pipeline vérifie notamment :

* la présence des 360 communes ;
* l’unicité des lignes avec `row_hash` ;
* l’absence de valeurs nulles sur les colonnes essentielles ;
* les relations entre la table de faits et les dimensions.

Les requêtes de contrôle BigQuery sont conservées dans :

```text
DOCUMENTATION/CONTROLES_BIGQUERY_FOURCASTERS.sql
```

## Automatisation

Le workflow GitHub Actions :

1. récupère le dépôt ;
2. s’authentifie auprès de Google Cloud ;
3. installe les dépendances avec `uv` ;
4. lance l’actualisation Open-Meteo ;
5. reconstruit les modèles dbt.

## Sécurité

Les éléments sensibles ne doivent jamais être ajoutés au dépôt :

* clés de comptes de service Google Cloud ;
* fichiers `.env` ;
* `profiles.yml` ;
* secrets GitHub Actions.

## Auteur

**MARTIN Loïck**

Projet de fin de formation Data Analyst — Wild Code School
