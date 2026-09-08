"""Collecte des niveaux de danger incendie publiés par Météo-France."""

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from google.cloud import bigquery

from fourcasters_dbt.configuration import DOSSIER_INCENDIE, PROJET_GCP


URL_METEO_FRANCE = (
    "https://public-api.meteofrance.fr/public/"
    "DPMeteoForets/v1/carte/departement/encours"
)
DOSSIER_GCS = "landing/meteofrance_incendie"
DATASET_LANDING = "meteofrance_landing"
DATASET_RAW = "meteofrance_raw"
TABLE_LANDING = f"{PROJET_GCP}.{DATASET_LANDING}.meteo_forets_actualisation"
TABLE_HISTORIQUE = f"{PROJET_GCP}.{DATASET_RAW}.meteo_forets"

NOMBRE_DEPARTEMENTS_ATTENDU = 96
NOMBRE_TENTATIVES = 3
TIMEOUT_API = 60
PAUSE_APRES_ERREUR = 10
PAUSE_QUOTA = 61
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

    return code_departement.zfill(2)


def creer_row_hash(reference_time: pd.Timestamp, code_departement: str) -> str:
    """Crée la clé unique d'une publication et d'un département."""

    texte_hash = f"{reference_time.isoformat()}|{code_departement}"
    return hashlib.sha256(texte_hash.encode("utf-8")).hexdigest()


def recuperer_meteo_forets(api_key: str) -> list[dict]:
    """Récupère les niveaux J1 et J2 des 96 départements."""

    parametres = {"format": "json", "echeance": "J1J2"}
    entetes = {"accept": "application/json", "apikey": api_key}

    for tentative in range(1, NOMBRE_TENTATIVES + 1):
        try:
            print(f"🔄 Tentative API {tentative}/{NOMBRE_TENTATIVES}")
            reponse = requests.get(
                URL_METEO_FRANCE,
                params=parametres,
                headers=entetes,
                timeout=TIMEOUT_API,
            )

            if reponse.status_code == 429:
                if tentative == NOMBRE_TENTATIVES:
                    raise RuntimeError("Météo-France bloque toujours les requêtes.")

                print(f"⏳ Limite API : pause de {PAUSE_QUOTA} secondes...")
                time.sleep(PAUSE_QUOTA)
                continue

            reponse.raise_for_status()
            donnees_api = reponse.json()

            if not isinstance(donnees_api, list):
                raise ValueError("La réponse de l'API n'est pas une liste.")

            return donnees_api

        except (requests.RequestException, ValueError) as erreur:
            print(f"❌ Échec de l'appel API : {erreur}")

            if tentative < NOMBRE_TENTATIVES:
                print(f"Nouvel essai dans {PAUSE_APRES_ERREUR} secondes...")
                time.sleep(PAUSE_APRES_ERREUR)

    raise RuntimeError("L'API Météo-France reste inaccessible après trois essais.")


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

    if donnees_incendie["dep_code"].duplicated().any():
        raise ValueError("Un département est présent plusieurs fois.")

    if donnees_incendie["reference_time"].nunique() != 1:
        raise ValueError("Plusieurs dates de publication sont présentes.")

    donnees_incendie["insere_a"] = datetime.now(timezone.utc)
    donnees_incendie["row_hash"] = [
        creer_row_hash(ligne.reference_time, ligne.dep_code)
        for ligne in donnees_incendie.itertuples()
    ]

    return donnees_incendie.sort_values("dep_code").reset_index(drop=True)


def enregistrer_parquet(donnees_incendie: pd.DataFrame) -> Path:
    """Enregistre une publication dans un fichier Parquet local."""

    reference_time = donnees_incendie["reference_time"].iloc[0]
    horodatage = reference_time.strftime("%Y%m%dT%H%M%SZ")
    fichier_parquet = DOSSIER_INCENDIE / f"meteo_forets_{horodatage}.parquet"
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

    print(f"✅ Datasets prêts dans la région {localisation}.")


def fusionner_historique_bigquery(client: bigquery.Client) -> None:
    """Ajoute la publication à l'historique sans créer de doublon."""

    colonnes_modifiees = [
        colonne for colonne in COLONNES_BIGQUERY if colonne != "row_hash"
    ]
    mises_a_jour = ",\n        ".join(
        f"{colonne} = source.{colonne}" for colonne in colonnes_modifiees
    )
    colonnes = ", ".join(COLONNES_BIGQUERY)
    valeurs = ", ".join(f"source.{colonne}" for colonne in COLONNES_BIGQUERY)

    requete = f"""
    CREATE TABLE IF NOT EXISTS `{TABLE_HISTORIQUE}`
    PARTITION BY DATE(reference_time)
    CLUSTER BY dep_code
    AS
    SELECT *
    FROM `{TABLE_LANDING}`
    WHERE FALSE;

    MERGE `{TABLE_HISTORIQUE}` AS cible
    USING `{TABLE_LANDING}` AS source
      ON cible.row_hash = source.row_hash

    WHEN MATCHED THEN
      UPDATE SET
        {mises_a_jour}

    WHEN NOT MATCHED THEN
      INSERT ({colonnes})
      VALUES ({valeurs});
    """
    client.query(requete).result()

    controle = f"""
        SELECT
            COUNT(*) AS nombre_lignes,
            COUNT(DISTINCT row_hash) AS nombre_cles
        FROM `{TABLE_HISTORIQUE}`
    """
    resultat = list(client.query(controle).result())[0]

    if resultat.nombre_lignes != resultat.nombre_cles:
        raise ValueError("La table historique contient des doublons.")

    print(f"✅ Historique incendie mis à jour : {resultat.nombre_lignes} lignes.")
