SELECT
    row_hash,
    insere_a,
    reference_time,
    DATE(reference_time) AS date_publication,
    DATE_ADD(DATE(reference_time), INTERVAL 1 DAY) AS date_j1,
    DATE_ADD(DATE(reference_time), INTERVAL 2 DAY) AS date_j2,
    TRIM(dep_code) AS numero_departement,
    TRIM(nom_dep) AS departement,
    niveau_j1,
    niveau_j2

FROM {{ source('meteofrance_raw', 'meteo_forets') }}

-- L'API et l'archive 2026 se recouvrent. Les anciens scripts n'utilisaient
-- pas toujours le même format de date dans le hash, malgré un bulletin identique.
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY reference_time, TRIM(dep_code)
    ORDER BY insere_a DESC, row_hash DESC
) = 1
