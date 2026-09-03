{{ config(materialized = 'table') }}

SELECT
    row_hash AS id_danger_incendie,
    reference_time,
    date_publication,
    numero_departement,
    niveau_j1,
    niveau_j2,
    insere_a

FROM {{ ref('stg_meteo_forets') }}