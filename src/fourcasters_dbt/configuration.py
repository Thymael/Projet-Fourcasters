"""Paramètres partagés par les deux pipelines Fourcasters."""

import os
from pathlib import Path


# Chemins du projet
RACINE_PROJET = Path(__file__).resolve().parents[2]
FICHIER_COMMUNES = RACINE_PROJET / "fourcasters" / "seeds" / "referentiel_communes.csv"
DOSSIER_OPENMETEO = RACINE_PROJET / "data" / "actualisation"
DOSSIER_INCENDIE = RACINE_PROJET / "data" / "actualisation_incendie"

# Google Cloud
PROJET_GCP = "fourcasters-openmeteo-loick"
CHEMIN_CLE_GCP_LOCALE = "C:/dev/cle_bigquery.json"
NOM_BUCKET = "fourcasters-openmeteo-loick-data"


def configurer_google_cloud():
    """Utilise la clé locale seulement si aucune identité GCP n'est déjà fournie."""

    # GitHub Actions fournit déjà cette variable : il ne faut pas l'écraser.
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CHEMIN_CLE_GCP_LOCALE
