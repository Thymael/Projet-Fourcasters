"""Récupère une journée météo pour les 360 communes de Fourcasters."""

import hashlib  # Pour créer le row_hash.
import subprocess  # Pour lancer les commandes dbt depuis Python.
import time  # Pour utiliser time.sleep().
from datetime import date, datetime, timedelta, timezone  # Pour les dates et insere_a.
from pathlib import Path  # Pour les chemins de dossiers.

import pandas as pd  # Bah, pour Pandas ! xD
import requests  # Pour interroger l'API Open-Meteo.
from google.cloud import bigquery, storage  # Pour envoyer les données sur Google Cloud.
from google.oauth2 import service_account  # Pour utiliser les droits de la clé locale.

# ============================================================
# 1. PARAMÈTRES
# ============================================================

dossier_projet = Path(r"C:\dev\Projet_Fourcasters")
fichier_communes = dossier_projet / "fourcasters" / "seeds" / "referentiel_communes.csv"
dossier_sortie = dossier_projet / "data" / "actualisation"

pause = 2  # Pause entre deux communes.
nombre_tentatives = 3  # Nombre d'essais par commune.

projet_gcp = "fourcasters-openmeteo-loick"
fichier_cle_gcp = "C:/dev/cle_bigquery.json"
nom_bucket = "fourcasters-openmeteo-loick-data"
dossier_gcs = "landing/actualisation"
table_landing = f"{projet_gcp}.openmeteo_landing.meteo_actualisation"

# ============================================================
# 2. VARIABLES MÉTÉO
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
    "soil_temperature_0_to_7cm_mean",]

# ============================================================
# 3. DATE À RÉCUPÉRER
# ============================================================

dossier_sortie.mkdir(parents=True, exist_ok=True)

print("\n====================================")
print("🌤️  ACTUALISATION OPEN-METEO  🌤️")
print("====================================")

# Le dernier CSV indique la dernière date commencée.
fichiers_existants = sorted(dossier_sortie.glob("openmeteo_????-??-??.csv"))

if fichiers_existants:
    derniere_date = fichiers_existants[-1].stem.replace("openmeteo_", "")
    print(f"📋 - Dernière date commencée : {derniere_date}")
else:
    print("📋 - Aucune date n'a encore été récupérée.")

# L'historique  se termine le 31 juillet 2026.
# La nouvelle journée autorisée est donc le 1er août 2026.
date_minimum = date(2026, 8, 1)

# la date choisie doit être au plus tard à J-6.
date_maximum = date.today() - timedelta(days=6)

date_a_recuperer = input(
    f"📅 - Date à récupérer "
    f"(entre {date_minimum} et {date_maximum}) : ").strip()

try:
    date_demandee = datetime.strptime(
        date_a_recuperer,
        "%Y-%m-%d").date()
except ValueError as erreur:
    raise ValueError(
        "❌ - La date doit être écrite au format AAAA-MM-JJ.") from erreur

# Empêche de récupérer une date déjà présente dans l'historique.
if date_demandee < date_minimum:
    raise ValueError(
        "❌ - Cette date appartient déjà à l'historique BigQuery.\n"
        f"📅 - Première date autorisée : {date_minimum}")

# Empêche de demander une date trop récente pour Open-Meteo.
if date_demandee > date_maximum:
    raise ValueError(
        "❌ - Cette date est trop récente pour Open-Meteo.\n"
        f"📅 - Dernière date autorisée : {date_maximum}")

fichier_csv = dossier_sortie / f"openmeteo_{date_a_recuperer}.csv"
fichier_parquet = dossier_sortie / f"openmeteo_{date_a_recuperer}.parquet"

# ============================================================
# 4. COMMUNES DÉJÀ RÉUSSIES
# ============================================================

df_communes = pd.read_csv(fichier_communes, dtype={"numero_departement": "string"})

# Le CSV sert aussi de suivi : présente = réussie, absente = à réessayer.
if fichier_csv.exists():
    df_deja_recupere = pd.read_csv(fichier_csv, dtype={"numero_departement": "string"})
    communes_reussies = set(zip(df_deja_recupere["nom_poi"], df_deja_recupere["numero_departement"]))
else:
    communes_reussies = set()

print("\n------------------------------------")
print("🚀 - DÉMARRAGE DE LA COLLECTE")
print("------------------------------------")
print(f"📅 - Date demandée          : {date_a_recuperer}")
print(f"🏙️  - Communes à traiter     : {len(df_communes)}")
print(f"✅ - Communes déjà réussies : {len(communes_reussies)}")

# ============================================================
# 5. REQUÊTE OPEN-METEO POUR UNE COMMUNE
# ============================================================

def recuperer_meteo(commune):
    """Essaie trois fois avant d'abandonner une commune."""

    url = "https://archive-api.open-meteo.com/v1/archive"
    parametres = {
        "latitude": commune["latitude"],
        "longitude": commune["longitude"],
        "start_date": date_a_recuperer,
        "end_date": date_a_recuperer,
        "daily": ",".join(variables_meteo),
        "timezone": "Europe/Paris",
        "models": "era5_seamless",}

    for tentative in range(1, nombre_tentatives + 1):
        try:
            print(f"   🔄 - Tentative {tentative}/{nombre_tentatives}")
            reponse = requests.get(url, params=parametres, timeout=300)

            # 429 = l'API demande de ralentir.
            if reponse.status_code == 429:
                if tentative < nombre_tentatives:
                    print("   🚦 - Limite API : pause de 61 secondes...")
                    time.sleep(61)
                continue

            reponse.raise_for_status()
            donnees_api = reponse.json()
            if "daily" not in donnees_api:
                raise ValueError("Aucune donnée météo reçue.")

            df_meteo = pd.DataFrame(donnees_api["daily"])
            if len(df_meteo) != 1:
                raise ValueError(f"1 ligne attendue, {len(df_meteo)} reçue(s).")

            nom_commune = str(commune["commune"]).strip()
            numero_departement = str(commune["numero_departement"]).strip()
            latitude = float(commune["latitude"])
            longitude = float(commune["longitude"])

            # Colonnes attendues par notre table BigQuery.
            df_meteo["nom_poi"] = nom_commune
            df_meteo["numero_departement"] = numero_departement
            df_meteo["latitude_poi"] = latitude
            df_meteo["longitude_poi"] = longitude
            df_meteo["ville"] = nom_commune
            df_meteo["departement"] = commune["departement"]
            df_meteo["latitude"] = latitude
            df_meteo["longitude"] = longitude

            # Même date + même commune = toujours le même row_hash.
            cle_hash = f"{date_a_recuperer}|{nom_commune}|{numero_departement}"
            df_meteo["row_hash"] = hashlib.sha256(cle_hash.encode("utf-8")).hexdigest()
            df_meteo["insere_a"] = datetime.now(timezone.utc)
            df_meteo["time"] = pd.to_datetime(df_meteo["time"], utc=True)

            for variable in variables_meteo:
                df_meteo[variable] = pd.to_numeric(df_meteo[variable], errors="coerce").astype("float64")

            return df_meteo

        except (requests.RequestException, ValueError) as erreur:
            print(f"   ❌ - Échec : {erreur}")
            if tentative < nombre_tentatives:
                print("   ⏳ - Nouvel essai dans 10 secondes...")
                time.sleep(10)

    return None

# ============================================================
# 6. BOUCLE SUR LES 360 COMMUNES
# ============================================================

for index, commune in df_communes.iterrows():
    nom_commune = str(commune["commune"]).strip()
    numero_departement = str(commune["numero_departement"]).strip()
    cle_commune = (nom_commune, numero_departement)

    print(f"\n📍 - [{index + 1}/{len(df_communes)}] - {nom_commune}")

    if cle_commune in communes_reussies:
        print("   ✅ - Déjà présente dans le CSV : commune ignorée.")
        continue

    df_commune = recuperer_meteo(commune)

    # Après trois échecs, la commune reste absente et sera retentée plus tard.
    if df_commune is None:
        print("   ❌ - Commune abandonnée après 3 tentatives.")
        time.sleep(pause)
        continue

    # Sauvegarde immédiate pour ne rien perdre si le programme s'arrête.
    df_commune.to_csv(fichier_csv, mode="a", header=not fichier_csv.exists(), index=False, encoding="utf-8-sig")
    communes_reussies.add(cle_commune)
    print("   ✅ - 1 journée récupérée et ajoutée au CSV.")
    time.sleep(pause)

# ============================================================
# 7. CRÉATION DU PARQUET
# ============================================================

if not fichier_csv.exists():
    raise ValueError("Aucune commune n'a été récupérée.")

df_actualisation = pd.read_csv(fichier_csv, dtype={"numero_departement": "string"})
df_actualisation = df_actualisation.drop_duplicates("row_hash", keep="last")
df_actualisation["time"] = pd.to_datetime(df_actualisation["time"], utc=True)
df_actualisation["insere_a"] = pd.to_datetime(df_actualisation["insere_a"], utc=True)

for variable in variables_meteo:
    df_actualisation[variable] = pd.to_numeric(df_actualisation[variable], errors="coerce").astype("float64")

df_actualisation.to_parquet(fichier_parquet, index=False)

# ============================================================
# 8. BILAN
# ============================================================

nombre_reussites = len(df_actualisation)
nombre_echecs = len(df_communes) - nombre_reussites

print("\n====================================")
print("🎉       COLLECTE TERMINÉE       🎉")
print("====================================")
print(f"📅 - Date                : {date_a_recuperer}")
print(f"✅ - Réussites           : {nombre_reussites}/{len(df_communes)}")
print(f"❌ - Communes manquantes : {nombre_echecs}")
print(f"📄 - CSV de suivi        : {fichier_csv}")
print(f"📦 - Parquet créé        : {fichier_parquet}")

if nombre_echecs > 0:
    print("🔁 - Relance la même date : seules les communes absentes seront réessayées.")

# ============================================================
# 9. ENVOI DU PARQUET DANS CLOUD STORAGE
# ============================================================

def envoyer_parquet_gcs(fichier_parquet):
    # Connexion à Google Cloud avec la clé locale.
    cle = service_account.Credentials.from_service_account_file(fichier_cle_gcp)
    client = storage.Client(project=projet_gcp, credentials=cle)

    # Préparation de l'emplacement du fichier dans le bucket.
    bucket = client.bucket(nom_bucket)
    chemin_gcs = f"{dossier_gcs}/{fichier_parquet.name}"
    fichier_gcs = bucket.blob(chemin_gcs)

    print("\n☁️  - Envoi du Parquet vers Cloud Storage...")
    fichier_gcs.upload_from_filename(str(fichier_parquet))

    adresse_gcs = f"gs://{nom_bucket}/{chemin_gcs}"
    print(f"✅ - Fichier envoyé : {adresse_gcs}")

    return adresse_gcs

# ============================================================
# 10. CHARGEMENT DU PARQUET DANS BIGQUERY
# ============================================================

def charger_parquet_bigquery(adresse_gcs, lignes_attendues):
    """Charge le Parquet dans la table temporaire et contrôle ses lignes."""

    # Connexion à BigQuery avec la même clé que pour Cloud Storage.
    cle = service_account.Credentials.from_service_account_file(fichier_cle_gcp)
    client = bigquery.Client(project=projet_gcp, credentials=cle)

    # La table temporaire est remplacée à chaque nouvelle journée.
    # La table historique openmeteo_raw.meteo_journaliere n'est pas modifiée ici.
    configuration = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)

    print("\n====================================")
    print("📥  CHARGEMENT DANS BIGQUERY  📥")
    print("====================================")
    print(f"🎯 - Table temporaire : {table_landing}")

    # BigQuery lit directement le Parquet présent dans Cloud Storage.
    chargement = client.load_table_from_uri(
        adresse_gcs,
        table_landing,
        job_config=configuration)

    # Le programme attend la fin du chargement avant de continuer.
    chargement.result()
    table = client.get_table(table_landing)

    # Le chargement est validé uniquement si toutes les communes sont présentes.
    if table.num_rows != lignes_attendues:
        raise ValueError(
            f"❌ - BigQuery contient {table.num_rows} lignes "
            f"au lieu des {lignes_attendues} attendues.")

    print(f"✅ - Table chargée : {table_landing}")
    print(f"🧮 - Nombre de lignes : {table.num_rows}/{lignes_attendues}")

# ============================================================
# 11. CONTRÔLES, FUSION ET MODÈLES DBT
# ============================================================

def lancer_dbt():
    """Contrôle, fusionne puis reconstruit les modèles météo."""

    dossier_dbt = dossier_projet / "fourcasters"

    print("\n====================================")
    print("🧪  CONTRÔLES ET FUSION DBT  🧪")
    print("====================================")

    try:
        # Vérifie les 360 lignes temporaires avant de toucher à l'historique.
        print("🔎 - Contrôle de la table temporaire...")
        subprocess.run([
            "uv", "run", "dbt", "test",
            "--project-dir", str(dossier_dbt),
            "--select", "source:openmeteo_landing.meteo_actualisation"],
            cwd=dossier_projet,
            check=True)

        # Ajoute seulement les row_hash absents de la table historique.
        print("\n🧲 - Fusion avec l'historique...")
        subprocess.run([
            "uv", "run", "dbt", "run-operation", "fusionner_actualisation",
            "--project-dir", str(dossier_dbt)],
            cwd=dossier_projet,
            check=True)

        # Recalcule le staging et tous les modèles qui en dépendent.
        print("\n🛠️  - Reconstruction des modèles météo...")
        subprocess.run([
            "uv", "run", "dbt", "build",
            "--project-dir", str(dossier_dbt),
            "--select", "stg_meteo_journaliere+"],
            cwd=dossier_projet,
            check=True)

    except subprocess.CalledProcessError as erreur:
        raise RuntimeError(
            "❌ - dbt a rencontré une erreur. Le Parquet et la table "
            "temporaire sont conservés pour pouvoir reprendre.") from erreur

    print("\n====================================")
    print("🎉  ACTUALISATION TERMINÉE  🎉")
    print("====================================")
    print("✅ - Archive Cloud Storage créée.")
    print("✅ - Historique BigQuery complété.")
    print("✅ - Modèles dbt reconstruits et testés.")

# ============================================================
# 12. CONFIRMATION DE L'UTILISATEUR
# ============================================================

# Le fichier ne peut être envoyé que si toutes les communes sont présentes.
if len(df_actualisation) == len(df_communes):
    print("\n====================================")
    print("☁️  ENVOI VERS GOOGLE CLOUD  ☁️")
    print("====================================")
    print(f"📅 - Date : {date_a_recuperer}")
    print(f"🏙️  - Communes : {len(df_actualisation)}/{len(df_communes)}")
    print(f"📦 - Fichier : {fichier_parquet.name}")

    confirmation = input(
        "\n❓ - Les contrôles sont-ils corrects ? Envoyer et charger le fichier ? "
        "(oui/non) : ").strip().lower()

    if confirmation == "oui":
        adresse_gcs = envoyer_parquet_gcs(fichier_parquet)
        charger_parquet_bigquery(adresse_gcs, len(df_communes))
        lancer_dbt()
    else:
        print("⏸️  - Envoi et chargement annulés. Le fichier reste disponible localement.")
else:
    print(
        f"❌ - Envoi impossible : {len(df_actualisation)} communes récupérées "
        f"sur {len(df_communes)} attendues.")
