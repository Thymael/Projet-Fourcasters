"""Fonctions utilisées pour entraîner et évaluer le modèle incendie."""

import logging
from pathlib import Path

import joblib
import pandas as pd
from google.cloud import bigquery
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from fourcasters_dbt.configuration import (
    DATASET_ANALYSE,
    PROJET_GCP,
    RACINE_PROJET,
    configurer_google_cloud,
)

logger = logging.getLogger(__name__)

TABLE_ML = f"{PROJET_GCP}.{DATASET_ANALYSE}.ml_train_incendie"
FICHIER_PIPELINE = RACINE_PROJET / "pipeline.pkl"
COLONNE_CIBLE = "cible_niveau_danger"
VERSION_FEATURES = "meteo_J-6_a_J_train_2024_2025_test_2026_fin_2026-10-02_v4"

ANNEES_APPRENTISSAGE = (2024, 2025)
ANNEE_TEST = 2026
DATE_FIN_TEST = pd.Timestamp("2026-10-02")

COLONNES_CONTEXTE = [
    "date_publication",
    "date_prevision",
    "numero_departement",
    "departement",
    "echeance",
]

COLONNES_MODELE = [
    "horizon_jours",
    "temperature_moyenne",
    "temperature_maximale",
    "humidite_moyenne",
    "precipitations_moyennes",
    "rafale_vent_maximale",
    "deficit_pression_vapeur_maximal",
    "temperature_moyenne_7j",
    "temperature_maximale_7j",
    "humidite_moyenne_7j",
    "precipitations_moyennes_7j",
    "rafale_vent_maximale_7j",
    "deficit_pression_vapeur_maximal_7j",
    "jours_sans_pluie_7j",
]


def charger_donnees() -> pd.DataFrame:
    """Charge le jeu d'apprentissage préparé par dbt."""
    configurer_google_cloud()
    client = bigquery.Client(project=PROJET_GCP)
    colonnes = ", ".join([*COLONNES_CONTEXTE, *COLONNES_MODELE, COLONNE_CIBLE])
    requete = f"""
        SELECT {colonnes}
        FROM `{TABLE_ML}`
        WHERE meteo_disponible = TRUE
        ORDER BY date_prevision, numero_departement, echeance
    """
    return client.query(requete).to_dataframe(create_bqstorage_client=False)


def preparer_donnees(donnees: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Prépare X et y et retire les lignes incomplètes."""
    colonnes = COLONNES_MODELE + [COLONNE_CIBLE]
    manquantes = [colonne for colonne in colonnes if colonne not in donnees.columns]
    if manquantes:
        raise ValueError(f"Colonnes manquantes : {manquantes}")

    valeurs = donnees[colonnes].apply(pd.to_numeric, errors="raise")
    if valeurs.isin([float("inf"), -float("inf")]).any().any():
        raise ValueError("Une variable du modèle contient une valeur infinie.")

    cible = valeurs[COLONNE_CIBLE].dropna()
    if not cible.isin([1, 2, 3, 4]).all():
        raise ValueError("La cible doit être un entier de 1 à 4.")

    valeurs = valeurs.dropna()
    if valeurs.empty:
        raise ValueError("Aucune donnée exploitable pour entraîner le modèle.")

    if len(valeurs) < len(donnees):
        logger.warning("%s lignes incomplètes retirées.", len(donnees) - len(valeurs))

    x = valeurs[COLONNES_MODELE].astype(float)
    y = valeurs[COLONNE_CIBLE].astype(int)
    return x, y


def separer_dates(dates_prevision: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Sépare 2024-2025 pour l'apprentissage et 2026 jusqu'au 02/10 pour le test."""
    dates_prevision = pd.to_datetime(
        dates_prevision,
        errors="raise",
    ).dt.normalize()

    if dates_prevision.isna().any():
        raise ValueError("Une date de prévision est manquante.")

    annees = dates_prevision.dt.year
    train = annees.isin(ANNEES_APPRENTISSAGE)
    test = annees.eq(ANNEE_TEST) & dates_prevision.le(DATE_FIN_TEST)

    if not train.any():
        raise ValueError("Aucune donnée 2024-2025 disponible pour l'apprentissage.")
    if not test.any():
        raise ValueError("Aucune donnée 2026 jusqu’au 02/10 disponible pour le test.")

    return train, test


def creer_modele() -> Pipeline:
    """Crée le Pipeline scikit-learn utilisé par le projet."""
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


def entrainer_modele(donnees: pd.DataFrame):
    """Entraîne sur 2024-2025 et évalue uniquement sur les cibles 2026."""
    donnees = donnees.reset_index(drop=True)

    if "date_prevision" not in donnees.columns:
        raise ValueError(
            "La date de prévision est nécessaire pour séparer "
            "l'apprentissage 2024-2025 du test 2026."
        )

    x, y = preparer_donnees(donnees)
    if len(x) < 10:
        raise ValueError("Pas assez de lignes pour entraîner et tester le modèle.")

    dates_prevision = pd.to_datetime(
        donnees.loc[x.index, "date_prevision"],
        errors="raise",
    )
    train, test = separer_dates(dates_prevision)

    x_train, x_test = x.loc[train], x.loc[test]
    y_train, y_test = y.loc[train], y.loc[test]

    modele = creer_modele()
    modele.fit(x_train, y_train)
    modele.fourcasters_feature_version = VERSION_FEATURES
    predictions = modele.predict(x_test)

    reference = DummyClassifier(strategy="most_frequent")
    reference.fit(x_train, y_train)
    prediction_reference = reference.predict(x_test)

    foret = modele.named_steps["modele"]
    hors_periode = ~(train | test)

    resultats = {
        "accuracy": accuracy_score(y_test, predictions),
        "accuracy_reference": accuracy_score(y_test, prediction_reference),
        "f1_macro_reference": f1_score(
            y_test,
            prediction_reference,
            labels=[1, 2, 3, 4],
            average="macro",
            zero_division=0,
        ),
        "classe_reference": int(y_train.mode().iloc[0]),
        "f1_macro": f1_score(
            y_test,
            predictions,
            labels=[1, 2, 3, 4],
            average="macro",
            zero_division=0,
        ),
        "rapport": classification_report(
            y_test,
            predictions,
            labels=[1, 2, 3, 4],
            zero_division=0,
        ),
        "matrice_confusion": confusion_matrix(
            y_test,
            predictions,
            labels=[1, 2, 3, 4],
        ),
        "importance": pd.Series(
            foret.feature_importances_,
            index=COLONNES_MODELE,
        ).sort_values(ascending=False),
        "nb_train": len(x_train),
        "nb_test": len(x_test),
        "nb_hors_periode": int(hors_periode.sum()),
        "debut_train": dates_prevision.loc[train].min().date(),
        "fin_train": dates_prevision.loc[train].max().date(),
        "debut_test": dates_prevision.loc[test].min().date(),
        "fin_test": dates_prevision.loc[test].max().date(),
        "annees_train": "2024-2025",
        "annee_test": "2026",
        "fenetre_meteo": "J-6 à J",
        "date_fin_test": DATE_FIN_TEST.date(),
    }
    return modele, resultats


def sauvegarder_modele(
    modele: Pipeline,
    fichier: Path = FICHIER_PIPELINE,
) -> None:
    """Enregistre le Pipeline pour pouvoir le recharger dans Streamlit."""
    joblib.dump(modele, fichier, compress=3)
