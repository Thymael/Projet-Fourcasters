"""Collecte des niveaux de danger incendie publiés par Météo-France."""

import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from google.cloud import bigquery

from fourcasters_dbt.configuration import (
    DOSSIER_INCENDIE,
    PROJET_GCP,
    configurer_google_cloud,
)
from fourcasters_dbt.google_cloud import (
    charger_parquet_bigquery,
    envoyer_parquet_gcs,
)


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
COLONNES_ATTENDUES = [
    "reference_time",
    "dep_code",
    "dep_nom",
    "niveau_j1",
    "niveau_j2",
]


def lire_api_key() -> str:
    """Lit l'API Key Météo-France depuis l'environnement."""

    api_key = os.getenv("METEOFRANCE_API_KEY")

    if not api_key:
        raise ValueError(
            "La variable METEOFRANCE_API_KEY est absente. "
            "Charge le fichier .env avant de lancer le script."
        )

    return api_key


def normaliser_code_departement(valeur) -> str:
    """Ajoute le zéro initial et conserve les codes corses 2A et 2B."""

    code_departement = str(valeur).strip().upper()

    if code_departement in ["2A", "2B"]:
        return code_departement

    if not code_departement.isdigit():
        raise ValueError(f"Code département incorrect : {code_departement}")

    return code_departement.zfill(2)


def creer_row_hash(reference_time, code_departement: str) -> str:
    """Crée la clé unique d'une publication et d'un département."""

    texte_hash = f"{reference_time.isoformat()}|{code_departement}"
    return hashlib.sha256(texte_hash.encode("utf-8")).hexdigest()


def recuperer_meteo_forets(api_key: str) -> list[dict]:
    """Récupère les niveaux J1 et J2 des 96 départements."""

    parametres = {"format": "json", "echeance": "J1J2"}
    entetes = {"accept": "application/json", "apikey": api_key}

    for tentative in range(1, NOMBRE_TENTATIVES + 1):
        try:
            print(f"Tentative API {tentative}/{NOMBRE_TENTATIVES}")
            reponse = requests.get(
                URL_METEO_FRANCE,
                params=parametres,
                headers=entetes,
                timeout=TIMEOUT_API,
            )

            if reponse.status_code == 429:
                if tentative == NOMBRE_TENTATIVES:
                    raise RuntimeError("Météo-France bloque toujours les requêtes.")

                print("Limite API : pause de 61 secondes...")
                time.sleep(61)
                continue

            reponse.raise_for_status()
            donnees_api = reponse.json()

            if not isinstance(donnees_api, list):
                raise ValueError("La réponse de l'API n'est pas une liste.")

            return donnees_api

        except (requests.RequestException, ValueError) as erreur:
            print(f"Échec de l'appel API : {erreur}")

            if tentative < NOMBRE_TENTATIVES:
                print("Nouvel essai dans 10 secondes...")
                time.sleep(10)

    raise RuntimeError("L'API Météo-France reste inaccessible après trois essais.")


def controler_colonnes(donnees: pd.DataFrame):
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


def convertir_niveaux_danger(donnees: pd.DataFrame):
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

    donnees_incendie["reference_time"] = pd.to_datetime(
        donnees_incendie["reference_time"],
        utc=True,
        errors="raise",
    )
    donnees_incendie["dep_code"] = donnees_incendie["dep_code"].map(
        normaliser_code_departement
    )
    donnees_incendie["dep_nom"] = (
        donnees_incendie["dep_nom"].astype("string").str.strip()
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


def preparer_datasets_bigquery(client: bigquery.Client):
    """Crée les datasets Météo-France dans la même région qu'Open-Meteo."""

    dataset_openmeteo = client.get_dataset(f"{PROJET_GCP}.openmeteo_raw")
    localisation = dataset_openmeteo.location or "EU"

    for nom_dataset in [DATASET_LANDING, DATASET_RAW]:
        dataset = bigquery.Dataset(f"{PROJET_GCP}.{nom_dataset}")
        dataset.location = localisation
        client.create_dataset(dataset, exists_ok=True)

    print(f"Datasets prêts dans la région {localisation}.")


def fusionner_historique_bigquery(client: bigquery.Client):
    """Ajoute la publication à l'historique sans créer de doublon."""

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
        reference_time = source.reference_time,
        dep_code = source.dep_code,
        dep_nom = source.dep_nom,
        niveau_j1 = source.niveau_j1,
        niveau_j2 = source.niveau_j2,
        insere_a = source.insere_a

    WHEN NOT MATCHED THEN
      INSERT (
        reference_time,
        dep_code,
        dep_nom,
        niveau_j1,
        niveau_j2,
        row_hash,
        insere_a
      )
      VALUES (
        source.reference_time,
        source.dep_code,
        source.dep_nom,
        source.niveau_j1,
        source.niveau_j2,
        source.row_hash,
        source.insere_a
      );
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

    print(f"Historique mis à jour : {resultat.nombre_lignes} lignes.")


def main():
    """Orchestre la collecte incendie et son chargement dans BigQuery."""

    mode_local = "--local-only" in sys.argv
    api_key = lire_api_key()
    configurer_google_cloud()
    DOSSIER_INCENDIE.mkdir(parents=True, exist_ok=True)

    print("\nACTUALISATION MÉTÉO DES FORÊTS")
    donnees_api = recuperer_meteo_forets(api_key)
    donnees_incendie = preparer_donnees(donnees_api)
    fichier_parquet = enregistrer_parquet(donnees_incendie)
    reference_time = donnees_incendie["reference_time"].iloc[0]

    print(f"Départements : {len(donnees_incendie)}/{NOMBRE_DEPARTEMENTS_ATTENDU}")
    print(f"Publication : {reference_time}")
    print(f"Parquet : {fichier_parquet}")

    if mode_local:
        print("Mode local : aucun envoi vers Google Cloud.")
        return

    print("\nEnvoi vers Google Cloud...")
    chemin_gcs = (
        f"{DOSSIER_GCS}/{reference_time:%Y/%m/%d}/{fichier_parquet.name}"
    )
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"Fichier envoyé : {adresse_gcs}")

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    preparer_datasets_bigquery(client_bigquery)
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING,
        NOMBRE_DEPARTEMENTS_ATTENDU,
    )
    fusionner_historique_bigquery(client_bigquery)
    print("\nActualisation incendie terminée.")


if __name__ == "__main__":
    main()
