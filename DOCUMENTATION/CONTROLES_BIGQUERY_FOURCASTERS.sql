-- ============================================================
-- FOURCASTERS - REQUETES PRINCIPALES DE CONTROLE BIGQUERY
-- ============================================================
-- Chaque bloc peut etre enregistre comme une requete distincte
-- dans BigQuery avec le nom CTRL_01, CTRL_02, etc.


-- ============================================================
-- CTRL_01_OPENMETEO_RAW_GLOBAL
-- Controle l'ensemble de l'historique Open-Meteo.
-- Attendu : nombre_lignes = nombre_cles_uniques et 0 hash manquant.
-- ============================================================

SELECT
    COUNT(*) AS nombre_lignes,
    COUNT(DISTINCT row_hash) AS nombre_cles_uniques,
    COUNTIF(row_hash IS NULL) AS row_hash_manquants,
    COUNT(DISTINCT DATE(time)) AS nombre_jours,
    MIN(DATE(time)) AS premiere_date,
    MAX(DATE(time)) AS derniere_date
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`;


-- ============================================================
-- CTRL_02_OPENMETEO_JOURNEES_INCOMPLETES
-- Recherche les dates qui ne contiennent pas exactement 360 communes.
-- Attendu : aucune ligne.
-- ============================================================

SELECT
    DATE(time) AS date_observation,
    COUNT(*) AS nombre_lignes,
    COUNT(DISTINCT row_hash) AS nombre_cles_uniques,
    COUNT(DISTINCT code_insee) AS nombre_communes
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`
GROUP BY date_observation
HAVING
    nombre_lignes != 360
    OR nombre_cles_uniques != 360
    OR nombre_communes != 360
ORDER BY date_observation DESC;


-- ============================================================
-- CTRL_03_OPENMETEO_DOUBLONS
-- Recherche les row_hash presents plusieurs fois dans l'historique.
-- Attendu : aucune ligne.
-- ============================================================

SELECT
    row_hash,
    COUNT(*) AS nombre_occurrences,
    MIN(DATE(time)) AS date_observation,
    ANY_VALUE(code_insee) AS code_insee
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`
GROUP BY row_hash
HAVING COUNT(*) > 1
ORDER BY nombre_occurrences DESC
LIMIT 100;


-- ============================================================
-- CTRL_04_DERNIERE_JOURNEE
-- Controle la derniere journee disponible dans BigQuery.
-- Attendu : 360 lignes, 360 cles uniques et 0 hash manquant.
-- ============================================================

WITH derniere_date AS (
    SELECT MAX(DATE(time)) AS date_observation
    FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`
)

SELECT
    DATE(meteo.time) AS date_observation,
    COUNT(*) AS nombre_lignes,
    COUNT(DISTINCT meteo.row_hash) AS nombre_cles_uniques,
    COUNTIF(meteo.row_hash IS NULL) AS hash_manquants
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere` AS meteo
CROSS JOIN derniere_date
WHERE DATE(meteo.time) = derniere_date.date_observation
GROUP BY date_observation;


-- ============================================================
-- CTRL_05_MODELE_DBT_VOLUMES
-- Controle les volumes et les cles du modele analytique.
-- Attendu : 360 communes et autant de faits que de cles uniques.
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_commune`)
        AS nombre_communes,

    (SELECT COUNT(DISTINCT code_insee)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_commune`)
        AS codes_insee_uniques,

    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_date`)
        AS nombre_dates,

    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS nombre_faits,

    (SELECT COUNT(DISTINCT CONCAT(CAST(date AS STRING), '|', code_insee))
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS cles_date_commune_uniques,

    (SELECT MIN(date)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS premiere_date,

    (SELECT MAX(date)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS derniere_date;


-- ============================================================
-- CTRL_06_RAW_ET_DBT_SYNCHRONISES
-- Compare la derniere date RAW avec la derniere date du modele dbt.
-- Attendu : les deux dates sont identiques.
-- ============================================================

SELECT
    (SELECT MAX(DATE(time))
     FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`)
        AS derniere_date_raw,

    (SELECT MAX(date)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS derniere_date_fact,

    (SELECT MAX(DATE(time))
     FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`)
    =
    (SELECT MAX(date)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS raw_et_fact_synchronises;


-- ============================================================
-- CTRL_07_FRAICHEUR_OPENMETEO
-- Mesure le retard de la derniere journee Open-Meteo.
-- ERA5-Seamless est volontairement recupere avec environ 6 jours de retard.
-- ============================================================

SELECT
    MAX(DATE(time)) AS derniere_date,
    DATE_DIFF(
        CURRENT_DATE('Europe/Paris'),
        MAX(DATE(time)),
        DAY
    ) AS retard_en_jours
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`;
