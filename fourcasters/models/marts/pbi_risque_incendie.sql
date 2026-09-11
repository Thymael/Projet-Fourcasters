-- Chaque journée météo reste la dernière connue jusqu'à la suivante.
-- Cette jointure conserve une seule ligne météo par prévision, même avec des trous.
WITH meteo_par_periode AS (
    SELECT *,
        LEAD(date, 1, DATE '9999-12-31') OVER (
            PARTITION BY numero_departement ORDER BY date
        ) AS date_suivante
    FROM {{ ref('int_meteo_departement_jour') }}
)

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

LEFT JOIN meteo_par_periode AS meteo
    ON danger.numero_departement = meteo.numero_departement
    AND meteo.date <= danger.date_publication
    AND danger.date_publication < meteo.date_suivante
