"""Point d'entrée unique des deux collectes quotidiennes Fourcasters."""

import sys

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
    """Orchestre la collecte Open-Meteo et son chargement dans BigQuery."""

    configurer_google_cloud()
    DOSSIER_OPENMETEO.mkdir(parents=True, exist_ok=True)

    communes = pd.read_csv(
        FICHIER_COMMUNES,
        dtype={"numero_departement": "string", "code_insee": "string"},
    )
    date_a_recuperer = trouver_date_a_recuperer(len(communes))

    if date_a_recuperer is None:
        print("Open-Meteo est déjà à jour.")
        return

    fichier_csv = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.csv"
    fichier_parquet = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.parquet"

    collecter_communes(communes, date_a_recuperer, fichier_csv)
    actualisation = creer_parquet(fichier_csv, fichier_parquet)

    print("\nCOLLECTE TERMINÉE")
    print(f"Communes : {len(actualisation)}/{len(communes)}")
    print(f"Parquet : {fichier_parquet}")

    if len(actualisation) != len(communes):
        raise RuntimeError(
            f"Envoi impossible : {len(actualisation)} communes sur {len(communes)}."
        )

    print("\nEnvoi vers Google Cloud...")
    chemin_gcs = f"{DOSSIER_GCS_OPENMETEO}/{fichier_parquet.name}"
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"Fichier envoyé : {adresse_gcs}")
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING_OPENMETEO,
        len(communes),
    )

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    fusionner_historique_openmeteo(client_bigquery)


def main_incendie(mode_local: bool = False) -> None:
    """Orchestre la collecte incendie et son chargement dans BigQuery."""

    api_key = lire_api_key()
    configurer_google_cloud()
    DOSSIER_INCENDIE.mkdir(parents=True, exist_ok=True)

    print("\nACTUALISATION MÉTÉO DES FORÊTS")
    donnees_api = recuperer_meteo_forets(api_key)
    donnees_incendie = preparer_donnees(donnees_api)
    fichier_parquet = enregistrer_parquet_incendie(donnees_incendie)
    reference_time = donnees_incendie["reference_time"].iloc[0]

    print(f"Départements : {len(donnees_incendie)}/{NOMBRE_DEPARTEMENTS_ATTENDU}")
    print(f"Publication : {reference_time}")
    print(f"Parquet : {fichier_parquet}")

    if mode_local:
        print("Mode local : aucun envoi vers Google Cloud.")
        return

    print("\nEnvoi vers Google Cloud...")
    chemin_gcs = (
        f"{DOSSIER_GCS_INCENDIE}/"
        f"{reference_time:%Y/%m/%d}/{fichier_parquet.name}"
    )
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"Fichier envoyé : {adresse_gcs}")

    client_bigquery = bigquery.Client(project=PROJET_GCP)
    preparer_datasets_bigquery(client_bigquery)
    charger_parquet_bigquery(
        adresse_gcs,
        TABLE_LANDING_INCENDIE,
        NOMBRE_DEPARTEMENTS_ATTENDU,
    )
    fusionner_historique_incendie(client_bigquery)
    print("\nActualisation incendie terminée.")


def main() -> None:
    """Lance les deux pipelines ou seulement celui demandé en argument."""

    openmeteo_seul = "--openmeteo-only" in sys.argv
    incendie_seul = "--incendie-only" in sys.argv
    mode_local = "--local-only" in sys.argv

    if openmeteo_seul and incendie_seul:
        raise ValueError("Choisis un seul pipeline à lancer.")

    if mode_local and not incendie_seul:
        raise ValueError("Utilise --local-only avec --incendie-only.")

    print("\nACTUALISATION FOURCASTERS")

    if not incendie_seul:
        print("\n1. Open-Meteo")
        main_openmeteo()

    if not openmeteo_seul:
        print("\n2. Météo-France - danger incendie")
        main_incendie(mode_local=mode_local)

    print("\nActualisation Fourcasters terminée.")


if __name__ == "__main__":
    main()
