SELECT
    danger.id_danger_incendie,
    danger.reference_time,
    danger.date_publication,
    danger.date_prevision,
    danger.echeance,

    danger.numero_departement,
    departement.departement,
    departement.region,

    danger.niveau_danger,

    meteo.date AS date_meteo_utilisee,

    DATE_DIFF(
        danger.date_publication,
        meteo.date,
        DAY
    ) AS retard_meteo_jours,

    meteo.nombre_points_meteo,
    meteo.temperature_moyenne,
    meteo.temperature_minimale,
    meteo.temperature_maximale,
    meteo.humidite_moyenne,
    meteo.precipitations_totales,
    meteo.vitesse_vent_moyenne,
    meteo.rafale_vent_maximale,
    meteo.couverture_nuageuse_moyenne,
    meteo.deficit_pression_vapeur_maximal,

    meteo.date IS NOT NULL AS meteo_disponible

FROM {{ ref('fact_danger_incendie') }} AS danger

INNER JOIN {{ ref('dim_departement') }} AS departement
    ON danger.numero_departement = departement.numero_departement

LEFT JOIN {{ ref('int_meteo_departement_jour') }} AS meteo
    ON danger.numero_departement = meteo.numero_departement
    AND meteo.date <= danger.date_publication

QUALIFY
    ROW_NUMBER() OVER (
        PARTITION BY danger.id_danger_incendie
        ORDER BY meteo.date DESC
    ) = 1