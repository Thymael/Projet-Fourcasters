"""Fonctions Google Cloud communes aux pipelines Fourcasters."""

from pathlib import Path

from google.cloud import bigquery, storage

from fourcasters_dbt.configuration import NOM_BUCKET, PROJET_GCP


def envoyer_parquet_gcs(fichier_parquet: Path, chemin_gcs: str) -> str:
    """Envoie un Parquet dans Cloud Storage et renvoie son adresse."""

    client = storage.Client(project=PROJET_GCP)
    bucket = client.bucket(NOM_BUCKET)
    fichier_gcs = bucket.blob(chemin_gcs)
    fichier_gcs.upload_from_filename(str(fichier_parquet))

    return f"gs://{NOM_BUCKET}/{chemin_gcs}"


def charger_parquet_bigquery(
    adresse_gcs: str,
    table_destination: str,
    nombre_lignes_attendu: int,
) -> None:
    """Remplace une table BigQuery par un Parquet et contrôle sa volumétrie."""

    client = bigquery.Client(project=PROJET_GCP)
    configuration = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    chargement = client.load_table_from_uri(
        adresse_gcs,
        table_destination,
        job_config=configuration,
    )
    chargement.result()

    table = client.get_table(table_destination)

    if table.num_rows != nombre_lignes_attendu:
        raise ValueError(
            f"BigQuery contient {table.num_rows} lignes "
            f"au lieu de {nombre_lignes_attendu}."
        )

    print(f"✅ Table chargée : {table_destination}")
