{{ config(materialized = 'table') }}

SELECT DISTINCT
    numero_departement,
    departement,
    region

FROM {{ ref('referentiel_communes') }}