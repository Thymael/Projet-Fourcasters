"""Point d'entrée unique des deux collectes quotidiennes Fourcasters."""

import argparse

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
from fourcasters_dbt.openmeteo import (
    DOSSIER_GCS as DOSSIER_GCS_OPENMETEO,
    TABLE_LANDING as TABLE_LANDING_OPENMETEO,
    collecter_communes,
    creer_parquet,
    fusionner_historique_bigquery as fusionner_historique_openmeteo,
    trouver_date_a_recuperer,
)


def main_openmeteo() -> None:
    """Lance la collecte Open-Meteo puis met à jour BigQuery."""

    print("\n🌦️  ACTUALISATION OPEN-METEO")
    configurer_google_cloud()
    DOSSIER_OPENMETEO.mkdir(parents=True, exist_ok=True)

    communes = pd.read_csv(
        FICHIER_COMMUNES,
        dtype={"numero_departement": "string", "code_insee": "string"},
    )
    date_a_recuperer = trouver_date_a_recuperer(len(communes))

    if date_a_recuperer is None:
        print("✅ Open-Meteo est déjà à jour.")
        return

    fichier_csv = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.csv"
    fichier_parquet = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.parquet"

    collecter_communes(communes, date_a_recuperer, fichier_csv)
    actualisation = creer_parquet(fichier_csv, fichier_parquet)

    print("\n✅ Collecte Open-Meteo terminée")
    print(f"   Communes : {len(actualisation)}/{len(communes)}")
    print(f"   Parquet : {fichier_parquet}")

    if len(actualisation) != len(communes):
        raise RuntimeError(
            f"Envoi impossible : {len(actualisation)} communes sur {len(communes)}."
        )

    print("\n☁️  Envoi vers Google Cloud...")
    chemin_gcs = f"{DOSSIER_GCS_OPENMETEO}/{fichier_parquet.name}"
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"✅ Fichier envoyé : {adresse_gcs}")
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING_OPENMETEO,
        len(communes),
    )

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    fusionner_historique_openmeteo(client_bigquery)


def main_incendie(mode_local: bool = False) -> None:
    """Lance la collecte incendie puis met à jour BigQuery."""

    print("\n🔥 ACTUALISATION MÉTÉO DES FORÊTS")
    api_key = lire_api_key()
    DOSSIER_INCENDIE.mkdir(parents=True, exist_ok=True)

    donnees_api = recuperer_meteo_forets(api_key)
    donnees_incendie = preparer_donnees(donnees_api)
    fichier_parquet = enregistrer_parquet_incendie(donnees_incendie)
    reference_time = donnees_incendie["reference_time"].iloc[0]

    print(f"✅ Départements : {len(donnees_incendie)}/{NOMBRE_DEPARTEMENTS_ATTENDU}")
    print(f"📅 Publication : {reference_time}")
    print(f"📦 Parquet : {fichier_parquet}")

    if mode_local:
        print("🧪 Mode local : aucun envoi vers Google Cloud.")
        return

    configurer_google_cloud()
    print("\n☁️  Envoi vers Google Cloud...")
    chemin_gcs = (
        f"{DOSSIER_GCS_INCENDIE}/"
        f"{reference_time:%Y/%m/%d}/{fichier_parquet.name}"
    )
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"✅ Fichier envoyé : {adresse_gcs}")

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    preparer_datasets_bigquery(client_bigquery)
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING_INCENDIE,
        NOMBRE_DEPARTEMENTS_ATTENDU,
    )
    fusionner_historique_incendie(client_bigquery)
    print("✅ Actualisation incendie terminée.")


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
    """Lance les deux pipelines ou seulement celui demandé en argument."""

    arguments = lire_arguments()

    print("\n🚀 ACTUALISATION FOURCASTERS")

    if not arguments.incendie_only:
        main_openmeteo()

    if not arguments.openmeteo_only:
        main_incendie(mode_local=arguments.local_only)

    print("\n🎉 Actualisation Fourcasters terminée.")


if __name__ == "__main__":
    main()
