"""Import ponctuel des archives annuelles de la Météo des forêts."""

import argparse
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from google.cloud import bigquery

from fourcasters_dbt.configuration import DOSSIER_INCENDIE, PROJET_GCP, configurer_google_cloud
from fourcasters_dbt.google_cloud import charger_parquet_bigquery, envoyer_parquet_gcs
from fourcasters_dbt.incendie import (
    DOSSIER_GCS,
    NOMBRE_DEPARTEMENTS_ATTENDU,
    TABLE_LANDING,
    convertir_niveaux_danger,
    creer_row_hash,
    fusionner_historique_bigquery,
    normaliser_code_departement,
    preparer_datasets_bigquery,
)


PREMIERE_ANNEE_DISPONIBLE = 2024
COLONNES_ARCHIVES = [
    "reference_time",
    "dep_code",
    "nom_dep",
    "niveau_j1",
    "niveau_j2",
]
# Les noms ont changé entre les fichiers 2024, 2025 et l'API actuelle.
RENOMMAGE_COLONNES = {
    "date": "reference_time",
    "num_dep": "dep_code",
    "dep_nom": "nom_dep",
}
URL_ARCHIVE = (
    "https://meteofrance.s3.sbg.io.cloud.ovh.net/"
    "data/BULLETIN/MDF/mdf_{annee}.csv.gz"
)
TIMEOUT_TELECHARGEMENT = 120


def lire_arguments():
    """Lit les années demandées et le mode d'exécution."""

    parser = argparse.ArgumentParser(
        description="Importe les archives annuelles de la Météo des forêts."
    )
    parser.add_argument(
        "--annees",
        nargs="+",
        type=int,
        default=list(
            range(
                PREMIERE_ANNEE_DISPONIBLE,
                datetime.now(timezone.utc).year + 1,
            )
        ),
        help="Années à importer, par exemple : --annees 2024 2025 2026",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Prépare le Parquet sans l'envoyer dans Google Cloud.",
    )
    return parser.parse_args()


def controler_annees(annees: list[int]):
    """Vérifie que les années demandées existent dans les archives."""

    annee_actuelle = datetime.now(timezone.utc).year
    annees_invalides = [
        annee
        for annee in annees
        if annee < PREMIERE_ANNEE_DISPONIBLE or annee > annee_actuelle
    ]

    if annees_invalides:
        raise ValueError(
            "Années indisponibles : "
            + ", ".join(str(annee) for annee in annees_invalides)
        )


def telecharger_archive(annee: int) -> pd.DataFrame:
    """Télécharge et lit le fichier CSV compressé d'une année."""

    url = URL_ARCHIVE.format(annee=annee)
    print(f"Téléchargement de l'archive {annee}...")

    reponse = requests.get(url, timeout=TIMEOUT_TELECHARGEMENT)
    reponse.raise_for_status()

    donnees = pd.read_csv(
        BytesIO(reponse.content),
        compression="gzip",
        sep=None,
        engine="python",
        dtype="string",
    )
    donnees.columns = donnees.columns.str.strip().str.lower()
    donnees = donnees.rename(columns=RENOMMAGE_COLONNES)
    donnees["annee_archive"] = annee

    print(f"Archive {annee} : {len(donnees)} lignes récupérées.")
    return donnees


def preparer_archives(donnees: pd.DataFrame) -> pd.DataFrame:
    """Harmonise les archives avec la table brute déjà utilisée."""

    colonnes_absentes = [
        colonne for colonne in COLONNES_ARCHIVES if colonne not in donnees.columns
    ]

    if colonnes_absentes:
        raise ValueError(
            "Colonnes absentes des archives : " + ", ".join(colonnes_absentes)
        )

    archives = donnees[COLONNES_ARCHIVES + ["annee_archive"]].copy()

    archives["reference_time"] = pd.to_datetime(
        archives["reference_time"],
        utc=True,
        errors="raise",
    )
    archives["dep_code"] = archives["dep_code"].map(normaliser_code_departement)
    archives["nom_dep"] = archives["nom_dep"].astype("string").str.strip()
    convertir_niveaux_danger(archives)

    if archives["reference_time"].isna().any():
        raise ValueError("Une date de publication est manquante.")

    if archives["nom_dep"].isna().any():
        raise ValueError("Un nom de département est manquant.")

    mauvaise_annee = archives[
        archives["reference_time"].dt.year != archives["annee_archive"]
    ]
    if not mauvaise_annee.empty:
        raise ValueError("Une publication n'appartient pas à la bonne archive annuelle.")

    doublons = archives.duplicated(["reference_time", "dep_code"])
    if doublons.any():
        raise ValueError("Les archives contiennent des départements en double.")

    nombres_departements = archives.groupby("reference_time")["dep_code"].nunique()
    publications_incompletes = nombres_departements[
        nombres_departements != NOMBRE_DEPARTEMENTS_ATTENDU
    ]
    if not publications_incompletes.empty:
        dates = publications_incompletes.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
        raise ValueError(
            "Publications incomplètes dans les archives : " + ", ".join(dates[:10])
        )

    archives["insere_a"] = datetime.now(timezone.utc)
    archives["row_hash"] = [
        creer_row_hash(ligne.reference_time, ligne.dep_code)
        for ligne in archives.itertuples()
    ]

    archives = archives.drop(columns="annee_archive")
    return archives.sort_values(["reference_time", "dep_code"]).reset_index(drop=True)


def enregistrer_parquet(donnees: pd.DataFrame, annees: list[int]) -> Path:
    """Enregistre toutes les années dans un seul Parquet."""

    premiere_annee = min(annees)
    derniere_annee = max(annees)
    fichier = DOSSIER_INCENDIE / (
        f"archives_meteo_forets_{premiere_annee}_{derniere_annee}.parquet"
    )
    donnees.to_parquet(fichier, index=False)
    return fichier


def importer_archives():
    """Télécharge, contrôle et charge les archives dans BigQuery."""

    arguments = lire_arguments()
    annees = sorted(set(arguments.annees))
    controler_annees(annees)

    DOSSIER_INCENDIE.mkdir(parents=True, exist_ok=True)
    configurer_google_cloud()

    print("\nIMPORT DES ARCHIVES MÉTÉO DES FORÊTS")
    archives_telechargees = [telecharger_archive(annee) for annee in annees]
    donnees = preparer_archives(pd.concat(archives_telechargees, ignore_index=True))
    fichier_parquet = enregistrer_parquet(donnees, annees)

    print(f"Années : {', '.join(str(annee) for annee in annees)}")
    print(f"Publications : {donnees['reference_time'].nunique()}")
    print(f"Lignes : {len(donnees)}")
    print(f"Parquet : {fichier_parquet}")

    if arguments.local_only:
        print("Mode local : aucun envoi vers Google Cloud.")
        return

    chemin_gcs = f"{DOSSIER_GCS}/archives/{fichier_parquet.name}"
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"Fichier envoyé : {adresse_gcs}")

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    preparer_datasets_bigquery(client_bigquery)
    charger_parquet_bigquery(adresse_gcs, TABLE_LANDING, len(donnees))
    fusionner_historique_bigquery(client_bigquery)
    print("\nImport des archives terminé.")
