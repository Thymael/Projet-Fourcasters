# Fourcasters

Projet de fin de formation Data Analyst à la Wild Code School.

Fourcasters rapproche des données météo historiques et les niveaux de danger de la **Météo des forêts** en France métropolitaine. Le projet couvre toute la chaîne vue pendant la formation : collecte Python, stockage dans Google Cloud et BigQuery, transformations dbt, analyse exploratoire en Python, Power BI et un premier modèle de Machine Learning présenté avec Streamlit.

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
        Parquet
          ↓
 Google Cloud Storage
          ↓
       BigQuery
          ↓
          dbt
      ↙    ↓    ↘
   EDA   Power BI   Machine Learning
                     ↓
                pipeline.pkl
                     ↓
                 Streamlit
```

La collecte quotidienne et le ML sont volontairement séparés : GitHub Actions actualise les données et lance dbt, tandis que l'entraînement du modèle est lancé à la demande.

## Prérequis

- Python **3.12** ;
- `uv` pour gérer l'environnement Python ;
- un projet Google Cloud avec accès à BigQuery et Cloud Storage ;
- une clé API Météo-France ;
- des identifiants Google Cloud utilisables en local ou via ADC.

## Installation

Installer les dépendances principales :

```bash
uv sync
```

Pour travailler dans les notebooks :

```bash
uv sync --group analyse
```

Pour utiliser Streamlit :

```bash
uv sync --group app
```

Créer ensuite le fichier `.env` à partir de `.env.example` et renseigner notamment la clé API Météo-France.

Pour dbt :

```bash
mkdir -p ~/.dbt
cp fourcasters/profiles.example.yml ~/.dbt/profiles.yml
```

## Utilisation

Actualiser les deux sources :

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

Construire les modèles et lancer les tests dbt :

```bash
uv run dbt build --project-dir fourcasters
```

Lancer les notebooks :

```bash
uv run --group analyse jupyter notebook
```

Lancer Streamlit :

```bash
uv run python -m streamlit run streamlit_app.py
```

L'application contient trois vues simples :

- **Prédictions** : le modèle part de la dernière date météo complète disponible et calcule J+1 et J+2 ;
- **Cas historique** : comparaison ponctuelle entre une prédiction et le niveau officiel Météo-France ;
- **Méthode et limites** : rappel du périmètre et des précautions d'usage.

Exemple de lecture : si la dernière météo complète est datée du 1er octobre, J+1 correspond au 2 octobre et J+2 au 3 octobre. L'application ne tente jamais de prédire à partir de la date civile du jour.

## Structure du projet

```text
Projet_Fourcasters/
├── .github/workflows/pipeline.yml
├── DOCUMENTATION/
├── fourcasters/              # projet dbt
├── notebooks/                # EDA Python
├── scripts/                  # scripts à lancer
├── src/fourcasters_dbt/      # fonctions Python
├── tests/                    # tests Python
├── pipeline.pkl              # modèle ML entraîné
├── streamlit_app.py          # prédictions J+1/J+2 et cas historique
├── SOUTENANCE.md             # déroulé oral de 15 minutes et checklist
├── pyproject.toml
├── uv.lock
└── README.md
```

## Analyse exploratoire

Deux notebooks servent à comprendre les données avant Power BI :

- `notebooks/EDA Météo.ipynb` : qualité, statistiques, saisonnalité, territoires, corrélations et journées extrêmes ;
- `notebooks/EDA Incendies.ipynb` : qualité des publications Météo-France, répartition des niveaux, saisonnalité, territoires et comparaison J1/J2.

L'analyse est faite principalement avec **Pandas** et **Matplotlib**.

## dbt

Les modèles suivent trois niveaux simples :

- **staging** : nettoyage des sources ;
- **intermediate** : enrichissements et agrégations ;
- **marts** : tables finales pour l'analyse, Power BI et le ML.

Les tables ML sont séparées :

- `ml_features_incendie` prépare les variables météo sans cible ;
- `ml_train_incendie` ajoute le niveau Météo-France utilisé comme cible ;

## Power BI

Power BI sert à analyser la météo et les niveaux de danger. Il utilise principalement la table `pbi_risque_incendie` préparée par dbt dans BigQuery.

Le Machine Learning n'est pas exécuté dans Power BI.

La documentation utilisateur est disponible dans [DOCUMENTATION/GUIDE_POWER_BI.md](DOCUMENTATION/GUIDE_POWER_BI.md).
Le support final se trouve dans `DOCUMENTATION/Fourcasters_Soutenance_15min.pptx`.

## Machine Learning

Le modèle principal est un **Random Forest** avec un Pipeline scikit-learn :

```text
SimpleImputer → RandomForestClassifier
```

La cible est le **niveau de danger incendie Météo-France (Météo des forêts)**, codé de 1 à 4. Dans le projet, les expressions « niveau de danger » et « risque d'incendie » renvoient à cette même référence officielle ; le modèle ne prédit pas un départ de feu réel.

Le découpage final est temporel :
- les cibles **2024 et 2025** servent à l'apprentissage ;
- les cibles **2026 jusqu'au 2 octobre inclus** servent au test ;
- aucune cible 2026 n'est utilisée pendant l'apprentissage ;
- toute cible postérieure au **02/10/2026** est exclue du split final.

### Repère temporel

**J** désigne la date de référence disposant des données météo nécessaires. Ce repère n'est donc pas automatiquement la date civile du jour : avec le décalage ERA5-Seamless, la dernière journée météo éligible se situe actuellement six jours avant la date d'exécution.

Le modèle utilise les **7 jours météo de J-6 à J inclus** :
- l'horizon 1 cible **J+1** ;
- l'horizon 2 cible **J+2** ;
- les deux horizons utilisent la même fenêtre J-6 → J et la variable `horizon_jours` les distingue.

La collecte Open-Meteo ne télécharge pas cette fenêtre de sept jours à chaque exécution : elle récupère **une seule journée manquante ou incomplète**. La fenêtre de sept jours est construite ensuite dans dbt à partir de l'historique déjà stocké.

### Entraînement final

Entraîner et enregistrer le modèle :

```bash
uv run python scripts/entrainer_ml_incendie.py
```

Le script crée `pipeline.pkl` à la racine du projet et affiche les effectifs exacts, les périodes, l'accuracy, la référence naïve, le F1 macro, le rapport par classe et la matrice de confusion.

Le jeu final contient **67 584 observations** :

- **46 080** lignes pour l'apprentissage 2024-2025 ;
- **21 504** lignes pour le test 2026 jusqu'au 2 octobre inclus.

Sur ce test, le Random Forest atteint **64,35 % d'accuracy** et **0,417 de F1 macro**. La référence naïve atteint **42,28 % d'accuracy**. Ces résultats décrivent un prototype pédagogique : les niveaux 3 et 4 restent nettement moins bien reconnus.

La référence naïve utilise `DummyClassifier(strategy="most_frequent")` : la classe majoritaire est **apprise uniquement sur le jeu d'entraînement 2024-2025**, puis appliquée au test 2026. Elle ne doit pas être décrite comme la classe majoritaire du jeu de test.

Comparer tous les modèles sur exactement le même split :

```bash
uv run python scripts/comparer_modeles_ml.py
```

Les scripts réaffichent ces mesures après chaque nouvel entraînement afin d'éviter de conserver des chiffres provenant d'une ancienne version du jeu de données.

### Empreinte carbone

Mesurer ponctuellement l'impact du **modèle final** avec CodeCarbon :

```bash
uv run --group analyse python scripts/mesurer_co2_ml.py
```

La mesure réalisée sur le modèle final est d'environ **0,0000026 kg CO2e**, soit **0,003 g CO2e** après arrondi. Elle donne un ordre de grandeur propre à cette exécution et à cette machine.

## Tests

Tests Python :

```bash
uv run pytest -q
```

Tests et modèles dbt :

```bash
uv run dbt build --project-dir fourcasters
```

Contrôle de la structure dbt :

```bash
uv run dbt parse --project-dir fourcasters
```

## Automatisation

`.github/workflows/pipeline.yml` exécute chaque jour :

1. Open-Meteo ;
2. Météo-France ;
3. les tables BigQuery ;
4. les modèles et tests dbt.

Open-Meteo récupère une seule journée manquante par exécution, avec un décalage de six jours. La collecte Météo-France s'arrête après la fin de la saison 2026, fixée au 2 octobre dans le projet. Le modèle ML n'est pas réentraîné chaque jour.

## Documentation

Les principaux documents du projet sont :

- [Schéma des données](DOCUMENTATION/SCHEMA_DONNEES.md) ;
- [Dictionnaire de données](DOCUMENTATION/DICTIONNAIRE_DONNEES.md) ;
- [Guide utilisateur Power BI](DOCUMENTATION/GUIDE_POWER_BI.md) ;
- [Index de la documentation](DOCUMENTATION/README.md) ;
- `DOCUMENTATION/CONTROLES_BIGQUERY_FOURCASTERS.sql` pour les contrôles manuels ;
- l'audit de sobriété ;
- la note de vigilance éthique ;
- la réflexion sur la dépendance technologique ;
- le point sur l'AI Act ;
- la matrice courte des risques au format Excel.

Les descriptions et tests des modèles sont également présents dans les fichiers YAML de dbt.

## Équipe et contact

Projet initialisé en groupe puis poursuivi individuellement dans le cadre de la formation Data Analyst : Angèle T., Christophe L., Eddy H. et Loïck M.

Pour une question ou un problème sur le projet, utiliser les **Issues du dépôt GitHub**.
