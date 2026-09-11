"""Collecte des niveaux de danger incendie publiés par Météo-France."""

import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from fourcasters_dbt.configuration import DOSSIER_INCENDIE, PROJET_GCP
from fourcasters_dbt.google_cloud import fusionner_historique
from fourcasters_dbt.http import recuperer_reponse

logger = logging.getLogger(__name__)


URL_METEO_FRANCE = (
    "https://public-api.meteofrance.fr/public/"
    "DPMeteoForets/v1/carte/departement/encours"
)
DOSSIER_GCS = "landing/meteofrance_incendie"
DATASET_LANDING = "meteofrance_landing"
DATASET_RAW = "meteofrance_raw"
TABLE_LANDING = f"{PROJET_GCP}.{DATASET_LANDING}.meteo_forets_actualisation"
TABLE_HISTORIQUE = f"{PROJET_GCP}.{DATASET_RAW}.meteo_forets"

CODES_DEPARTEMENTS = {f"{code:02d}" for code in range(1, 96) if code != 20} | {"2A", "2B"}
NOMBRE_DEPARTEMENTS_ATTENDU = len(CODES_DEPARTEMENTS)
TIMEOUT_API = 60
COLONNES_ATTENDUES = [
    "reference_time",
    "dep_code",
    "dep_nom",
    "niveau_j1",
    "niveau_j2",
]
COLONNES_BIGQUERY = [
    "reference_time",
    "dep_code",
    "nom_dep",
    "niveau_j1",
    "niveau_j2",
    "row_hash",
    "insere_a",
]


def lire_api_key() -> str:
    """Lit l'API Key Météo-France depuis l'environnement."""

    api_key = os.getenv("METEOFRANCE_API_KEY")

    if not api_key:
        raise ValueError(
            "La variable METEOFRANCE_API_KEY est absente. "
            "Ajoute-la dans le fichier .env."
        )

    return api_key


def normaliser_code_departement(valeur: object) -> str:
    """Ajoute le zéro initial et conserve les codes corses 2A et 2B."""

    code_departement = str(valeur).strip().upper()

    if code_departement in {"2A", "2B"}:
        return code_departement

    if not code_departement.isdigit():
        raise ValueError(f"Code département incorrect : {code_departement}")

    code_departement = code_departement.zfill(2)
    if code_departement not in CODES_DEPARTEMENTS:
        raise ValueError(f"Département hors du périmètre métropolitain : {code_departement}")
    return code_departement


def creer_row_hash(reference_time: pd.Timestamp, code_departement: str) -> str:
    """Crée la clé unique d'une publication et d'un département."""

    texte_hash = f"{reference_time.isoformat()}|{code_departement}"
    return hashlib.sha256(texte_hash.encode("utf-8")).hexdigest()


def recuperer_meteo_forets(api_key: str) -> list[dict]:
    """Récupère les niveaux J1 et J2 des 96 départements."""

    parametres = {"format": "json", "echeance": "J1J2"}
    entetes = {"accept": "application/json", "apikey": api_key}

    reponse = recuperer_reponse(
        URL_METEO_FRANCE, params=parametres, headers=entetes, timeout=TIMEOUT_API,
    )
    donnees_api = reponse.json()
    if not isinstance(donnees_api, list):
        raise ValueError("La réponse Météo-France n'est pas une liste.")
    return donnees_api


def controler_colonnes(donnees: pd.DataFrame) -> None:
    """Vérifie que la réponse contient toutes les colonnes utiles."""

    colonnes_absentes = [
        colonne
        for colonne in COLONNES_ATTENDUES
        if colonne not in donnees.columns
    ]

    if colonnes_absentes:
        raise ValueError(
            "Colonnes absentes de la réponse : "
            + ", ".join(colonnes_absentes)
        )


def convertir_niveaux_danger(donnees: pd.DataFrame) -> None:
    """Convertit et contrôle les niveaux de danger J1 et J2."""

    for colonne in ["niveau_j1", "niveau_j2"]:
        donnees[colonne] = pd.to_numeric(
            donnees[colonne], errors="raise"
        ).astype("Int64")

        if donnees[colonne].isna().any():
            raise ValueError(f"Valeur manquante dans la colonne {colonne}.")

        if not donnees[colonne].between(1, 4).all():
            raise ValueError(f"Niveau incorrect dans la colonne {colonne}.")


def preparer_donnees(donnees_api: list[dict]) -> pd.DataFrame:
    """Contrôle la réponse Météo-France et prépare les colonnes BigQuery."""

    if len(donnees_api) != NOMBRE_DEPARTEMENTS_ATTENDU:
        raise ValueError(
            f"{NOMBRE_DEPARTEMENTS_ATTENDU} départements attendus, "
            f"mais {len(donnees_api)} reçus."
        )

    donnees_incendie = pd.DataFrame(donnees_api)
    controler_colonnes(donnees_incendie)
    donnees_incendie = donnees_incendie[COLONNES_ATTENDUES].copy()
    # Le nom de colonne de la table brute historique est `nom_dep`.
    donnees_incendie = donnees_incendie.rename(columns={"dep_nom": "nom_dep"})

    return preparer_publications(donnees_incendie)


def preparer_publications(donnees: pd.DataFrame) -> pd.DataFrame:
    """Contrôle les publications de l'API ou des archives avant leur chargement."""
    donnees_incendie = donnees.copy()
    donnees_incendie["reference_time"] = pd.to_datetime(
        donnees_incendie["reference_time"],
        utc=True,
        errors="raise",
    )
    donnees_incendie["dep_code"] = donnees_incendie["dep_code"].map(
        normaliser_code_departement
    )
    donnees_incendie["nom_dep"] = (
        donnees_incendie["nom_dep"].astype("string").str.strip()
    )
    convertir_niveaux_danger(donnees_incendie)

    if donnees_incendie.empty or donnees_incendie["reference_time"].isna().any():
        raise ValueError("Publication vide ou date manquante.")
    if donnees_incendie["nom_dep"].isna().any() or donnees_incendie["nom_dep"].eq("").any():
        raise ValueError("Un nom de département est manquant.")
    if donnees_incendie.duplicated(["reference_time", "dep_code"]).any():
        raise ValueError("Un département est présent plusieurs fois dans une publication.")
    volumes = donnees_incendie.groupby("reference_time")["dep_code"].nunique()
    if not volumes.eq(NOMBRE_DEPARTEMENTS_ATTENDU).all():
        raise ValueError("Chaque publication doit contenir les 96 départements.")

    donnees_incendie["insere_a"] = datetime.now(timezone.utc)
    donnees_incendie["row_hash"] = [
        creer_row_hash(ligne.reference_time, ligne.dep_code)
        for ligne in donnees_incendie.itertuples()
    ]

    return donnees_incendie[COLONNES_BIGQUERY].sort_values(
        ["reference_time", "dep_code"]
    ).reset_index(drop=True)


def enregistrer_parquet(donnees_incendie: pd.DataFrame) -> Path:
    """Enregistre une publication dans un fichier Parquet local."""

    reference_time = donnees_incendie["reference_time"].iloc[0]
    horodatage = reference_time.strftime("%Y%m%dT%H%M%SZ")
    fichier_parquet = DOSSIER_INCENDIE / f"meteo_forets_{horodatage}.parquet"
    fichier_parquet.parent.mkdir(parents=True, exist_ok=True)
    donnees_incendie.to_parquet(fichier_parquet, index=False)
    return fichier_parquet


def preparer_datasets_bigquery(client: bigquery.Client) -> None:
    """Crée les datasets Météo-France dans la même région qu'Open-Meteo."""

    dataset_openmeteo = client.get_dataset(f"{PROJET_GCP}.openmeteo_raw")
    localisation = dataset_openmeteo.location or "EU"

    for nom_dataset in (DATASET_LANDING, DATASET_RAW):
        dataset = bigquery.Dataset(f"{PROJET_GCP}.{nom_dataset}")
        dataset.location = localisation
        client.create_dataset(dataset, exists_ok=True)

    logger.info("Datasets prêts dans la région %s.", localisation)


def fusionner_historique_bigquery(client: bigquery.Client, table_landing=TABLE_LANDING) -> None:
    """Fusionne une publication ou un import d'archives validé."""
    fusionner_historique(
        client, table_landing, TABLE_HISTORIQUE, COLONNES_BIGQUERY,
        "reference_time", "dep_code",
    )
