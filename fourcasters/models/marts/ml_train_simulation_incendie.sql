WITH danger_unique AS (
    SELECT *
    FROM {{ ref('fact_danger_incendie') }}
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY date_publication, numero_departement, echeance
        ORDER BY reference_time DESC, insere_a DESC, id_danger_incendie DESC
    ) = 1
),

cibles_j1_j2 AS (
    SELECT
        date_publication AS date_meteo,
        numero_departement,
        CASE WHEN echeance = 'J1' THEN 1 ELSE 2 END AS horizon_jours,
        niveau_danger AS cible_niveau_danger
    FROM danger_unique
),

cibles_j0 AS (
    SELECT
        date_prevision AS date_meteo,
        numero_departement,
        0 AS horizon_jours,
        niveau_danger AS cible_niveau_danger
    FROM danger_unique
    WHERE echeance = 'J1'
),

cibles AS (
    SELECT * FROM cibles_j0
    UNION ALL
    SELECT * FROM cibles_j1_j2
)

SELECT
    CONCAT(
        CAST(meteo.date AS STRING),
        '|',
        meteo.code_insee,
        '|',
        CAST(cibles.horizon_jours AS STRING)
    ) AS id_simulation,

    meteo.date AS date_meteo,
    meteo.numero_departement,
    departement.departement,
    meteo.code_insee,
    commune.commune,
    commune.latitude,
    commune.longitude,

    cibles.horizon_jours,
    cibles.cible_niveau_danger,

    meteo.temperature_moyenne,
    meteo.temperature_maximale,
    meteo.humidite_moyenne,
    meteo.precipitations_totales AS precipitations,
    meteo.rafale_vent_maximale,
    meteo.deficit_pression_vapeur_maximal

FROM {{ ref('fact_meteo') }} AS meteo

INNER JOIN {{ ref('dim_commune') }} AS commune
    ON meteo.code_insee = commune.code_insee

INNER JOIN {{ ref('dim_departement') }} AS departement
    ON meteo.numero_departement = departement.numero_departement

INNER JOIN cibles
    ON meteo.date = cibles.date_meteo
    AND meteo.numero_departement = cibles.numero_departement

WHERE
    meteo.temperature_moyenne IS NOT NULL
    AND meteo.temperature_maximale IS NOT NULL
    AND meteo.humidite_moyenne IS NOT NULL
    AND meteo.precipitations_totales IS NOT NULL
    AND meteo.rafale_vent_maximale IS NOT NULL
    AND meteo.deficit_pression_vapeur_maximal IS NOT NULL
