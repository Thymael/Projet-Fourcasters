SELECT
    row_hash,
    insere_a,
    TRIM(code_insee) AS code_insee,
    DATE(time) AS date,

    SAFE_CAST(weather_code AS INT64) AS code_meteo,

    SAFE_CAST(temperature_2m_mean AS FLOAT64) AS temperature_moyenne,
    SAFE_CAST(temperature_2m_min AS FLOAT64) AS temperature_minimale,
    SAFE_CAST(temperature_2m_max AS FLOAT64) AS temperature_maximale,

    SAFE_CAST(apparent_temperature_mean AS FLOAT64) AS temperature_ressentie_moyenne,
    SAFE_CAST(apparent_temperature_min AS FLOAT64) AS temperature_ressentie_minimale,
    SAFE_CAST(apparent_temperature_max AS FLOAT64) AS temperature_ressentie_maximale,

    SAFE_CAST(relative_humidity_2m_mean AS FLOAT64) AS humidite_moyenne,
    SAFE_CAST(relative_humidity_2m_min AS FLOAT64) AS humidite_minimale,
    SAFE_CAST(relative_humidity_2m_max AS FLOAT64) AS humidite_maximale,

    SAFE_CAST(dew_point_2m_mean AS FLOAT64) AS point_de_rosee_moyen,

    SAFE_CAST(precipitation_sum AS FLOAT64) AS precipitations_totales,
    SAFE_CAST(rain_sum AS FLOAT64) AS pluie_totale,
    SAFE_CAST(snowfall_sum AS FLOAT64) AS neige_totale,
    SAFE_CAST(precipitation_hours AS FLOAT64) AS heures_de_precipitations,

    SAFE_CAST(wind_speed_10m_mean AS FLOAT64) AS vitesse_vent_moyenne,
    SAFE_CAST(wind_speed_10m_max AS FLOAT64) AS vitesse_vent_maximale,
    SAFE_CAST(wind_gusts_10m_max AS FLOAT64) AS rafale_vent_maximale,
    SAFE_CAST(wind_direction_10m_dominant AS FLOAT64) AS direction_vent_dominante,

    SAFE_CAST(cloud_cover_mean AS FLOAT64) AS couverture_nuageuse_moyenne,
    SAFE_CAST(pressure_msl_mean AS FLOAT64) AS pression_moyenne,
    SAFE_CAST(sunshine_duration AS FLOAT64) AS duree_ensoleillement,
    SAFE_CAST(shortwave_radiation_sum AS FLOAT64) AS rayonnement_solaire_total,

    SAFE_CAST(et0_fao_evapotranspiration AS FLOAT64) AS evapotranspiration,
    SAFE_CAST(vapour_pressure_deficit_max AS FLOAT64) AS deficit_pression_vapeur_maximal,

    SAFE_CAST(soil_moisture_0_to_7cm_mean AS FLOAT64) AS humidite_sol_0_7cm,
    SAFE_CAST(soil_moisture_7_to_28cm_mean AS FLOAT64) AS humidite_sol_7_28cm,
    SAFE_CAST(soil_moisture_28_to_100cm_mean AS FLOAT64) AS humidite_sol_28_100cm,

    SAFE_CAST(soil_temperature_0_to_7cm_mean AS FLOAT64) AS temperature_sol_0_7cm

FROM {{ source('openmeteo_raw', 'meteo_journaliere') }}