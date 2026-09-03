# Fourcasters — Analyse météorologique et risque d'incendie

## Présentation

**Fourcasters** est un projet réalisé dans le cadre de la formation Data Analyst de la Wild Code School.

L'objectif est d'exploiter des données météorologiques historiques en France afin d'étudier les conditions climatiques et leur lien avec certains risques, notamment les fortes chaleurs, les précipitations et le danger d'incendie.

Le projet utilise deux sources principales :

- **Open-Meteo** pour les données météorologiques historiques ;
- **Météo-France** pour les niveaux de danger incendie de la Météo des forêts.

Les données sont collectées avec Python, stockées dans BigQuery puis transformées avec dbt pour être exploitées dans Power BI et dans de futurs travaux de Machine Learning.

## Sources de données

### Open-Meteo

- Source : API Open-Meteo Historical
- Modèle : `ERA5-Seamless`
- Granularité : une observation quotidienne par point géographique
- Historique initial : du 1er janvier 2000 au 31 juillet 2026
- Actualisation : une journée à la fois
- Décalage volontaire : J-6 pour attendre la disponibilité des données ERA5
- Zone étudiée : France métropolitaine
- Référentiel : 360 points d'observation

### Météo-France

- Source : API Météo des forêts
- Granularité : une prévision par département
- Zone étudiée : 96 départements de France métropolitaine
- Données : niveau de danger incendie à J1 et J2
- Historique 2026 initialisé à partir des archives Météo-France
- Actualisation quotidienne à partir de l'API

Ces données correspondent à un **niveau de danger incendie prévu** et non à des incendies réellement observés.

## Architecture

```text
Open-Meteo Historical API             Météo-France
        │                                  │
        ▼                                  ▼
actualiser_openmeteo.py        actualiser_meteofrance_incendie.py
        │                                  │
        ▼                                  ▼
openmeteo_raw                    meteofrance_raw
meteo_journaliere                 meteo_forets
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
                      dbt
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          staging  intermediate  marts
                                  │
                                  ▼
                               Power BI
```

Les scripts Python écrivent directement dans les tables RAW de BigQuery.

Aucun fichier CSV, Parquet ou table temporaire n'est nécessaire pour l'actualisation quotidienne.

## Modèle analytique

Le modèle dbt utilise une architecture en étoile.

### `dim_commune`

Dimension contenant les informations géographiques des 360 points d'observation Open-Meteo.

### `dim_departement`

Dimension contenant les départements utilisés pour les données Météo-France.

### `dim_date`

Dimension calendaire couvrant la période étudiée.

### `fact_meteo`

Table de faits contenant les observations météorologiques quotidiennes :

- températures et températures ressenties ;
- humidité et point de rosée ;
- précipitations, pluie et neige ;
- vitesse et direction du vent ;
- couverture nuageuse et pression atmosphérique ;
- ensoleillement et rayonnement solaire ;
- évapotranspiration ;
- déficit de pression de vapeur ;
- humidité et température du sol.

### `fact_danger_incendie`

Table de faits contenant les prévisions de danger incendie Météo-France.

Une ligne correspond à :

- un département ;
- une date de prévision ;
- une échéance `J1` ou `J2` ;
- un niveau de danger.

Cette structure permet de rapprocher plus facilement les niveaux de danger des données météorologiques correspondant à la même date.

## Organisation du projet

```text
Projet_Fourcasters/
├── .github/
│   └── workflows/
│       └── pipeline.yml
├── DOCUMENTATION/
├── fourcasters/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── seeds/
│   │   └── referentiel_communes.csv
│   ├── tests/
│   └── dbt_project.yml
├── scripts/
│   ├── actualiser_openmeteo.py
│   └── actualiser_meteofrance_incendie.py
├── .gitignore
├── .python-version
├── pyproject.toml
└── uv.lock
```

## Actualisation quotidienne

### Open-Meteo

```bash
uv run python scripts/actualiser_openmeteo.py
```

Le script :

1. cherche la dernière journée présente dans BigQuery ;
2. reprend une journée incomplète si nécessaire ;
3. récupère les communes manquantes auprès d'Open-Meteo ;
4. écrit directement les nouvelles lignes dans BigQuery ;
5. évite les doublons grâce à `row_hash`.

### Météo-France

```bash
uv run python scripts/actualiser_meteofrance_incendie.py
```

Le script :

1. récupère la publication courante de la Météo des forêts ;
2. prépare les données des 96 départements ;
3. vérifie les lignes déjà présentes ;
4. ajoute uniquement les nouvelles données dans BigQuery ;
5. évite les doublons grâce à `row_hash`.

## dbt

Tester la connexion :

```bash
uv run dbt debug --project-dir fourcasters
```

Construire l'ensemble du projet :

```bash
uv run dbt build --project-dir fourcasters
```

Construire uniquement la partie Open-Meteo :

```bash
uv run dbt build --project-dir fourcasters --select stg_meteo_journaliere+
```

Construire uniquement la partie Météo-France :

```bash
uv run dbt build --project-dir fourcasters --select stg_meteo_forets+
```

## Contrôles

Le pipeline vérifie notamment :

- la présence des points géographiques attendus ;
- l'unicité des lignes avec `row_hash` ;
- l'absence de valeurs nulles sur les colonnes essentielles ;
- les relations entre les tables de faits et les dimensions ;
- les valeurs possibles des niveaux de danger incendie ;
- les échéances `J1` et `J2`.

Les requêtes de contrôle BigQuery sont conservées dans :

```text
DOCUMENTATION/CONTROLES_BIGQUERY_FOURCASTERS.sql
```

## Automatisation

Le workflow GitHub Actions :

1. récupère le dépôt ;
2. s'authentifie auprès de Google Cloud ;
3. installe les dépendances avec `uv` ;
4. actualise les données Open-Meteo ;
5. actualise les données Météo-France ;
6. reconstruit et teste les modèles dbt.

## Sécurité

Les éléments sensibles ne doivent jamais être ajoutés au dépôt :

- clés de comptes de service Google Cloud ;
- clés API ;
- fichiers `.env` ;
- `profiles.yml` ;
- secrets GitHub Actions.

## Auteur

**MARTIN Loïck**

Projet de fin de formation Data Analyst — Wild Code School