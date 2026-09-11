WITH danger_unique AS (

    SELECT *
    FROM {{ ref('fact_danger_incendie') }}

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY
            date_publication,
            numero_departement,
            echeance
        ORDER BY reference_time DESC, insere_a DESC, id_danger_incendie DESC
    ) = 1

)

SELECT
    CONCAT(
        CAST(danger.date_publication AS STRING),
        '|',
        danger.numero_departement,
        '|',
        danger.echeance
    ) AS id_apprentissage,

    danger.reference_time,
    danger.date_publication,
    danger.date_prevision,
    danger.numero_departement,

    departement.departement,
    departement.region,

    danger.echeance,

    CASE
        WHEN danger.echeance = 'J1' THEN 1
        ELSE 2
    END AS horizon_jours,

    danger.niveau_danger AS cible_niveau_danger,

    features.meteo_date,
    features.nombre_points_meteo,
    features.temperature_moyenne,
    features.temperature_maximale,
    features.humidite_moyenne,
    features.precipitations_totales,
    features.precipitations_moyennes,
    features.rafale_vent_maximale,
    features.deficit_pression_vapeur_maximal,

    features.temperature_moyenne_7j,
    features.temperature_maximale_7j,
    features.humidite_moyenne_7j,
    features.precipitations_7j,
    features.precipitations_moyennes_7j,
    features.rafale_vent_maximale_7j,
    features.deficit_pression_vapeur_maximal_7j,
    features.jours_sans_pluie_7j,

    features.meteo_disponible

FROM danger_unique AS danger

INNER JOIN {{ ref('ml_features_incendie') }} AS features
    ON danger.date_publication = features.date_publication
    AND danger.numero_departement = features.numero_departement

INNER JOIN {{ ref('dim_departement') }} AS departement
    ON danger.numero_departement = departement.numero_departement
