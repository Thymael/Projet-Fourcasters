"""Fonctions Google Cloud communes aux pipelines Fourcasters."""

import logging
from pathlib import Path

from google.cloud import bigquery, storage

from fourcasters_dbt.configuration import NOM_BUCKET, PROJET_GCP

logger = logging.getLogger(__name__)


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

    logger.info("✅ Table de réception chargée : %s (%s lignes)", table_destination, table.num_rows)


def fusionner_historique(
    client, table_landing, table_historique, colonnes, colonne_date, colonne_code,
) -> None:
    """Fusionne le lot, puis vérifie ses clés avant de valider la transaction."""
    colonnes_sql = ", ".join(colonnes)
    valeurs = ", ".join(f"source.{colonne}" for colonne in colonnes)
    mises_a_jour = ", ".join(
        f"{colonne} = source.{colonne}" for colonne in colonnes if colonne != "row_hash"
    )
    # Le load job reste hors transaction. Seul le lot validé atteint l'historique.
    requete = f"""
        CREATE TABLE IF NOT EXISTS `{table_historique}`
        PARTITION BY DATE({colonne_date})
        CLUSTER BY {colonne_code}
        AS SELECT {colonnes_sql} FROM `{table_landing}` WHERE FALSE;

        BEGIN TRANSACTION;
        ASSERT (
            SELECT COUNT(*) > 0
                AND COUNT(*) = COUNT(DISTINCT row_hash)
            FROM `{table_landing}`
        ) AS 'Lot vide, hash manquant ou duplique';

        MERGE `{table_historique}` AS cible
        USING `{table_landing}` AS source
            ON cible.row_hash = source.row_hash
        WHEN MATCHED THEN UPDATE SET {mises_a_jour}
        WHEN NOT MATCHED THEN INSERT ({colonnes_sql}) VALUES ({valeurs});

        ASSERT (
            SELECT COUNT(*) = COUNT(DISTINCT row_hash)
            FROM `{table_historique}`
            WHERE row_hash IN (SELECT row_hash FROM `{table_landing}`)
        ) AS 'Doublons dans le lot fusionne';
        COMMIT TRANSACTION;
    """
    # BigQuery annule la transaction si MERGE ou ASSERT échoue avant COMMIT.
    client.query(requete).result()
    logger.info("✅ Historique mis à jour : %s", table_historique)
