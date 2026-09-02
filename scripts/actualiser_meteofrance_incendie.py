"""Actualise une journée Open-Meteo pour les 360 communes de Fourcasters."""

import hashlib  # Pour créer un identifiant unique par ligne.
import os  # Pour retrouver la clé Google Cloud.
import time  # Pour faire une pause entre les requêtes.
from datetime import date, datetime, timedelta, timezone  # Pour gérer les dates.
from pathlib import Path  # Pour construire les chemins des fichiers.
from zoneinfo import ZoneInfo  # Pour utiliser l'heure française.

import pandas as pd  # Pour préparer les tableaux de données.
import requests  # Pour interroger l'API Open-Meteo.
from google.cloud import bigquery, storage  # Pour envoyer les données vers GCP.


# ============================================================
# 1. PARAMÈTRES DU PROJET
# ============================================================

dossier_projet = Path(__file__).resolve().parents[1]  # Racine du dépôt.
fichier_communes = dossier_projet / "fourcasters" / "seeds" / "referentiel_communes.csv"  # Les 360 communes.
dossier_sortie = dossier_projet / "data" / "actualisation"  # Fichiers temporaires.
dossier_sortie.mkdir(parents=True, exist_ok=True)  # Crée le dossier s'il manque.

taille_lot = 10  # Dix communes sont envoyées dans la même requête.
pause = 10  # Pause en secondes entre deux lots.
nombre_tentatives = 3  # Un lot peut être essayé trois fois.

projet_gcp = "fourcasters-openmeteo-loick"  # Projet Google Cloud.
fichier_cle_gcp = "C:/dev/cle_bigquery.json"  # Clé utilisée seulement en local.
nom_bucket = "fourcasters-openmeteo-loick-data"  # Bucket Cloud Storage.
dossier_gcs = "landing/actualisation"  # Dossier du bucket.
table_landing = f"{projet_gcp}.openmeteo_landing.meteo_actualisation"  # Table temporaire.
table_historique = f"{projet_gcp}.openmeteo_raw.meteo_journaliere"  # Table finale.

# En local, on utilise la clé présente sur le PC.
# Dans GitHub Actions, l'authentification est déjà fournie par le workflow.
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = fichier_cle_gcp


# ============================================================
# 2. VARIABLES MÉTÉO À RÉCUPÉRER
# ============================================================

variables_meteo = [
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
# 3. DATE À RÉCUPÉRER
# ============================================================

def trouver_date_a_recuperer():
    """Choisit la journée qui suit la dernière date présente dans BigQuery."""

    date_minimum = date(2026, 8, 1)  # Le premier jour après l'historique initial.
    aujourdhui_paris = datetime.now(ZoneInfo("Europe/Paris")).date()  # Date française.
    date_maximum = aujourdhui_paris - timedelta(days=6)  # ERA5 arrive avec du retard.

    client = bigquery.Client(project=projet_gcp)  # Connexion à BigQuery.
    requete = f"""
        SELECT MAX(DATE(time)) AS derniere_date
        FROM `{table_historique}`
    """

    resultat = list(client.query(requete).result())  # Exécute la requête.
    derniere_date = resultat[0].derniere_date  # Dernière journée déjà chargée.

    if derniere_date is None:
        date_demandee = date_minimum
    else:
        date_demandee = derniere_date + timedelta(days=1)

    if date_demandee > date_maximum:
        raise ValueError(
            "❌ - Aucune nouvelle journée ERA5 n'est encore disponible.\n"
            f"📅 - Dernière date autorisée : {date_maximum}")

    return date_demandee.isoformat()  # Format attendu par Open-Meteo.


# ============================================================
# 4. PRÉPARATION D'UNE COMMUNE
# ============================================================

def cle_commune(commune):
    """Crée une clé simple pour reconnaître une commune."""

    nom = str(commune["commune"]).strip()  # Retire les espaces inutiles.
    departement = str(commune["numero_departement"]).strip()  # Garde les 01, 02, etc.
    return nom, departement


def preparer_commune(donnees_commune, commune, date_a_recuperer):
    """Transforme la réponse d'une commune en une ligne prête pour BigQuery."""

    if "daily" not in donnees_commune:
        raise ValueError(f"Aucune donnée reçue pour {commune['commune']}.")

    df_meteo = pd.DataFrame(donnees_commune["daily"])  # Transforme le JSON en tableau.

    if len(df_meteo) != 1:
        raise ValueError(f"Une seule ligne était attendue pour {commune['commune']}.")

    nom_commune, numero_departement = cle_commune(commune)
    latitude = float(commune["latitude"])
    longitude = float(commune["longitude"])

    # Colonnes utilisées par la suite du projet.
    df_meteo["nom_poi"] = nom_commune
    df_meteo["numero_departement"] = numero_departement
    df_meteo["latitude_poi"] = latitude
    df_meteo["longitude_poi"] = longitude
    df_meteo["ville"] = nom_commune
    df_meteo["departement"] = commune["departement"]
    df_meteo["latitude"] = latitude
    df_meteo["longitude"] = longitude

    cle_hash = f"{date_a_recuperer}|{nom_commune}|{numero_departement}"  # Clé stable.
    df_meteo["row_hash"] = hashlib.sha256(cle_hash.encode("utf-8")).hexdigest()
    df_meteo["insere_a"] = datetime.now(timezone.utc)
    df_meteo["time"] = pd.to_datetime(df_meteo["time"], utc=True)

    for variable in variables_meteo:
        df_meteo[variable] = pd.to_numeric(
            df_meteo[variable], errors="coerce").astype("float64")

    return df_meteo


# ============================================================
# 5. REQUÊTE OPEN-METEO PAR LOT
# ============================================================

def recuperer_lot(lot_communes, date_a_recuperer):
    """Récupère la météo de 10 communes avec une seule requête."""

    url = "https://archive-api.open-meteo.com/v1/archive"  # API historique.
    latitudes = ",".join(lot_communes["latitude"].astype(str))  # Regroupe les latitudes.
    longitudes = ",".join(lot_communes["longitude"].astype(str))  # Regroupe les longitudes.

    parametres = {
        "latitude": latitudes,
        "longitude": longitudes,
        "start_date": date_a_recuperer,
        "end_date": date_a_recuperer,
        "daily": ",".join(variables_meteo),
        "timezone": "Europe/Paris",
        "models": "era5_seamless",
    }

    for tentative in range(1, nombre_tentatives + 1):
        try:
            print(f"   Tentative {tentative}/{nombre_tentatives}")
            reponse = requests.get(url, params=parametres, timeout=120)  # Attend au maximum 2 minutes.

            if reponse.status_code == 429:
                if tentative == nombre_tentatives:
                    raise RuntimeError("Open-Meteo bloque toujours les requêtes.")

                print("   🚦 - Limite API : pause de 61 secondes...")
                time.sleep(61)
                continue

            reponse.raise_for_status()
            donnees_api = reponse.json()  # Récupère le contenu de la réponse.

            # Avec une seule commune, Open-Meteo ne renvoie pas une liste.
            if isinstance(donnees_api, dict):
                donnees_api = [donnees_api]

            if len(donnees_api) != len(lot_communes):
                raise ValueError("Le nombre de réponses ne correspond pas au lot envoyé.")

            lignes = []  # Contiendra les dix communes du lot.

            for position in range(len(lot_communes)):
                commune = lot_communes.iloc[position]  # Commune envoyée à cette position.
                donnees_commune = donnees_api[position]  # Réponse située à la même position.
                df_commune = preparer_commune(
                    donnees_commune, commune, date_a_recuperer)
                lignes.append(df_commune)

            return pd.concat(lignes, ignore_index=True)

        except (requests.RequestException, ValueError, KeyError) as erreur:
            print(f"   ❌ - Échec : {erreur}")

            if tentative < nombre_tentatives:
                print("   ⏳ - Nouvel essai dans 10 secondes...")
                time.sleep(10)

    return None


# ============================================================
# 6. COLLECTE DES 360 COMMUNES
# ============================================================

date_a_recuperer = trouver_date_a_recuperer()  # Prochaine date absente de BigQuery.
fichier_csv = dossier_sortie / f"openmeteo_{date_a_recuperer}.csv"  # Fichier de suivi.
fichier_parquet = dossier_sortie / f"openmeteo_{date_a_recuperer}.parquet"  # Fichier envoyé.

df_communes = pd.read_csv(
    fichier_communes, dtype={"numero_departement": "string"})

# Le CSV permet de reprendre uniquement les communes manquantes.
if fichier_csv.exists():
    df_deja_recupere = pd.read_csv(
        fichier_csv, dtype={"numero_departement": "string"})
    communes_reussies = set(zip(
        df_deja_recupere["nom_poi"],
        df_deja_recupere["numero_departement"]))
else:
    communes_reussies = set()

indices_a_traiter = []  # Liste des communes encore absentes.

for index, commune in df_communes.iterrows():
    if cle_commune(commune) not in communes_reussies:
        indices_a_traiter.append(index)

communes_a_traiter = df_communes.loc[indices_a_traiter]  # Retire les communes déjà réussies.
departs_des_lots = range(0, len(communes_a_traiter), taille_lot)  # 0, 10, 20, etc.
nombre_lots = len(departs_des_lots)  # Nombre de requêtes prévues.

print("\n🌤️  ACTUALISATION OPEN-METEO")
print(f"Date : {date_a_recuperer}")
print(f"Communes déjà récupérées : {len(communes_reussies)}")
print(f"Lots à traiter : {nombre_lots}")

for numero_lot, debut in enumerate(departs_des_lots, start=1):
    lot_communes = communes_a_traiter.iloc[debut:debut + taille_lot]

    print(f"\n📦 Lot {numero_lot}/{nombre_lots} - {len(lot_communes)} communes")
    df_lot = recuperer_lot(lot_communes, date_a_recuperer)

    if df_lot is None:
        print("   ❌ Lot abandonné après 3 tentatives.")
        continue

    # Chaque lot est sauvegardé tout de suite pour ne rien perdre.
    df_lot.to_csv(
        fichier_csv,
        mode="a",
        header=not fichier_csv.exists(),
        index=False,
        encoding="utf-8-sig")

    print(f"   ✅ {len(df_lot)} communes ajoutées au CSV.")

    if numero_lot < nombre_lots:
        time.sleep(pause)


# ============================================================
# 7. CRÉATION ET CONTRÔLE DU PARQUET
# ============================================================

if not fichier_csv.exists():
    raise ValueError("Aucune commune n'a été récupérée.")

df_actualisation = pd.read_csv(
    fichier_csv, dtype={"numero_departement": "string"})
df_actualisation = df_actualisation.drop_duplicates("row_hash", keep="last")  # Évite les doublons.
df_actualisation["time"] = pd.to_datetime(df_actualisation["time"], utc=True)
df_actualisation["insere_a"] = pd.to_datetime(
    df_actualisation["insere_a"], utc=True)

for variable in variables_meteo:
    df_actualisation[variable] = pd.to_numeric(
        df_actualisation[variable], errors="coerce").astype("float64")

df_actualisation.to_parquet(fichier_parquet, index=False)  # Format utilisé par BigQuery.

nombre_reussites = len(df_actualisation)
nombre_attendu = len(df_communes)

print("\n✅ COLLECTE TERMINÉE")
print(f"Communes : {nombre_reussites}/{nombre_attendu}")
print(f"Parquet : {fichier_parquet}")

if nombre_reussites != nombre_attendu:
    raise RuntimeError(
        f"Envoi impossible : {nombre_reussites} communes sur {nombre_attendu}.")


# ============================================================
# 8. ENVOI VERS CLOUD STORAGE
# ============================================================

def envoyer_parquet_gcs():
    """Envoie le Parquet dans le bucket du projet."""

    client = storage.Client(project=projet_gcp)  # Connexion à Cloud Storage.
    bucket = client.bucket(nom_bucket)  # Sélectionne le bucket.
    chemin_gcs = f"{dossier_gcs}/{fichier_parquet.name}"  # Emplacement du fichier.
    fichier_gcs = bucket.blob(chemin_gcs)  # Prépare le fichier distant.

    fichier_gcs.upload_from_filename(str(fichier_parquet))
    adresse_gcs = f"gs://{nom_bucket}/{chemin_gcs}"

    print(f"☁️ Fichier envoyé : {adresse_gcs}")
    return adresse_gcs


# ============================================================
# 9. CHARGEMENT DANS BIGQUERY
# ============================================================

def charger_parquet_bigquery(adresse_gcs):
    """Remplace la table temporaire par la nouvelle journée."""

    client = bigquery.Client(project=projet_gcp)  # Connexion à BigQuery.
    configuration = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)

    chargement = client.load_table_from_uri(
        adresse_gcs, table_landing, job_config=configuration)
    chargement.result()  # Attend la fin du chargement.

    table = client.get_table(table_landing)

    if table.num_rows != nombre_attendu:
        raise ValueError(
            f"BigQuery contient {table.num_rows} lignes "
            f"au lieu de {nombre_attendu}.")

    print(f"✅ Table chargée : {table_landing}")


# ============================================================
# 10. ENVOI AUTOMATIQUE
# ============================================================

print("\n☁️ Envoi vers Google Cloud...")
adresse_gcs = envoyer_parquet_gcs()
charger_parquet_bigquery(adresse_gcs)

# La fusion dans l'historique et les modèles dbt sont lancés
# juste après ce script par GitHub Actions.
