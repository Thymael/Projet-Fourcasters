# Fourcasters

Projet de fin de formation Data Analyst à la Wild Code School.

Fourcasters rapproche des données météo historiques et les niveaux de danger de la **Météo des forêts** en France métropolitaine. Le projet couvre toute la chaîne vue pendant la formation : collecte Python, stockage dans Google Cloud et BigQuery, transformations dbt, analyse, Power BI et un premier modèle de Machine Learning présenté avec Streamlit.

> Le modèle ML cherche à reproduire un niveau de danger Météo-France. Il ne prédit pas les départs de feu réels et ne doit pas être utilisé comme outil opérationnel.

## Données

| Source | Contenu | Grain |
| --- | --- | --- |
| Open-Meteo / ERA5-Seamless | Données météorologiques historiques | 1 point géographique × 1 jour |
| Météo-France | Niveau de danger J1 et J2 | 1 département × 1 publication × 1 échéance |

Le référentiel contient **360 points** répartis en France métropolitaine. Les données Météo-France couvrent **96 départements**.

## Architecture

```text
Open-Meteo + Météo-France
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
       ↙      ↘
 Power BI   Machine Learning
               ↓
          pipeline.pkl
               ↓
           Streamlit
```

La collecte quotidienne et le ML sont volontairement séparés : GitHub Actions actualise les données et lance dbt, tandis que l'entraînement du modèle est lancé à la demande.

## Dossiers principaux

```text
Projet_Fourcasters/
├── .github/workflows/pipeline.yml
├── DOCUMENTATION/
├── fourcasters/              # projet dbt
├── notebooks/                # EDA
├── scripts/                  # scripts à lancer
├── src/fourcasters_dbt/      # fonctions Python
├── tests/                    # tests Python
├── streamlit_app.py          # démonstration du modèle
├── pyproject.toml
└── README.md
```

## Installation

Le projet utilise Python 3.12 et `uv`.

```bash
uv sync
```

Créer ensuite le fichier `.env` à partir de `.env.example` et renseigner :

- la clé API Météo-France ;
- les identifiants Google Cloud si nécessaire en local.

Pour dbt :

```bash
mkdir -p ~/.dbt
cp fourcasters/profiles.example.yml ~/.dbt/profiles.yml
```

## Actualiser les données

Les deux sources :

```bash
uv run python scripts/actualiser_fourcasters.py
```

Open-Meteo uniquement :

```bash
uv run python scripts/actualiser_fourcasters.py --openmeteo-only
```

Météo-France uniquement :

```bash
uv run python scripts/actualiser_fourcasters.py --incendie-only
```

Test local de Météo-France sans chargement Cloud :

```bash
uv run python scripts/actualiser_fourcasters.py --incendie-only --local-only
```

L'import des archives Météo-France est séparé du pipeline quotidien :

```bash
uv run python scripts/importer_archives_meteofrance.py --annees 2024 2025 2026
```

## dbt

```bash
uv run dbt build --project-dir fourcasters
```

Les modèles suivent trois niveaux simples :

- **staging** : nettoyage des sources ;
- **intermediate** : enrichissements et agrégations ;
- **marts** : tables finales pour l'analyse, Power BI et le ML.

Les tables ML sont volontairement séparées :

- `ml_features_incendie` prépare les variables météo sans cible ;
- `ml_train_incendie` ajoute ensuite le niveau Météo-France utilisé comme cible.

## Machine Learning

Le modèle principal est un **Random Forest**. Il utilise un Pipeline scikit-learn :

```text
SimpleImputer → RandomForestClassifier
```

Le découpage est chronologique : les dates les plus anciennes servent au train et les 20 % de dates les plus récentes au test. Deux jours sont laissés entre les deux périodes pour tenir compte des horizons J1 et J2.

Entraîner et enregistrer le modèle :

```bash
uv run python scripts/entrainer_ml_incendie.py
```

Le script crée `pipeline.pkl` à la racine du projet. Ce fichier contient le prétraitement et le modèle entraîné.

Résultats obtenus lors du dernier test :

| Modèle | Accuracy | F1 macro |
| --- | ---: | ---: |
| Classe majoritaire | 38,43 % | — |
| Régression logistique | 29,06 % | 0,253 |
| Arbre de décision | 37,46 % | 0,275 |
| Random Forest | **55,51 %** | **0,338** |

Les niveaux 3 et 4 sont encore mal reconnus. Le modèle reste donc un prototype.

Comparer les modèles :

```bash
uv run python scripts/comparer_modeles_ml.py
```

Mesurer ponctuellement l'impact de l'entraînement avec CodeCarbon :

```bash
uv run --group analyse python scripts/mesurer_co2_ml.py
```

## Streamlit

Streamlit sert uniquement à présenter le modèle ML de façon interactive. L'application utilise la période de test et compare la prédiction du modèle avec le niveau officiel Météo-France.

Ajouter Streamlit une première fois avec `uv`, puis lancer l'application :

```bash
uv add --group app streamlit
uv run streamlit run streamlit_app.py
```

La première commande ajoute Streamlit au projet et met à jour `uv.lock`. Elle n'est à faire qu'une fois.

Il faut avoir créé `pipeline.pkl` auparavant avec le script d'entraînement.

## Power BI

Power BI reste la couche de visualisation du projet pour l'analyse météo et le danger incendie. Il lit les tables préparées par dbt dans BigQuery.

Le ML n'est pas exécuté dans Power BI : la démonstration du modèle est faite dans Streamlit.

## Tests

Tests Python :

```bash
uv run pytest -q
```

Tests et modèles dbt :

```bash
uv run dbt build --project-dir fourcasters
```

Contrôle rapide de la structure dbt :

```bash
uv run dbt parse --project-dir fourcasters
```

## Automatisation

`.github/workflows/pipeline.yml` actualise chaque jour :

1. Open-Meteo ;
2. Météo-France ;
3. les tables BigQuery ;
4. les modèles et tests dbt.

Le modèle ML n'est pas réentraîné chaque jour. L'entraînement reste volontairement manuel pour ce projet étudiant.

## Documentation

Le dossier `DOCUMENTATION/` contient :

- les requêtes de contrôle BigQuery ;
- l'audit de sobriété ;
- la note de vigilance éthique ;
- la réflexion sur la dépendance technologique ;
- le point sur l'AI Act.

## Équipe

Projet initialisé en groupe puis poursuivi individuellement dans le cadre de la formation Data Analyst : Angèle T., Christophe L., Eddy H. et Loïck M.
