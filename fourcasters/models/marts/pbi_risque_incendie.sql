/* Table prête pour Power BI : un danger prévu et la météo du jour de publication. */
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
    meteo.nombre_points_meteo IS NOT NULL AS meteo_disponible

FROM {{ ref('fact_danger_incendie') }} AS danger
LEFT JOIN {{ ref('int_meteo_departement_jour') }} AS meteo
    ON danger.date_publication = meteo.date
    AND danger.numero_departement = meteo.numero_departement
INNER JOIN {{ ref('dim_departement') }} AS departement
    ON danger.numero_departement = departement.numero_departement
