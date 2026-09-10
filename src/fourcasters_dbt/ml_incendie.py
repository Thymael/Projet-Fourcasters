"""Fonctions simples pour entraîner le modèle de danger incendie."""

import pandas as pd

from google.cloud import bigquery
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


PROJET_GCP = "fourcasters-openmeteo-loick"

TABLE_ML = (
    "fourcasters-openmeteo-loick."
    "openmeteo_analyse."
    "ml_train_incendie"
)


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


COLONNE_CIBLE = "cible_niveau_danger"


def charger_donnees() -> pd.DataFrame:
    """Charge le jeu d'apprentissage directement depuis BigQuery."""

    client = bigquery.Client(project=PROJET_GCP)

    requete = f"""
        SELECT *
        FROM `{TABLE_ML}`
        WHERE meteo_disponible = TRUE
        ORDER BY date_publication
    """

    return client.query(requete).to_dataframe()


def preparer_donnees(
    donnees: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Prépare les variables utilisées par le modèle."""

    colonnes_obligatoires = COLONNES_MODELE + [COLONNE_CIBLE]

    colonnes_manquantes = [
        colonne
        for colonne in colonnes_obligatoires
        if colonne not in donnees.columns
    ]

    if colonnes_manquantes:
        raise ValueError(
            f"Colonnes manquantes : {colonnes_manquantes}"
        )

    donnees = donnees.copy()

    for colonne in colonnes_obligatoires:
        donnees[colonne] = pd.to_numeric(
            donnees[colonne],
            errors="coerce",
        )

    donnees = donnees.dropna(
        subset=colonnes_obligatoires
    )

    if donnees.empty:
        raise ValueError(
            "Aucune donnée exploitable pour entraîner le modèle."
        )

    x = donnees[COLONNES_MODELE].astype(float)
    y = donnees[COLONNE_CIBLE].astype(int)

    return x, y


def creer_modele() -> RandomForestClassifier:
    """Crée le modèle de classification."""

    return RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )


def entrainer_modele(donnees: pd.DataFrame):
    """Entraîne le modèle et calcule quelques indicateurs simples."""

    x, y = preparer_donnees(donnees)

    if len(x) < 10:
        raise ValueError(
            "Pas assez de données pour entraîner et tester le modèle."
        )

    # Les données sont séparées chronologiquement :
    # 80 % pour apprendre et 20 % pour tester.
    dates = pd.to_datetime(
        donnees.loc[x.index, "date_publication"]
    )

    ordre = dates.sort_values().index

    x = x.loc[ordre]
    y = y.loc[ordre]

    coupure = int(len(x) * 0.8)

    x_train = x.iloc[:coupure]
    x_test = x.iloc[coupure:]

    y_train = y.iloc[:coupure]
    y_test = y.iloc[coupure:]

    modele = creer_modele()

    modele.fit(
        x_train,
        y_train,
    )

    predictions = modele.predict(x_test)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    rapport = classification_report(
        y_test,
        predictions,
        zero_division=0,
    )

    matrice = confusion_matrix(
        y_test,
        predictions,
        labels=[1, 2, 3, 4],
    )

    importance = pd.Series(
        modele.feature_importances_,
        index=COLONNES_MODELE,
    ).sort_values(ascending=False)

    resultats = {
        "accuracy": accuracy,
        "rapport": rapport,
        "matrice_confusion": matrice,
        "importance": importance,
        "nb_train": len(x_train),
        "nb_test": len(x_test),
    }

    return modele, resultats