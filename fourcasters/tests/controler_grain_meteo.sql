-- Une ligne par jour et par commune ; les jours totalement absents sont aussi signalés.
WITH calendrier AS (
    SELECT date
    FROM UNNEST(GENERATE_DATE_ARRAY(
        (SELECT MIN(date) FROM {{ ref('stg_meteo_journaliere') }}),
        (SELECT MAX(date) FROM {{ ref('stg_meteo_journaliere') }})
    )) AS date
),
volumes AS (
    SELECT date, COUNT(*) AS lignes, COUNT(DISTINCT code_insee) AS communes
    FROM {{ ref('stg_meteo_journaliere') }}
    GROUP BY date
)
SELECT calendrier.date
FROM calendrier LEFT JOIN volumes USING (date)
WHERE COALESCE(lignes, 0) != (SELECT COUNT(*) FROM {{ ref('referentiel_communes') }})
    OR COALESCE(communes, 0) != (SELECT COUNT(*) FROM {{ ref('referentiel_communes') }})
