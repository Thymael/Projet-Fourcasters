"""Actualise une journée Open-Meteo directement dans BigQuery."""

import hashlib                                                                                     # Crée un identifiant unique par ligne.
import time                                                                                        # Ajoute une pause entre les appels API.
from datetime import date, datetime, timedelta, timezone                                           # Gère les dates et heures.
from pathlib import Path                                                                           # Construit les chemins du projet.
from zoneinfo import ZoneInfo                                                                      # Utilise l'heure française.

import pandas as pd                                                                                # Lit le référentiel des communes.
import requests                                                                                    # Interroge l'API Open-Meteo.
from google.cloud import bigquery                                                                  # Lit et alimente BigQuery.
from dotenv import load_dotenv                                                                     # Charge les variables locales du fichier .env.


# ============================================================
# 1. PARAMÈTRES DU PROJET
# ============================================================

RACINE_PROJET = Path(__file__).resolve().parents[1]                                                 # Racine du dépôt Fourcasters.
FICHIER_COMMUNES = RACINE_PROJET / "fourcasters" / "seeds" / "referentiel_communes.csv"            # Référentiel des 360 communes.

PROJET_GCP = "fourcasters-openmeteo-loick"                                                         # Projet Google Cloud.
TABLE_METEO = f"{PROJET_GCP}.openmeteo_raw.meteo_journaliere"                                     # Table météo historique.
DATE_DEBUT = date(2026, 8, 1)                                                                      # Première journée après l'historique.
RETARD_ERA5 = 6                                                                                    # Marge avant disponibilité des données ERA5.
PAUSE_API = 3                                                                                      # Pause entre deux communes.
TENTATIVES_API = 3                                                                                 # Nombre maximal d'essais par commune.

load_dotenv(RACINE_PROJET / ".env")                                                                # Charge la configuration locale.
client = bigquery.Client()                                                                         # Utilise les identifiants Google disponibles.


# ============================================================
# 2. VARIABLES MÉTÉO
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
# 3. FONCTIONS
# ============================================================

def creer_hash(jour, commune):
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
        jour = DATE_DEBUT                                                                           # Commence après l'historique initial.
    elif resultat[0].lignes < nombre_communes:
        jour = resultat[0].jour                                                                     # Reprend une journée incomplète.
    else:
        jour = resultat[0].jour + timedelta(days=1)                                                 # Passe à la journée suivante.

    aujourdhui = datetime.now(ZoneInfo("Europe/Paris")).date()                                      # Utilise la date française.
    dernier_jour_disponible = aujourdhui - timedelta(days=RETARD_ERA5)

    if jour > dernier_jour_disponible:
        return None                                                                                     # Rien à actualiser aujourd'hui.

    return jour


def hashes_existants(jour):
    requete = f"""
        SELECT row_hash
        FROM `{TABLE_METEO}`
        WHERE DATE(time) = '{jour.isoformat()}'
    """

    return {ligne.row_hash for ligne in client.query(requete).result()}                             # Repère les lignes déjà présentes.


def recuperer_meteo(commune, jour):
    url = "https://archive-api.open-meteo.com/v1/archive"                                           # API historique Open-Meteo.

    parametres = {
        "latitude": float(commune["latitude"]),
        "longitude": float(commune["longitude"]),
        "start_date": jour.isoformat(),
        "end_date": jour.isoformat(),
        "daily": ",".join(VARIABLES_METEO),
        "timezone": "Europe/Paris",
        "models": "era5_seamless",
    }

    for tentative in range(1, TENTATIVES_API + 1):
        try:
            reponse = requests.get(url, params=parametres, timeout=120)                             # Attend au maximum deux minutes.

            if reponse.status_code == 429:
                print(f"   🚦 Limite API : pause de 61 s ({tentative}/{TENTATIVES_API})")
                time.sleep(61)
                continue

            reponse.raise_for_status()
            donnees = reponse.json()

            if donnees.get("error"):
                raise ValueError(donnees.get("reason", "Erreur Open-Meteo"))

            daily = donnees.get("daily", {})

            if not daily.get("time") or daily.get("temperature_2m_mean", [None])[0] is None:
                raise ValueError("Données journalières incomplètes.")

            return daily

        except (requests.RequestException, ValueError, KeyError) as erreur:
            if tentative < TENTATIVES_API:
                print(f"   ⏳ Nouvel essai : {erreur}")
                time.sleep(10)
            else:
                print(f"   ❌ Échec après {TENTATIVES_API} tentatives : {erreur}")

    return None


def creer_ligne(commune, daily, jour):
    ligne = {
        "time": f"{jour.isoformat()}T00:00:00+00:00",
        "code_insee": str(commune["code_insee"]).strip(),                                         # Identifie le point via le référentiel.
        "row_hash": creer_hash(jour, commune),                                                     # Clé unique date + code INSEE.
        "insere_a": datetime.now(timezone.utc).isoformat(),                                        # Date d'insertion dans BigQuery.
    }

    for variable in VARIABLES_METEO:
        valeurs = daily.get(variable)                                                              # Une valeur par journée.
        ligne[variable] = valeurs[0] if valeurs else None

    return ligne


# ============================================================
# 4. ACTUALISATION
# ============================================================

def main():
    communes = pd.read_csv(
    FICHIER_COMMUNES,
    dtype={"numero_departement": "string", "code_insee": "string"},)                                # Préserve les zéros des codes.
    jour = trouver_date_a_recuperer(len(communes))                                                  # Choisit la prochaine journée utile.

    if jour is None:
        print("\n✅ Aucune nouvelle journée ERA5 disponible.")
        return

    deja_presents = hashes_existants(jour)                                                           # Permet de reprendre après une coupure.

    print("\n🌤️  ACTUALISATION OPEN-METEO")
    print(f"📅 Date : {jour}")
    print(f"📍 Communes : {len(communes)}")
    print(f"✅ Déjà présentes : {len(deja_presents)}")

    reussites = len(deja_presents)
    echecs = 0

    for numero, (_, commune) in enumerate(communes.iterrows(), start=1):
        row_hash = creer_hash(jour, commune)

        if row_hash in deja_presents:
            continue                                                                               # Ignore les communes déjà enregistrées.

        nom = str(commune["commune"]).strip()
        departement = str(commune["numero_departement"]).strip()
        daily = recuperer_meteo(commune, jour)

        if daily is None:
            echecs += 1
            print(f"❌ {numero:03}/{len(communes)} - {nom} ({departement})")
            continue

        ligne = creer_ligne(commune, daily, jour)
        erreurs = client.insert_rows_json(TABLE_METEO, [ligne], row_ids=[row_hash])                 # Envoie directement la ligne dans BigQuery.

        if erreurs:
            echecs += 1
            print(f"❌ {numero:03}/{len(communes)} - {nom} ({departement}) - {erreurs}")
            continue

        reussites += 1
        print(f"✅ {numero:03}/{len(communes)} - {nom} ({departement})")
        time.sleep(PAUSE_API)                                                                       # Évite d'enchaîner les appels trop vite.

    print("\n📊 BILAN")
    print(f"✅ Communes présentes : {reussites}/{len(communes)}")
    print(f"❌ Échecs : {echecs}")

    if reussites == len(communes):
        print("🎉 Journée complète dans BigQuery.")
    else:
        print("⚠️ Journée incomplète : relance simplement le script.")


if __name__ == "__main__":
    main()