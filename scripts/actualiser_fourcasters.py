"""Actualise Open-Meteo et la Météo des forêts directement dans BigQuery."""

import csv                                                                                         # Lit le CSV renvoyé par Météo-France.
import hashlib                                                                                     # Crée un identifiant unique par ligne.
import io                                                                                          # Lit le contenu CSV en mémoire.
import os                                                                                          # Lit la clé API depuis l'environnement.
import time                                                                                        # Ajoute une pause entre les appels API.
from datetime import date, datetime, timedelta, timezone                                           # Gère les dates et heures.
from pathlib import Path                                                                           # Construit les chemins du projet.
from zoneinfo import ZoneInfo                                                                      # Utilise l'heure française.

import pandas as pd                                                                                # Lit le référentiel des communes.
import requests                                                                                    # Interroge les API météo.
from dotenv import load_dotenv                                                                     # Charge les variables locales du fichier .env.
from google.cloud import bigquery                                                                  # Lit et alimente BigQuery.


# ============================================================
# 1. PARAMÈTRES DU PROJET
# ============================================================

RACINE_PROJET = Path(__file__).resolve().parents[1]                                                 # Racine du dépôt Fourcasters.
FICHIER_COMMUNES = RACINE_PROJET / "fourcasters" / "seeds" / "referentiel_communes.csv"            # Référentiel des 360 communes.

PROJET_GCP = "fourcasters-openmeteo-loick"                                                         # Projet Google Cloud.
TABLE_METEO = f"{PROJET_GCP}.openmeteo_raw.meteo_journaliere"                                     # Table météo historique.
TABLE_INCENDIE = f"{PROJET_GCP}.meteofrance_raw.meteo_forets"                                     # Table Météo des forêts.

URL_OPENMETEO = "https://archive-api.open-meteo.com/v1/archive"                                    # API historique Open-Meteo.
URL_METEOFRANCE = "https://public-api.meteofrance.fr/public/DPMeteoForets/v1/carte/encours"        # API Météo des forêts.

DATE_DEBUT = date(2026, 8, 1)                                                                      # Première journée après l'historique.
RETARD_ERA5 = 6                                                                                    # Marge avant disponibilité des données ERA5.

TAILLE_LOT = 20                                                                                    # Nombre de communes par appel Open-Meteo.
PAUSE_API = 3                                                                                      # Pause entre deux lots.
TENTATIVES_API = 2                                                                                 # Nombre maximal d'essais par lot.
TIMEOUT_API = 30                                                                                   # Temps maximal d'attente par appel Open-Meteo.

load_dotenv(RACINE_PROJET / ".env")                                                                # Charge la configuration locale.
CLE_METEOFRANCE = os.getenv("METEOFRANCE_API_KEY")                                                 # Lit la clé API Météo-France.

client = bigquery.Client()                                                                         # Utilise les identifiants Google disponibles.
session = requests.Session()                                                                       # Réutilise les connexions HTTP.


# ============================================================
# 2. VARIABLES OPEN-METEO
# ============================================================

VARIABLES_METEO = [
    "weather_code",
    "temperature_2m_mean",
    "temperature_2m_min",
    "temperature_2m_max",
    "apparent_temperature_mean",
    "apparent_temperature_min",
    "apparent_temperature_max",
    "relative_humidity_2m_mean",
    "relative_humidity_2m_min",
    "relative_humidity_2m_max",
    "dew_point_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "precipitation_hours",
    "wind_speed_10m_mean",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "cloud_cover_mean",
    "pressure_msl_mean",
    "sunshine_duration",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
    "vapour_pressure_deficit_max",
    "soil_moisture_0_to_7cm_mean",
    "soil_moisture_7_to_28cm_mean",
    "soil_moisture_28_to_100cm_mean",
    "soil_temperature_0_to_7cm_mean",
]


# ============================================================
# 3. FONCTIONS OPEN-METEO
# ============================================================

def creer_hash_openmeteo(jour, commune):
    code_insee = str(commune["code_insee"]).strip()                                                # Identifie la commune sans ambiguïté.
    cle = f"{jour}|{code_insee}"                                                                   # Clé unique : date + code INSEE.
    return hashlib.sha256(cle.encode("utf-8")).hexdigest()


def trouver_date_a_recuperer(nombre_communes):
    requete = f"""
        SELECT DATE(time) AS jour, COUNT(DISTINCT row_hash) AS lignes
        FROM `{TABLE_METEO}`
        WHERE DATE(time) >= '{DATE_DEBUT.isoformat()}'
        GROUP BY jour
        ORDER BY jour DESC
        LIMIT 1
    """

    resultat = list(client.query(requete).result())                                                 # Cherche la dernière journée chargée.

    if not resultat:
        jour = DATE_DEBUT                                                                          # Commence après l'historique initial.
    elif resultat[0].lignes < nombre_communes:
        jour = resultat[0].jour                                                                    # Reprend une journée incomplète.
    else:
        jour = resultat[0].jour + timedelta(days=1)                                                # Passe à la journée suivante.

    aujourdhui = datetime.now(ZoneInfo("Europe/Paris")).date()                                      # Utilise la date française.
    dernier_jour_disponible = aujourdhui - timedelta(days=RETARD_ERA5)

    if jour > dernier_jour_disponible:
        return None                                                                                # Rien à actualiser aujourd'hui.

    return jour


def hashes_openmeteo_existants(jour):
    requete = f"""
        SELECT row_hash
        FROM `{TABLE_METEO}`
        WHERE DATE(time) = '{jour.isoformat()}'
    """

    return {ligne.row_hash for ligne in client.query(requete).result()}                             # Repère les lignes déjà présentes.


def recuperer_meteo_lot(communes, jour):
    latitudes = ",".join(communes["latitude"].astype(str))                                         # Regroupe les coordonnées du lot.
    longitudes = ",".join(communes["longitude"].astype(str))

    parametres = {
        "latitude": latitudes,
        "longitude": longitudes,
        "start_date": jour.isoformat(),
        "end_date": jour.isoformat(),
        "daily": ",".join(VARIABLES_METEO),
        "timezone": "Europe/Paris",
        "models": "era5_seamless",
    }

    for tentative in range(1, TENTATIVES_API + 1):
        try:
            reponse = session.get(URL_OPENMETEO, params=parametres, timeout=TIMEOUT_API)            # Un appel pour tout le lot.

            if reponse.status_code == 429 and tentative < TENTATIVES_API:
                attente = int(reponse.headers.get("Retry-After", 30))
                print(f"   🚦 Limite API : pause de {attente} s")
                time.sleep(attente)
                continue

            reponse.raise_for_status()
            donnees = reponse.json()

            if isinstance(donnees, dict):
                donnees = [donnees]                                                                # Uniformise un éventuel lot d'une commune.

            if len(donnees) != len(communes):
                raise ValueError("Nombre de réponses différent du nombre de communes.")

            return donnees

        except (requests.RequestException, ValueError, KeyError) as erreur:
            if tentative < TENTATIVES_API:
                print(f"   ⏳ Nouvel essai ({tentative}/{TENTATIVES_API}) : {erreur}")
                time.sleep(5)
            else:
                print(f"   ❌ Échec du lot après {TENTATIVES_API} tentatives : {erreur}")

    return None


def creer_ligne_openmeteo(commune, daily, jour):
    ligne = {
        "time": f"{jour.isoformat()}T00:00:00+00:00",
        "code_insee": str(commune["code_insee"]).strip(),                                         # Identifie le point via le référentiel.
        "row_hash": creer_hash_openmeteo(jour, commune),                                          # Clé unique date + code INSEE.
        "insere_a": datetime.now(timezone.utc).isoformat(),                                        # Date d'insertion dans BigQuery.
    }

    for variable in VARIABLES_METEO:
        valeurs = daily.get(variable)                                                              # Une valeur par journée.
        ligne[variable] = valeurs[0] if valeurs else None

    return ligne


def actualiser_openmeteo():
    communes = pd.read_csv(
        FICHIER_COMMUNES,
        dtype={"numero_departement": "string", "code_insee": "string"},
    )                                                                                              # Préserve les zéros des codes.

    jour = trouver_date_a_recuperer(len(communes))                                                 # Choisit la prochaine journée utile.

    if jour is None:
        print("\n✅ Aucune nouvelle journée ERA5 disponible.")
        return

    deja_presents = hashes_openmeteo_existants(jour)                                               # Permet de reprendre après une coupure.

    communes["row_hash"] = communes.apply(
        lambda commune: creer_hash_openmeteo(jour, commune),
        axis=1,
    )

    communes_a_recuperer = communes[
        ~communes["row_hash"].isin(deja_presents)
    ].copy()

    total_lots = (
        len(communes_a_recuperer) + TAILLE_LOT - 1
    ) // TAILLE_LOT

    print("\n🌤️  ACTUALISATION OPEN-METEO")
    print(f"📅 Date : {jour}")
    print(f"📍 Communes : {len(communes)}")
    print(f"✅ Déjà présentes : {len(deja_presents)}")
    print(f"📦 Lots à traiter : {total_lots}")

    reussites = len(deja_presents)
    echecs = 0

    for debut in range(0, len(communes_a_recuperer), TAILLE_LOT):
        lot = communes_a_recuperer.iloc[debut:debut + TAILLE_LOT]
        numero_lot = debut // TAILLE_LOT + 1

        print(f"\n📦 Lot {numero_lot}/{total_lots} - {len(lot)} communes")

        donnees_lot = recuperer_meteo_lot(lot, jour)

        if donnees_lot is None:
            echecs += len(lot)
            continue

        lignes = []

        for (_, commune), donnees in zip(lot.iterrows(), donnees_lot):
            daily = donnees.get("daily", {})
            temperatures = daily.get("temperature_2m_mean", [])

            if not daily.get("time") or not temperatures or temperatures[0] is None:
                echecs += 1
                print(f"   ❌ Données incomplètes : {commune['commune']}")
                continue

            lignes.append(creer_ligne_openmeteo(commune, daily, jour))

        if not lignes:
            continue

        erreurs = client.insert_rows_json(
            TABLE_METEO,
            lignes,
            row_ids=[ligne["row_hash"] for ligne in lignes],
        )                                                                                          # Envoie le lot dans BigQuery.

        if erreurs:
            echecs += len(lignes)
            print(f"   ❌ Erreur BigQuery : {erreurs}")
            continue

        reussites += len(lignes)

        print(f"   ✅ {len(lignes)} lignes ajoutées")
        print(f"   📊 Progression : {reussites}/{len(communes)}")

        time.sleep(PAUSE_API)                                                                      # Petite pause avant le lot suivant.

    print("\n📊 BILAN OPEN-METEO")
    print(f"✅ Communes présentes : {reussites}/{len(communes)}")
    print(f"❌ Échecs : {echecs}")

    if reussites == len(communes):
        print("🎉 Journée Open-Meteo complète dans BigQuery.")
    else:
        print("⚠️ Journée Open-Meteo incomplète : relance simplement le script.")


# ============================================================
# 4. FONCTIONS MÉTÉO-FRANCE
# ============================================================

def creer_table_incendie():
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


def creer_hash_meteofrance(reference_time, dep_code):
    cle = f"{reference_time}|{dep_code}"                                                           # Clé unique : publication + département.
    return hashlib.sha256(cle.encode("utf-8")).hexdigest()


def recuperer_meteofrance():
    if not CLE_METEOFRANCE:
        raise RuntimeError("METEOFRANCE_API_KEY absente du fichier .env")

    headers = {
        "apikey": CLE_METEOFRANCE,
        "accept": "*/*",
    }

    reponse = session.get(URL_METEOFRANCE, headers=headers, timeout=60)

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


def transformer_lignes_meteofrance(donnees):
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
            "row_hash": creer_hash_meteofrance(reference_time, dep_code),
            "insere_a": datetime.now(timezone.utc).isoformat(),
        })

    return lignes


def hashes_meteofrance_existants(lignes):
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


def actualiser_meteofrance():
    creer_table_incendie()

    donnees = recuperer_meteofrance()

    if not donnees:
        print("\n✅ Rien à actualiser côté Météo-France.")
        return

    lignes = transformer_lignes_meteofrance(donnees)
    deja_presents = hashes_meteofrance_existants(lignes)
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


# ============================================================
# 5. PIPELINE COMPLET
# ============================================================

def main():
    print("\n============================================================")
    print("🌦️  ACTUALISATION FOURCASTERS")
    print("============================================================")

    actualiser_openmeteo()                                                                         # Met à jour les observations météo.
    actualiser_meteofrance()                                                                       # Met à jour le danger incendie.

    print("\n✅ Actualisation Fourcasters terminée.")


if __name__ == "__main__":
    main()
