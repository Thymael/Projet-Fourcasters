{{ config(materialized = 'table') }}

-- Prévisions de danger incendie ramenées à une ligne par date et département

SELECT
    CONCAT(row_hash, '-J1') AS id_danger_incendie,
    reference_time,
    date_publication,
    date_j1 AS date_prevision,
    numero_departement,
    'J1' AS echeance,
    niveau_j1 AS niveau_danger,
    insere_a

FROM {{ ref('stg_meteo_forets') }}

UNION ALL

SELECT
    CONCAT(row_hash, '-J2') AS id_danger_incendie,
    reference_time,
    date_publication,
    date_j2 AS date_prevision,
    numero_departement,
    'J2' AS echeance,
    niveau_j2 AS niveau_danger,
    insere_a

FROM {{ ref('stg_meteo_forets') }}