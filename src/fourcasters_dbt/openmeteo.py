"""Collecte quotidienne des données Open-Meteo pour Fourcasters."""

import hashlib
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from google.cloud import bigquery

from fourcasters_dbt.configuration import (
    DOSSIER_OPENMETEO,
    FICHIER_COMMUNES,
    PROJET_GCP,
    configurer_google_cloud,
)
from fourcasters_dbt.google_cloud import (
    charger_parquet_bigquery,
    envoyer_parquet_gcs,
)


URL_OPENMETEO = "https://archive-api.open-meteo.com/v1/archive"
TABLE_LANDING = f"{PROJET_GCP}.openmeteo_landing.meteo_actualisation"
TABLE_HISTORIQUE = f"{PROJET_GCP}.openmeteo_raw.meteo_journaliere"
DOSSIER_GCS = "landing/actualisation"

DATE_DEBUT_ACTUALISATION = date(2026, 8, 1)
RETARD_ERA5_JOURS = 6
TAILLE_LOT = 10
PAUSE_ENTRE_LOTS = 10
NOMBRE_TENTATIVES = 3
TIMEOUT_API = 120

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


def trouver_date_a_recuperer() -> str:
    """Renvoie la première journée absente de l'historique BigQuery."""

    date_maximum = (
        datetime.now(ZoneInfo("Europe/Paris")).date()
        - timedelta(days=RETARD_ERA5_JOURS)
    )
    requete = f"""
        SELECT MAX(DATE(time)) AS derniere_date
        FROM `{TABLE_HISTORIQUE}`
    """

    client = bigquery.Client(project=PROJET_GCP)
    derniere_date = list(client.query(requete).result())[0].derniere_date

    if derniere_date is None:
        date_demandee = DATE_DEBUT_ACTUALISATION
    else:
        date_demandee = derniere_date + timedelta(days=1)

    if date_demandee > date_maximum:
        raise ValueError(
            "Aucune nouvelle journée ERA5 n'est disponible. "
            f"Dernière date autorisée : {date_maximum}."
        )

    return date_demandee.isoformat()


def creer_cle_commune(commune: pd.Series) -> tuple[str, str]:
    """Crée une clé avec le nom et le département d'une commune."""

    nom_commune = str(commune["commune"]).strip()
    numero_departement = str(commune["numero_departement"]).strip()
    return nom_commune, numero_departement


def preparer_commune(
        donnees_commune: dict,
        commune: pd.Series,
        date_a_recuperer: str) -> pd.DataFrame:
    """Transforme la réponse d'une commune en une ligne prête pour BigQuery."""

    if "daily" not in donnees_commune:
        raise ValueError(f"Aucune donnée reçue pour {commune['commune']}.")

    meteo_commune = pd.DataFrame(donnees_commune["daily"])

    if len(meteo_commune) != 1:
        raise ValueError(f"Une seule ligne était attendue pour {commune['commune']}.")

    nom_commune, numero_departement = creer_cle_commune(commune)
    latitude = float(commune["latitude"])
    longitude = float(commune["longitude"])

    # Ces deux groupes de colonnes sont encore attendus par les modèles existants.
    meteo_commune["nom_poi"] = nom_commune
    meteo_commune["numero_departement"] = numero_departement
    meteo_commune["latitude_poi"] = latitude
    meteo_commune["longitude_poi"] = longitude
    meteo_commune["ville"] = nom_commune
    meteo_commune["departement"] = commune["departement"]
    meteo_commune["latitude"] = latitude
    meteo_commune["longitude"] = longitude

    texte_hash = f"{date_a_recuperer}|{nom_commune}|{numero_departement}"
    meteo_commune["row_hash"] = hashlib.sha256(
        texte_hash.encode("utf-8")
    ).hexdigest()
    meteo_commune["insere_a"] = datetime.now(timezone.utc)
    meteo_commune["time"] = pd.to_datetime(meteo_commune["time"], utc=True)

    for variable in VARIABLES_METEO:
        meteo_commune[variable] = pd.to_numeric(
            meteo_commune[variable], errors="coerce"
        ).astype("float64")

    return meteo_commune


def construire_parametres_api(
        communes: pd.DataFrame,
        date_a_recuperer: str) -> dict:
    """Construit les paramètres Open-Meteo d'un lot de communes."""

    return {
        "latitude": ",".join(communes["latitude"].astype(str)),
        "longitude": ",".join(communes["longitude"].astype(str)),
        "start_date": date_a_recuperer,
        "end_date": date_a_recuperer,
        "daily": ",".join(VARIABLES_METEO),
        "timezone": "Europe/Paris",
        "models": "era5_seamless",
    }


def preparer_reponse_lot(
        donnees_api,
        communes: pd.DataFrame,
        date_a_recuperer: str) -> pd.DataFrame:
    """Associe chaque réponse Open-Meteo à la commune envoyée à la même position."""

    # Pour une seule commune, l'API renvoie un objet au lieu d'une liste.
    if isinstance(donnees_api, dict):
        donnees_api = [donnees_api]

    if len(donnees_api) != len(communes):
        raise ValueError("Le nombre de réponses ne correspond pas au lot envoyé.")

    lignes = []

    for position, (_, commune) in enumerate(communes.iterrows()):
        lignes.append(
            preparer_commune(
                donnees_api[position],
                commune,
                date_a_recuperer,
            )
        )

    return pd.concat(lignes, ignore_index=True)


def recuperer_lot(
        communes: pd.DataFrame,
        date_a_recuperer: str) -> pd.DataFrame | None:
    """Récupère un lot de communes avec une seule requête Open-Meteo."""

    parametres = construire_parametres_api(communes, date_a_recuperer)

    for tentative in range(1, NOMBRE_TENTATIVES + 1):
        try:
            print(f"   Tentative {tentative}/{NOMBRE_TENTATIVES}")
            reponse = requests.get(
                URL_OPENMETEO,
                params=parametres,
                timeout=TIMEOUT_API,
            )

            if reponse.status_code == 429:
                if tentative == NOMBRE_TENTATIVES:
                    raise RuntimeError("Open-Meteo bloque toujours les requêtes.")

                print("   Limite API : pause de 61 secondes...")
                time.sleep(61)
                continue

            reponse.raise_for_status()
            return preparer_reponse_lot(
                reponse.json(),
                communes,
                date_a_recuperer,
            )

        except (requests.RequestException, ValueError, KeyError) as erreur:
            print(f"   Échec : {erreur}")

            if tentative < NOMBRE_TENTATIVES:
                print("   Nouvel essai dans 10 secondes...")
                time.sleep(10)

    return None


def lire_communes_deja_recuperees(fichier_csv: Path) -> set[tuple[str, str]]:
    """Lit le CSV de reprise et renvoie les communes déjà collectées."""

    if not fichier_csv.exists():
        return set()

    donnees_existantes = pd.read_csv(
        fichier_csv,
        dtype={"numero_departement": "string"},
    )
    return set(zip(
        donnees_existantes["nom_poi"],
        donnees_existantes["numero_departement"],
    ))


def selectionner_communes_manquantes(
        communes: pd.DataFrame,
        communes_recuperees: set[tuple[str, str]]) -> pd.DataFrame:
    """Garde uniquement les communes absentes du CSV de reprise."""

    indices_manquants = [
        index
        for index, commune in communes.iterrows()
        if creer_cle_commune(commune) not in communes_recuperees
    ]
    return communes.loc[indices_manquants]


def collecter_communes(
        communes: pd.DataFrame,
        date_a_recuperer: str,
        fichier_csv: Path):
    """Collecte et sauvegarde les communes par lots."""

    communes_recuperees = lire_communes_deja_recuperees(fichier_csv)
    communes_manquantes = selectionner_communes_manquantes(
        communes,
        communes_recuperees,
    )
    departs_lots = range(0, len(communes_manquantes), TAILLE_LOT)

    print("\nACTUALISATION OPEN-METEO")
    print(f"Date : {date_a_recuperer}")
    print(f"Communes déjà récupérées : {len(communes_recuperees)}")
    print(f"Lots à traiter : {len(departs_lots)}")

    for numero_lot, debut in enumerate(departs_lots, start=1):
        lot = communes_manquantes.iloc[debut:debut + TAILLE_LOT]
        print(f"\nLot {numero_lot}/{len(departs_lots)} - {len(lot)} communes")
        meteo_lot = recuperer_lot(lot, date_a_recuperer)

        if meteo_lot is None:
            print("   Lot abandonné après trois tentatives.")
            continue

        # La sauvegarde immédiate permet de reprendre après une interruption.
        meteo_lot.to_csv(
            fichier_csv,
            mode="a",
            header=not fichier_csv.exists(),
            index=False,
            encoding="utf-8-sig",
        )
        print(f"   {len(meteo_lot)} communes ajoutées au CSV.")

        if numero_lot < len(departs_lots):
            time.sleep(PAUSE_ENTRE_LOTS)


def creer_parquet(
        fichier_csv: Path,
        fichier_parquet: Path) -> pd.DataFrame:
    """Nettoie le CSV de reprise puis crée le Parquet à charger."""

    if not fichier_csv.exists():
        raise ValueError("Aucune commune n'a été récupérée.")

    actualisation = pd.read_csv(
        fichier_csv,
        dtype={"numero_departement": "string"},
    )
    actualisation = actualisation.drop_duplicates("row_hash", keep="last")
    actualisation["time"] = pd.to_datetime(actualisation["time"], utc=True)
    actualisation["insere_a"] = pd.to_datetime(
        actualisation["insere_a"], utc=True
    )

    for variable in VARIABLES_METEO:
        actualisation[variable] = pd.to_numeric(
            actualisation[variable], errors="coerce"
        ).astype("float64")

    actualisation.to_parquet(fichier_parquet, index=False)
    return actualisation


def main():
    """Orchestre la collecte Open-Meteo et le chargement dans BigQuery."""

    configurer_google_cloud()
    DOSSIER_OPENMETEO.mkdir(parents=True, exist_ok=True)

    date_a_recuperer = trouver_date_a_recuperer()
    fichier_csv = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.csv"
    fichier_parquet = DOSSIER_OPENMETEO / f"openmeteo_{date_a_recuperer}.parquet"
    communes = pd.read_csv(
        FICHIER_COMMUNES,
        dtype={"numero_departement": "string"},
    )

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
    chemin_gcs = f"{DOSSIER_GCS}/{fichier_parquet.name}"
    adresse_gcs = envoyer_parquet_gcs(fichier_parquet, chemin_gcs)
    print(f"Fichier envoyé : {adresse_gcs}")
    charger_parquet_bigquery(adresse_gcs, TABLE_LANDING, len(communes))

    # La fusion et dbt sont lancés ensuite par GitHub Actions.


if __name__ == "__main__":
    main()
