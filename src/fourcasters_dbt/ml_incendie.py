"""Apprentissage et évaluation du danger Météo-France."""

import logging

import pandas as pd
from google.cloud import bigquery
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from fourcasters_dbt.configuration import DATASET_ANALYSE, PROJET_GCP, configurer_google_cloud

logger = logging.getLogger(__name__)
TABLE_ML = f"{PROJET_GCP}.{DATASET_ANALYSE}.ml_train_incendie"
COLONNE_CIBLE = "cible_niveau_danger"
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
    """Charge seulement les variables utiles et les fenêtres météo complètes."""
    configurer_google_cloud()
    client = bigquery.Client(project=PROJET_GCP)
    colonnes = ", ".join(["date_publication", *COLONNES_MODELE, COLONNE_CIBLE])
    requete = f"""
        SELECT {colonnes}
        FROM `{TABLE_ML}`
        WHERE meteo_disponible = TRUE
        ORDER BY date_publication, numero_departement, echeance
    """
    return client.query(requete).to_dataframe(create_bqstorage_client=False)


def preparer_donnees(donnees: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Écarte les lignes incomplètes et refuse une cible hors des niveaux 1 à 4."""
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
    return valeurs[COLONNES_MODELE].astype(float), valeurs[COLONNE_CIBLE].astype(int)


def separer_dates(dates: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Réserve les 20 % de dates les plus récentes au test, avec deux jours d'écart."""
    dates = pd.to_datetime(dates, errors="raise").dt.normalize()
    if dates.isna().any():
        raise ValueError("Une date de publication est manquante.")
    jours = dates.sort_values().unique()
    if len(jours) < 2:
        raise ValueError("Il faut plusieurs dates pour séparer apprentissage et test.")
    date_test = pd.Timestamp(jours[max(1, int(len(jours) * 0.8))])
    # Les cibles J1/J2 de l'apprentissage doivent être antérieures au premier test.
    train = dates < date_test - pd.Timedelta(days=2)
    test = dates >= date_test
    if not train.any() or not test.any():
        raise ValueError("Période trop courte après la séparation chronologique.")
    return train, test


def creer_modele() -> RandomForestClassifier:
    """Crée une forêt aléatoire reproductible, sans recherche de paramètres."""
    return RandomForestClassifier(
        n_estimators=200, random_state=42, class_weight="balanced", n_jobs=-1,
    )


def entrainer_modele(donnees: pd.DataFrame):
    """Compare la forêt au choix systématique de la classe majoritaire."""
    donnees = donnees.reset_index(drop=True)
    if "date_publication" not in donnees.columns:
        raise ValueError("La date de publication est nécessaire à l'évaluation.")
    x, y = preparer_donnees(donnees)
    if len(x) < 10:
        raise ValueError("Pas assez de lignes pour entraîner et tester le modèle.")
    dates = pd.to_datetime(donnees.loc[x.index, "date_publication"])
    train, test = separer_dates(dates)
    x_train, x_test = x.loc[train], x.loc[test]
    y_train, y_test = y.loc[train], y.loc[test]

    modele = creer_modele()
    modele.fit(x_train, y_train)
    predictions = modele.predict(x_test)
    reference = DummyClassifier(strategy="most_frequent")
    reference.fit(x_train, y_train)
    prediction_reference = reference.predict(x_test)

    resultats = {
        "accuracy": accuracy_score(y_test, predictions),
        "accuracy_reference": accuracy_score(y_test, prediction_reference),
        "f1_macro": f1_score(
            y_test, predictions, labels=[1, 2, 3, 4], average="macro", zero_division=0,
        ),
        "rapport": classification_report(y_test, predictions, labels=[1, 2, 3, 4], zero_division=0),
        "matrice_confusion": confusion_matrix(y_test, predictions, labels=[1, 2, 3, 4]),
        "importance": pd.Series(
            modele.feature_importances_, index=COLONNES_MODELE,
        ).sort_values(ascending=False),
        "nb_train": len(x_train),
        "nb_test": len(x_test),
        "nb_ecartes": int((~train & ~test).sum()),
        "fin_train": dates.loc[train].max().date(),
        "debut_test": dates.loc[test].min().date(),
    }
    return modele, resultats
