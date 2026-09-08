"""Chemins et paramètres communs au projet."""

import os
from pathlib import Path

from dotenv import load_dotenv


RACINE_PROJET = Path(__file__).resolve().parents[2]
FICHIER_COMMUNES = RACINE_PROJET / "fourcasters" / "seeds" / "referentiel_communes.csv"
DOSSIER_OPENMETEO = RACINE_PROJET / "data" / "actualisation"
DOSSIER_INCENDIE = RACINE_PROJET / "data" / "actualisation_incendie"

PROJET_GCP = "fourcasters-openmeteo-loick"
NOM_BUCKET = "fourcasters-openmeteo-loick-data"
CLE_GCP_PAR_DEFAUT = RACINE_PROJET.parent / "cle_bigquery.json"

# En local, les secrets sont lus depuis .env. Ce fichier n'est jamais versionné.
load_dotenv(RACINE_PROJET / ".env")


def configurer_google_cloud() -> None:
    """Configure la clé GCP locale si aucune identité n'est déjà active."""

    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return

    # Ce chemin garde le fonctionnement historique du projet sous C:/dev.
    if CLE_GCP_PAR_DEFAUT.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CLE_GCP_PAR_DEFAUT)
        return

    raise FileNotFoundError(
        "Clé Google Cloud introuvable. Ajoute son chemin dans le fichier .env."
    )
