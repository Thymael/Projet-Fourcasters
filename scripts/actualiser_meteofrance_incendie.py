"""Actualise la Météo des forêts directement dans BigQuery."""

import csv                                                                                         # Lit le CSV renvoyé par Météo-France.
import hashlib                                                                                     # Crée un identifiant unique par ligne.
import io                                                                                          # Lit le contenu CSV en mémoire.
import os                                                                                          # Lit la clé API depuis l'environnement.
from datetime import datetime, timezone                                                            # Ajoute la date d'insertion.
from pathlib import Path                                                                           # Construit les chemins du projet.

import requests                                                                                    # Interroge l'API Météo-France.
from dotenv import load_dotenv                                                                     # Charge les variables locales du fichier .env.
from google.cloud import bigquery                                                                  # Lit et alimente BigQuery.


# ============================================================
# 1. PARAMÈTRES
# ============================================================

RACINE_PROJET = Path(__file__).resolve().parents[1]                                                 # Racine du dépôt.
URL_API = "https://public-api.meteofrance.fr/public/DPMeteoForets/v1/carte/encours"

PROJET_GCP = "fourcasters-openmeteo-loick"
TABLE_INCENDIE = f"{PROJET_GCP}.meteofrance_raw.meteo_forets"

load_dotenv(RACINE_PROJET / ".env")                                                                # Charge les secrets locaux.
CLE_API = os.getenv("METEOFRANCE_API_KEY")
client = bigquery.Client()


# ============================================================
# 2. FONCTIONS
# ============================================================

def creer_table():
    schema = [
        bigquery.SchemaField("reference_time", "TIMESTAMP"),
        bigquery.SchemaField("dep_code", "STRING"),
        bigquery.SchemaField("nom_dep", "STRING"),
        bigquery.SchemaField("niveau_j1", "INTEGER"),
        bigquery.SchemaField("niveau_j2", "INTEGER"),
        bigquery.SchemaField("row_hash", "STRING"),
        bigquery.SchemaField("insere_a", "TIMESTAMP"),
    ]

    table = bigquery.Table(TABLE_INCENDIE, schema=schema)
    client.create_table(table, exists_ok=True)                                                     # Crée la table au premier lancement.


def creer_hash(reference_time, dep_code):
    cle = f"{reference_time}|{dep_code}"
    return hashlib.sha256(cle.encode("utf-8")).hexdigest()


def recuperer_donnees():
    if not CLE_API:
        raise RuntimeError("METEOFRANCE_API_KEY absente du fichier .env")

    headers = {
        "apikey": CLE_API,
        "accept": "*/*",
    }

    reponse = requests.get(URL_API, headers=headers, timeout=60)

    if reponse.status_code == 404:
        print("🌳 Aucune donnée Météo des forêts disponible.")
        return []

    reponse.raise_for_status()

    contenu = reponse.text.strip()

    if not contenu:
        return []

    dialecte = csv.Sniffer().sniff(contenu[:2000], delimiters=";,")                                # Détecte virgule ou point-virgule.
    lecteur = csv.DictReader(io.StringIO(contenu), dialect=dialecte)

    return list(lecteur)


def transformer_lignes(donnees):
    lignes = []

    for donnee in donnees:
        reference_time = donnee["reference_time"].strip()
        dep_code = donnee["dep_code"].strip()

        lignes.append({
            "reference_time": reference_time,
            "dep_code": dep_code,
            "nom_dep": donnee["dep_nom"].strip(),
            "niveau_j1": int(donnee["niveau_j1"]),
            "niveau_j2": int(donnee["niveau_j2"]),
            "row_hash": creer_hash(reference_time, dep_code),
            "insere_a": datetime.now(timezone.utc).isoformat(),
        })

    return lignes


def hashes_existants(lignes):
    if not lignes:
        return set()

    hashes = [ligne["row_hash"] for ligne in lignes]

    requete = f"""
        SELECT row_hash
        FROM `{TABLE_INCENDIE}`
        WHERE row_hash IN UNNEST(@hashes)
    """

    configuration = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("hashes", "STRING", hashes)
        ]
    )

    resultat = client.query(requete, job_config=configuration).result()
    return {ligne.row_hash for ligne in resultat}


# ============================================================
# 3. ACTUALISATION
# ============================================================

def main():
    creer_table()

    donnees = recuperer_donnees()

    if not donnees:
        print("✅ Rien à actualiser.")
        return

    lignes = transformer_lignes(donnees)
    deja_presents = hashes_existants(lignes)
    nouvelles_lignes = [ligne for ligne in lignes if ligne["row_hash"] not in deja_presents]

    print("\n🔥 ACTUALISATION MÉTÉO DES FORÊTS")
    print(f"📍 Départements reçus : {len(lignes)}")
    print(f"✅ Déjà présents : {len(deja_presents)}")
    print(f"➕ Nouvelles lignes : {len(nouvelles_lignes)}")

    if not nouvelles_lignes:
        print("✅ Publication déjà présente dans BigQuery.")
        return

    erreurs = client.insert_rows_json(
        TABLE_INCENDIE,
        nouvelles_lignes,
        row_ids=[ligne["row_hash"] for ligne in nouvelles_lignes],
    )

    if erreurs:
        raise RuntimeError(f"Erreur BigQuery : {erreurs}")

    print(f"🎉 {len(nouvelles_lignes)} lignes ajoutées dans BigQuery.")


if __name__ == "__main__":
    main()