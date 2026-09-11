-- Chaque horodatage doit contenir exactement les 96 départements du référentiel.
SELECT reference_time
FROM {{ ref('stg_meteo_forets') }}
GROUP BY reference_time
HAVING COUNT(*) != 96 OR COUNT(DISTINCT numero_departement) != 96
