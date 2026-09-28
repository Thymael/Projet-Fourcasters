"""Modèle utilisé par le simulateur météo de l'application Streamlit."""

import logging
from pathlib import Path

import joblib
import pandas as pd
from google.cloud import bigquery
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

from fourcasters_dbt.configuration import (
    DATASET_ANALYSE,
    PROJET_GCP,
    RACINE_PROJET,
    configurer_google_cloud,
)

logger = logging.getLogger(__name__)

TABLE_ML_SIMULATION = (
    f"{PROJET_GCP}.{DATASET_ANALYSE}.ml_train_simulation_incendie"
)
FICHIER_PIPELINE_SIMULATION = RACINE_PROJET / "pipeline_simulation.pkl"
COLONNE_CIBLE_SIMULATION = "cible_niveau_danger"

COLONNES_CONTEXTE_SIMULATION = [
    "date_meteo",
    "numero_departement",
    "departement",
    "code_insee",
    "commune",
]

COLONNES_MODELE_SIMULATION = [
    "horizon_jours",
    "latitude",
    "longitude",
    "temperature_moyenne",
    "temperature_maximale",
    "humidite_moyenne",
    "precipitations",
    "rafale_vent_maximale",
    "deficit_pression_vapeur_maximal",
]


def charger_donnees_simulation() -> pd.DataFrame:
    """Charge le jeu d'apprentissage du simulateur depuis BigQuery."""
    configurer_google_cloud()
    client = bigquery.Client(project=PROJET_GCP)
    colonnes = ", ".join(
        [
            *COLONNES_CONTEXTE_SIMULATION,
            *COLONNES_MODELE_SIMULATION,
            COLONNE_CIBLE_SIMULATION,
        ]
    )
    requete = f"""
        SELECT {colonnes}
        FROM `{TABLE_ML_SIMULATION}`
        ORDER BY date_meteo, code_insee, horizon_jours
    """
    return client.query(requete).to_dataframe(
        create_bqstorage_client=False
    )


def preparer_donnees_simulation(
    donnees: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Prépare les variables numériques et la cible."""
    colonnes = [
        *COLONNES_MODELE_SIMULATION,
        COLONNE_CIBLE_SIMULATION,
    ]
    manquantes = [
        colonne for colonne in colonnes
        if colonne not in donnees.columns
    ]
    if manquantes:
        raise ValueError(f"Colonnes manquantes : {manquantes}")

    valeurs = donnees[colonnes].apply(
        pd.to_numeric,
        errors="raise",
    )
    valeurs = valeurs.replace(
        [float("inf"), -float("inf")],
        pd.NA,
    ).dropna()

    if valeurs.empty:
        raise ValueError("Aucune donnée exploitable pour le simulateur.")

    cible = valeurs[COLONNE_CIBLE_SIMULATION].astype(int)
    if not cible.isin([1, 2, 3, 4]).all():
        raise ValueError("La cible doit être comprise entre 1 et 4.")

    x = valeurs[COLONNES_MODELE_SIMULATION].astype(float)
    return x, cible


def separer_dates_simulation(
    dates: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """Garde les dates les plus récentes pour le test."""
    dates = pd.to_datetime(dates, errors="raise").dt.normalize()
    jours = dates.sort_values().unique()

    if len(jours) < 2:
        raise ValueError("Il faut plusieurs dates pour entraîner le modèle.")

    date_test = pd.Timestamp(
        jours[max(1, int(len(jours) * 0.8))]
    )
    train = dates < date_test - pd.Timedelta(days=2)
    test = dates >= date_test

    if not train.any() or not test.any():
        raise ValueError("Période trop courte pour séparer train et test.")

    return train, test


def creer_modele_simulation() -> Pipeline:
    """Crée le Random Forest du simulateur."""
    return Pipeline(
        steps=[
            ("imputation", SimpleImputer(strategy="median")),
            (
                "modele",
                RandomForestClassifier(
                    n_estimators=200,
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )


def entrainer_modele_simulation(
    donnees: pd.DataFrame,
) -> tuple[Pipeline, dict]:
    """Entraîne et évalue le modèle du simulateur."""
    donnees = donnees.reset_index(drop=True)
    x, y = preparer_donnees_simulation(donnees)

    dates = pd.to_datetime(
        donnees.loc[x.index, "date_meteo"]
    )
    train, test = separer_dates_simulation(dates)

    x_train, x_test = x.loc[train], x.loc[test]
    y_train, y_test = y.loc[train], y.loc[test]

    modele = creer_modele_simulation()
    modele.fit(x_train, y_train)
    predictions = modele.predict(x_test)

    reference = DummyClassifier(strategy="most_frequent")
    reference.fit(x_train, y_train)
    prediction_reference = reference.predict(x_test)

    resultats = {
        "accuracy": accuracy_score(y_test, predictions),
        "accuracy_reference": accuracy_score(
            y_test,
            prediction_reference,
        ),
        "f1_macro": f1_score(
            y_test,
            predictions,
            labels=[1, 2, 3, 4],
            average="macro",
            zero_division=0,
        ),
        "nb_train": len(x_train),
        "nb_test": len(x_test),
        "fin_train": dates.loc[train].max().date(),
        "debut_test": dates.loc[test].min().date(),
    }
    return modele, resultats


def sauvegarder_modele_simulation(
    modele: Pipeline,
    fichier: Path = FICHIER_PIPELINE_SIMULATION,
) -> None:
    """Enregistre le pipeline du simulateur."""
    joblib.dump(modele, fichier, compress=3)


def creer_entrees_simulation(
    *,
    latitude: float,
    longitude: float,
    temperature_moyenne: float,
    temperature_maximale: float,
    humidite_moyenne: float,
    precipitations: float,
    rafale_vent_maximale: float,
    deficit_pression_vapeur_maximal: float,
) -> pd.DataFrame:
    """Crée les trois lignes J0, J+1 et J+2 à prédire."""
    lignes = []
    for horizon in (0, 1, 2):
        lignes.append(
            {
                "horizon_jours": horizon,
                "latitude": latitude,
                "longitude": longitude,
                "temperature_moyenne": temperature_moyenne,
                "temperature_maximale": temperature_maximale,
                "humidite_moyenne": humidite_moyenne,
                "precipitations": precipitations,
                "rafale_vent_maximale": rafale_vent_maximale,
                "deficit_pression_vapeur_maximal":
                    deficit_pression_vapeur_maximal,
            }
        )
    return pd.DataFrame(
        lignes,
        columns=COLONNES_MODELE_SIMULATION,
    )
