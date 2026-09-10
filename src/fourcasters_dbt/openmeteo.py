"""Collecte quotidienne des données Open-Meteo pour Fourcasters."""

import hashlib
import logging
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from google.cloud import bigquery

from fourcasters_dbt.configuration import PROJET_GCP
from fourcasters_dbt.google_cloud import fusionner_historique
from fourcasters_dbt.http import recuperer_reponse

logger = logging.getLogger(__name__)


URL_OPENMETEO = "https://archive-api.open-meteo.com/v1/archive"
TABLE_LANDING = f"{PROJET_GCP}.openmeteo_landing.meteo_actualisation"
TABLE_HISTORIQUE = f"{PROJET_GCP}.openmeteo_raw.meteo_journaliere"
DOSSIER_GCS = "landing/actualisation"

DATE_DEBUT_ACTUALISATION = date(2026, 8, 1)
RETARD_ERA5_JOURS = 6
TAILLE_LOT = 10
PAUSE_ENTRE_LOTS = 10
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
COLONNES_BIGQUERY = [
    "time",
    "code_insee",
    "row_hash",
    "insere_a",
    *VARIABLES_METEO,
]


def trouver_date_a_recuperer(nombre_communes: int) -> str | None:
    """Cherche la première journée absente ou incomplète depuis août 2026."""

    date_maximum = (
        datetime.now(ZoneInfo("Europe/Paris")).date()
        - timedelta(days=RETARD_ERA5_JOURS)
    )
    requete = f"""
        WITH calendrier AS (
            SELECT jour FROM UNNEST(GENERATE_DATE_ARRAY(
                DATE('{DATE_DEBUT_ACTUALISATION}'), DATE('{date_maximum}')
            )) AS jour
        ),
        volumes AS (
            SELECT DATE(time) AS jour, COUNT(*) AS lignes,
                COUNT(DISTINCT code_insee) AS communes
            FROM `{TABLE_HISTORIQUE}`
            WHERE DATE(time) BETWEEN '{DATE_DEBUT_ACTUALISATION}' AND '{date_maximum}'
            GROUP BY jour
        )
        SELECT calendrier.jour
        FROM calendrier LEFT JOIN volumes USING (jour)
        WHERE COALESCE(lignes, 0) != {nombre_communes}
            OR COALESCE(communes, 0) != {nombre_communes}
        ORDER BY calendrier.jour
        LIMIT 1
    """
    client = bigquery.Client(project=PROJET_GCP)
    resultats = list(client.query(requete).result())
    if not resultats:
        logger.info("✅ Historique complet jusqu'au %s.", date_maximum)
        return None
    date_demandee = resultats[0].jour

    return date_demandee.isoformat()


def creer_cle_commune(commune: pd.Series) -> str:
    """Crée la clé stable utilisée pour reprendre une collecte interrompue."""

    return str(commune["code_insee"]).strip()


def preparer_commune(
    donnees_commune: dict,
    commune: pd.Series,
    date_a_recuperer: str,
) -> pd.DataFrame:
    """Transforme la réponse d'une commune en une ligne prête pour BigQuery."""

    meteo_commune = pd.DataFrame(donnees_commune.get("daily", {}))
    colonnes_absentes = set(["time", *VARIABLES_METEO]) - set(meteo_commune.columns)
    if colonnes_absentes:
        raise ValueError(f"Colonnes météo absentes : {sorted(colonnes_absentes)}")
    if len(meteo_commune) != 1:
        raise ValueError(f"Une ligne attendue pour {commune['commune']}.")
    jour_recu = pd.to_datetime(meteo_commune["time"], utc=True, errors="raise")
    if jour_recu.isna().any() or not (
        jour_recu.dt.date == date.fromisoformat(date_a_recuperer)
    ).all():
        raise ValueError(f"La réponse ne correspond pas au {date_a_recuperer}.")

    code_insee = creer_cle_commune(commune)
    meteo_commune["code_insee"] = code_insee

    # Le hash reprend le grain réel de la table brute : une date et un point.
    texte_hash = f"{date_a_recuperer}|{code_insee}"
    meteo_commune["row_hash"] = hashlib.sha256(
        texte_hash.encode("utf-8")
    ).hexdigest()
    meteo_commune["insere_a"] = datetime.now(timezone.utc)
    meteo_commune["time"] = pd.to_datetime(meteo_commune["time"], utc=True)

    for variable in VARIABLES_METEO:
        meteo_commune[variable] = pd.to_numeric(
            meteo_commune[variable], errors="raise"
        ).astype("float64")

    return meteo_commune


def construire_parametres_api(
    communes: pd.DataFrame,
    date_a_recuperer: str,
) -> dict[str, str]:
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
    donnees_api: dict | list[dict],
    communes: pd.DataFrame,
    date_a_recuperer: str,
) -> pd.DataFrame:
    """Associe chaque réponse Open-Meteo à la commune envoyée à la même position."""

    # Pour une seule commune, l'API renvoie un objet au lieu d'une liste.
    if isinstance(donnees_api, dict):
        donnees_api = [donnees_api]
    if not isinstance(donnees_api, list) or communes.empty:
        raise ValueError("Réponse ou lot Open-Meteo vide ou incorrect.")

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
    date_a_recuperer: str,
) -> pd.DataFrame:
    """Récupère un lot et refuse une réponse mal formée."""
    reponse = recuperer_reponse(
        URL_OPENMETEO,
        params=construire_parametres_api(communes, date_a_recuperer),
        timeout=TIMEOUT_API,
    )
    return preparer_reponse_lot(reponse.json(), communes, date_a_recuperer)


def lire_communes_deja_recuperees(fichier_csv: Path) -> set[str]:
    """Lit le CSV de reprise et renvoie les communes déjà collectées."""

    if not fichier_csv.exists() or fichier_csv.stat().st_size == 0:
        return set()

    donnees_existantes = pd.read_csv(
        fichier_csv,
        dtype={"code_insee": "string"},
    )
    codes_insee = donnees_existantes["code_insee"].dropna().str.strip()
    return set(codes_insee)


def selectionner_communes_manquantes(
    communes: pd.DataFrame,
    communes_recuperees: set[str],
) -> pd.DataFrame:
    """Garde uniquement les communes absentes du CSV de reprise."""

    codes_insee = communes["code_insee"].astype("string").str.strip()
    return communes.loc[~codes_insee.isin(communes_recuperees)].copy()


def collecter_communes(
    communes: pd.DataFrame,
    date_a_recuperer: str,
    fichier_csv: Path,
) -> None:
    """Collecte et sauvegarde les communes par lots."""

    communes_recuperees = lire_communes_deja_recuperees(fichier_csv)
    communes_manquantes = selectionner_communes_manquantes(
        communes,
        communes_recuperees,
    )
    departs_lots = range(0, len(communes_manquantes), TAILLE_LOT)

    logger.info("📅 Date : %s", date_a_recuperer)
    logger.info("Communes déjà récupérées : %s", len(communes_recuperees))
    logger.info("Lots à traiter : %s", len(departs_lots))

    for numero_lot, debut in enumerate(departs_lots, start=1):
        lot = communes_manquantes.iloc[debut:debut + TAILLE_LOT]
        logger.info("Lot %s/%s : %s communes", numero_lot, len(departs_lots), len(lot))
        meteo_lot = recuperer_lot(lot, date_a_recuperer)

        # La sauvegarde immédiate permet de reprendre après une interruption.
        meteo_lot.to_csv(
            fichier_csv,
            mode="a",
            header=not fichier_csv.exists() or fichier_csv.stat().st_size == 0,
            index=False,
            encoding="utf-8-sig",
        )
        logger.info("%s communes sauvegardées dans le CSV.", len(meteo_lot))

        if numero_lot < len(departs_lots):
            time.sleep(PAUSE_ENTRE_LOTS)


def creer_parquet(
    fichier_csv: Path,
    fichier_parquet: Path,
    communes: pd.DataFrame,
    date_a_recuperer: str,
) -> pd.DataFrame:
    """Nettoie le CSV de reprise puis crée le Parquet à charger."""

    if not fichier_csv.exists():
        raise ValueError("Aucune commune n'a été récupérée.")

    actualisation = pd.read_csv(
        fichier_csv,
        dtype={"numero_departement": "string", "code_insee": "string"},
    )
    actualisation = actualisation[COLONNES_BIGQUERY].copy()
    actualisation["code_insee"] = actualisation["code_insee"].str.strip()
    actualisation = actualisation.drop_duplicates(["time", "code_insee"], keep="last")
    actualisation["time"] = pd.to_datetime(actualisation["time"], utc=True)
    actualisation["insere_a"] = pd.to_datetime(
        actualisation["insere_a"], utc=True
    )

    for variable in VARIABLES_METEO:
        actualisation[variable] = pd.to_numeric(
            actualisation[variable], errors="raise"
        ).astype("float64")

    if set(actualisation["code_insee"]) != set(communes["code_insee"]):
        raise ValueError("La collecte ne contient pas exactement les communes du référentiel.")
    if len(actualisation) != len(communes):
        raise ValueError("Une seule ligne par commune est attendue.")
    if actualisation["time"].isna().any() or not (
        actualisation["time"].dt.date == date.fromisoformat(date_a_recuperer)
    ).all():
        raise ValueError("Le CSV de reprise contient une autre date.")
    if actualisation["insere_a"].isna().any():
        raise ValueError("Une date de collecte est manquante.")
    if actualisation[VARIABLES_METEO].isin([float("inf"), -float("inf")]).any().any():
        raise ValueError("Une valeur météo est infinie.")
    hashes_attendus = actualisation["code_insee"].map(
        lambda code: hashlib.sha256(f"{date_a_recuperer}|{code}".encode()).hexdigest()
    )
    if not actualisation["row_hash"].eq(hashes_attendus).all():
        raise ValueError("Les clés du CSV ne correspondent pas à ses dates et communes.")
    actualisation.to_parquet(fichier_parquet, index=False)
    return actualisation


def fusionner_historique_bigquery(client: bigquery.Client) -> None:
    """Ajoute la journée validée à l'historique."""
    fusionner_historique(
        client, TABLE_LANDING, TABLE_HISTORIQUE, COLONNES_BIGQUERY,
        "time", "code_insee",
    )
