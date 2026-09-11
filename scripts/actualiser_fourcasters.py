"""Point d'entrée unique des deux collectes quotidiennes Fourcasters."""

import argparse
import logging

import pandas as pd
from google.cloud import bigquery

from fourcasters_dbt.configuration import (
    DOSSIER_INCENDIE,
    DOSSIER_OPENMETEO,
    FICHIER_COMMUNES,
    PROJET_GCP,
    configurer_google_cloud,
)
from fourcasters_dbt.google_cloud import (
    charger_parquet_bigquery,
    envoyer_parquet_gcs,
)
from fourcasters_dbt.incendie import (
    DOSSIER_GCS as DOSSIER_GCS_INCENDIE,
    NOMBRE_DEPARTEMENTS_ATTENDU,
    TABLE_LANDING as TABLE_LANDING_INCENDIE,
    enregistrer_parquet as enregistrer_parquet_incendie,
    fusionner_historique_bigquery as fusionner_historique_incendie,
    lire_api_key,
    preparer_datasets_bigquery,
    preparer_donnees,
    recuperer_meteo_forets,
)
from fourcasters_dbt.journal import configurer_logs
from fourcasters_dbt.openmeteo import (
    DOSSIER_GCS as DOSSIER_GCS_OPENMETEO,
    TABLE_LANDING as TABLE_LANDING_OPENMETEO,
    collecter_communes,
    creer_parquet,
    fusionner_historique_bigquery as fusionner_historique_openmeteo,
    trouver_date_a_recuperer,
)

logger = logging.getLogger(__name__)
NOMBRE_POINTS_ATTENDU = 360
MAX_JOURS_PAR_EXECUTION = 7


def actualiser_journee_openmeteo(communes, date_a_recuperer) -> None:
    """Collecte une journée complète avant de la charger."""

    fichier_csv = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.csv"
    fichier_parquet = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.parquet"

    collecter_communes(communes, date_a_recuperer, fichier_csv)
    actualisation = creer_parquet(fichier_csv, fichier_parquet, communes, date_a_recuperer)

    logger.info("✅ Collecte terminée : %s/%s communes", len(actualisation), len(communes))
    logger.info("Parquet : %s", fichier_parquet)

    logger.info("☁️  Envoi vers Google Cloud...")
    chemin_gcs = f"{DOSSIER_GCS_OPENMETEO}/{fichier_parquet.name}"
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    logger.info("Fichier envoyé : %s", adresse_gcs)
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING_OPENMETEO,
        len(communes),
    )

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    fusionner_historique_openmeteo(client_bigquery)


def main_openmeteo() -> None:
    """Rattrape les journées manquantes, au maximum sept par exécution."""
    logger.info("🌦️ Actualisation Open-Meteo")
    configurer_google_cloud()
    DOSSIER_OPENMETEO.mkdir(parents=True, exist_ok=True)
    communes = pd.read_csv(
        FICHIER_COMMUNES,
        dtype={"numero_departement": "string", "code_insee": "string"},
    )
    communes["code_insee"] = communes["code_insee"].str.strip()
    if (
        len(communes) != NOMBRE_POINTS_ATTENDU
        or communes["code_insee"].isna().any()
        or communes["code_insee"].duplicated().any()
    ):
        raise ValueError("Le référentiel doit contenir 360 codes de commune distincts.")
    for _ in range(MAX_JOURS_PAR_EXECUTION):
        jour = trouver_date_a_recuperer(len(communes))
        if jour is None:
            return
        actualiser_journee_openmeteo(communes, jour)
    if trouver_date_a_recuperer(len(communes)) is not None:
        logger.warning("⏳ Sept journées récupérées. Une prochaine exécution poursuivra le rattrapage.")


def main_incendie(mode_local: bool = False) -> None:
    """Lance la collecte incendie puis met à jour BigQuery."""

    logger.info("🔥 Actualisation Météo des forêts")
    api_key = lire_api_key()
    DOSSIER_INCENDIE.mkdir(parents=True, exist_ok=True)

    donnees_api = recuperer_meteo_forets(api_key)
    donnees_incendie = preparer_donnees(donnees_api)
    fichier_parquet = enregistrer_parquet_incendie(donnees_incendie)
    reference_time = donnees_incendie["reference_time"].iloc[0]

    logger.info("Départements : %s/%s", len(donnees_incendie), NOMBRE_DEPARTEMENTS_ATTENDU)
    logger.info("Publication : %s", reference_time)
    logger.info("Parquet : %s", fichier_parquet)

    if mode_local:
        logger.info("🧪 Mode local : aucun envoi vers Google Cloud.")
        return

    configurer_google_cloud()
    logger.info("☁️  Envoi vers Google Cloud...")
    chemin_gcs = (
        f"{DOSSIER_GCS_INCENDIE}/"
        f"{reference_time:%Y/%m/%d}/{fichier_parquet.name}"
    )
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    logger.info("Fichier envoyé : %s", adresse_gcs)

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    preparer_datasets_bigquery(client_bigquery)
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING_INCENDIE,
        NOMBRE_DEPARTEMENTS_ATTENDU,
    )
    fusionner_historique_incendie(client_bigquery)
    logger.info("✅ Actualisation incendie terminée.")


def lire_arguments() -> argparse.Namespace:
    """Lit les options choisies dans le terminal."""

    parser = argparse.ArgumentParser(description="Actualise les données Fourcasters.")
    choix = parser.add_mutually_exclusive_group()
    choix.add_argument(
        "--openmeteo-only",
        action="store_true",
        help="Lance seulement la collecte Open-Meteo.",
    )
    choix.add_argument(
        "--incendie-only",
        action="store_true",
        help="Lance seulement la collecte Météo-France.",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Teste l'incendie sans envoyer de fichier dans Google Cloud.",
    )
    arguments = parser.parse_args()

    if arguments.local_only and not arguments.incendie_only:
        parser.error("--local-only doit être utilisé avec --incendie-only")

    return arguments


def main() -> None:
    """Lance les deux pipelines ou seulement celui demandé."""

    configurer_logs()
    arguments = lire_arguments()

    logger.info("🚀 Démarrage de l'actualisation Fourcasters")

    try:
        if not arguments.incendie_only:
            main_openmeteo()

        if not arguments.openmeteo_only:
            main_incendie(mode_local=arguments.local_only)

    except Exception:
        logger.exception("❌ Échec de l'actualisation Fourcasters")
        raise SystemExit(1)

    logger.info("✅ Actualisation Fourcasters terminée")


if __name__ == "__main__":
    main()
