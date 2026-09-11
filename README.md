# Fourcasters

[![Actualisation quotidienne](https://github.com/Thymael/Projet-Fourcasters/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Thymael/Projet-Fourcasters/actions/workflows/pipeline.yml)

Projet de fin de formation Data Analyst à la Wild Code School.

Fourcasters rapproche la météo historique et le danger d'incendie en France
métropolitaine. Les données servent à l'analyse exploratoire, à Power BI et à
un premier modèle de classification.

## Données utilisées

| Source | Contenu | Une ligne représente |
|---|---|---|
| Open-Meteo, ERA5-Seamless | Météo historique reconstituée par réanalyse | un point et un jour, sur 360 points |
| Météo-France, API et archives depuis 2024 | Danger prévu à J1 et J2 | un département et un horodatage de publication, sur 96 départements |

Le niveau Météo-France va de 1 à 4. Il indique un **danger prévu**, sans
recenser les départs de feu. Les archives incendie sont saisonnières.

Open-Meteo reconstitue la météo à partir de modèles et d'observations. Les
360 points ne sont donc pas 360 stations de mesure. Le pipeline garde six
jours de recul avant de demander une nouvelle journée.
[Documentation Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api).

## Organisation

| Dossier | Contenu |
|---|---|
| `scripts/` | les trois commandes à lancer |
| `src/fourcasters_dbt/` | collecte, contrôles, chargement et ML |
| `fourcasters/` | référentiel, modèles SQL et tests dbt |
| `tests/` | tests Python sans API ni accès cloud |
| `notebooks/` | analyse exploratoire |
| `DOCUMENTATION/` | modèle Power BI, méthode ML, contrôles et bilan |

Les fichiers passent de Python à Cloud Storage, puis aux tables de réception
BigQuery. Après validation, un `MERGE` met à jour l'historique. dbt construit
ensuite les dimensions, les tables de faits et les tables Power BI/ML.

## Installation

Prérequis : Python 3.12, `uv`, un accès au projet Google Cloud et une clé API
Météo-France. Les tables historiques Open-Meteo doivent déjà exister : le
script quotidien reprend à partir du 1er août 2026 et ne recrée pas l'import
initial 2000–juillet 2026.

Depuis la racine du projet, dans Git Bash :

```bash
uv sync --frozen
cp .env.example .env
mkdir -p ~/.dbt
cp fourcasters/profiles.example.yml ~/.dbt/profiles.yml
```

Renseigner `.env` avec le chemin de la clé Google et la clé Météo-France.
Une identité Google ADC déjà configurée peut aussi être utilisée. Le profil
dbt reprend la région **US** du projet existant. Le changer ne déplace pas
les données.

## Commandes

```bash
# Collecter les deux sources et charger BigQuery
uv run python scripts/actualiser_fourcasters.py

# Reconstruire les tables d'analyse et exécuter les tests dbt
uv run dbt build --project-dir fourcasters

# Collecter une seule source
uv run python scripts/actualiser_fourcasters.py --openmeteo-only
uv run python scripts/actualiser_fourcasters.py --incendie-only

# Vérifier l'API incendie et produire un Parquet local, sans écrire dans Google Cloud
uv run python scripts/actualiser_fourcasters.py --incendie-only --local-only

# Import ponctuel des archives (pas besoin de le relancer chaque jour)
uv run python scripts/importer_archives_meteofrance.py --annees 2024 2025 2026

# Entraîner et évaluer le modèle
uv run python scripts/entrainer_ml_incendie.py
```

Pour préparer les archives sans envoi dans Google Cloud, ajouter `--local-only`.
Open-Meteo recherche la première journée manquante ou incomplète et rattrape
jusqu'à sept journées par exécution. Les CSV locaux permettent de reprendre
une collecte interrompue. Sur GitHub Actions, ces fichiers locaux ne sont
pas conservés entre deux exécutions.

Ne pas lancer deux collectes identiques simultanément depuis le PC et GitHub :
elles utilisent la même table de réception. Les exécutions du workflow
quotidien sont mises en file d'attente entre elles.

## Analyse et Power BI

Pour utiliser le notebook :

```bash
uv sync --frozen --group analyse
uv run jupyter notebook notebooks/01_eda_fourcasters.ipynb
```

Le PBIX fourni contient cinq pages. Les noms de ses tables, colonnes et mesures
sont conservés. Voir le [modèle Power BI](DOCUMENTATION/MODELE_POWERBI.md)
et la [méthode ML](DOCUMENTATION/ML_INCENDIE.md).

## Vérifications et automatisation

```bash
uv run pytest -q
uv run dbt parse --project-dir fourcasters
git diff --check
```

`dbt parse` vérifie le projet sans exécuter de SQL dans BigQuery. `dbt build`
reconstruit les tables et contrôle leurs données ; il demande les accès cloud.

- `tests.yml` vérifie Python et dbt sur les pull requests et les mises à jour de `main`.
- `pipeline.yml` collecte les données puis lance `dbt build`, chaque jour à 4 h,
  heure de Paris, ou à la demande dans l'onglet Actions.
- Les secrets attendus sont `GCP_SA_KEY` et `METEOFRANCE_API_KEY`.

Les logs indiquent l'heure, le niveau et l'étape. Une erreur arrête le script
avec un code de sortie non nul. La collecte est incrémentale ; les tables
finales dbt restent reconstruites entièrement pour garder leur logique simple.

Les [contrôles SQL](DOCUMENTATION/CONTROLES_BIGQUERY_FOURCASTERS.sql) complètent
les tests. Le [bilan de l'harmonisation](DOCUMENTATION/BILAN_HARMONISATION.md)
distingue les changements vérifiés localement des vérifications cloud restantes.

## Équipe

Angèle, Christophe, Eddy et Loïck. Dépôt du pipeline météo et danger incendie
maintenu par Loïck Martin.
