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


-- ============================================================
-- CTRL_08_METEOFRANCE_RAW_GLOBAL
-- Controle l'ensemble de l'historique Meteo-France.
-- Attendu : nombre_lignes = nombre_cles_uniques et 0 hash manquant.
-- ============================================================

SELECT
    COUNT(*) AS nombre_lignes,
    COUNT(DISTINCT row_hash) AS nombre_cles_uniques,
    COUNTIF(row_hash IS NULL) AS row_hash_manquants,
    COUNT(DISTINCT reference_time) AS nombre_publications,
    COUNT(DISTINCT dep_code) AS nombre_departements,
    MIN(reference_time) AS premiere_publication,
    MAX(reference_time) AS derniere_publication
FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`;


-- ============================================================
-- CTRL_09_METEOFRANCE_PUBLICATIONS_INCOMPLETES
-- Recherche les publications qui ne contiennent pas 96 departements.
-- Attendu : aucune ligne.
-- ============================================================

SELECT
    reference_time,
    COUNT(*) AS nombre_lignes,
    COUNT(DISTINCT row_hash) AS nombre_cles_uniques,
    COUNT(DISTINCT dep_code) AS nombre_departements
FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`
GROUP BY reference_time
HAVING
    nombre_lignes != 96
    OR nombre_cles_uniques != 96
    OR nombre_departements != 96
ORDER BY reference_time DESC;


-- ============================================================
-- CTRL_10_METEOFRANCE_DOUBLONS
-- Recherche les row_hash presents plusieurs fois.
-- Attendu : aucune ligne.
-- ============================================================

SELECT
    row_hash,
    COUNT(*) AS nombre_occurrences,
    MIN(reference_time) AS reference_time,
    ANY_VALUE(dep_code) AS numero_departement
FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`
GROUP BY row_hash
HAVING COUNT(*) > 1
ORDER BY nombre_occurrences DESC
LIMIT 100;


-- ============================================================
-- CTRL_11_METEOFRANCE_MODELE_DBT
-- Controle les volumes du modele analytique danger incendie.
-- Chaque ligne RAW produit une ligne J1 et une ligne J2.
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`)
        AS nombre_lignes_raw,

    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_departement`)
        AS nombre_departements,

    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS nombre_faits,

    (SELECT COUNT(DISTINCT id_danger_incendie)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS ids_uniques,

    (SELECT COUNTIF(echeance = 'J1')
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS nombre_j1,

    (SELECT COUNTIF(echeance = 'J2')
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS nombre_j2;


-- ============================================================
-- CTRL_12_METEOFRANCE_RAW_ET_DBT_SYNCHRONISES
-- Compare la derniere publication RAW avec le modele dbt.
-- Attendu : les deux dates sont identiques.
-- ============================================================

SELECT
    (SELECT MAX(reference_time)
     FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`)
        AS derniere_publication_raw,

    (SELECT MAX(reference_time)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS derniere_publication_fact,

    (SELECT MAX(reference_time)
     FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`)
    =
    (SELECT MAX(reference_time)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS raw_et_fact_synchronises;


-- ============================================================
-- CTRL_13_FRAICHEUR_METEOFRANCE
-- Mesure l'anciennete de la derniere publication Meteo-France.
-- ============================================================

SELECT
    MAX(DATE(reference_time)) AS derniere_publication,
    DATE_DIFF(
        CURRENT_DATE('Europe/Paris'),
        MAX(DATE(reference_time)),
        DAY
    ) AS retard_en_jours
FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`;


-- ============================================================
-- CTRL_14_COUVERTURE_INCENDIE_DERNIERE_DATE_OPENMETEO
-- Verifie la couverture incendie pour la derniere date Open-Meteo.
-- Attendu : 96 departements en J1 et 96 departements en J2.
-- ============================================================

WITH derniere_date_openmeteo AS (
    SELECT MAX(DATE(time)) AS date_observation
    FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`
)

SELECT
    incendie.date_prevision,
    incendie.echeance,
    COUNT(*) AS nombre_lignes,
    COUNT(DISTINCT incendie.numero_departement) AS nombre_departements
FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie` AS incendie
CROSS JOIN derniere_date_openmeteo
WHERE incendie.date_prevision = derniere_date_openmeteo.date_observation
GROUP BY
    incendie.date_prevision,
    incendie.echeance
ORDER BY incendie.echeance;