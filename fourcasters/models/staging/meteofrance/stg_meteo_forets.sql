{{ config(materialized = 'view') }}

-- Préparation des données Météo des forêts
SELECT
    row_hash,
    insere_a,

    reference_time,
    DATE(reference_time) AS date_publication,

    TRIM(dep_code) AS numero_departement,
    TRIM(nom_dep) AS departement,

    niveau_j1,
    niveau_j2

FROM {{ source('meteofrance_raw', 'meteo_forets') }}