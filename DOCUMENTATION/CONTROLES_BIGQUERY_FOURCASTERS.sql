-- FOURCASTERS - CONTRÔLES BIGQUERY
-- Chaque bloc peut être enregistré comme une requête séparée.


-- CTRL 01 : état général Open-Meteo
-- Attendu : autant de lignes que de clés, aucun hash manquant.
SELECT
    COUNT(*) AS lignes,
    COUNT(DISTINCT row_hash) AS cles_uniques,
    COUNTIF(row_hash IS NULL) AS hash_manquants,
    COUNT(DISTINCT DATE(time)) AS jours,
    MIN(DATE(time)) AS premiere_date,
    MAX(DATE(time)) AS derniere_date
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`;


-- CTRL 02 : journées Open-Meteo incomplètes
-- Attendu : aucune ligne.
WITH calendrier AS (
    SELECT jour FROM UNNEST(GENERATE_DATE_ARRAY(
        (SELECT MIN(DATE(time)) FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`),
        (SELECT MAX(DATE(time)) FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`)
    )) AS jour
)
SELECT
    calendrier.jour AS date_observation,
    COUNT(meteo.code_insee) AS lignes,
    COUNT(DISTINCT meteo.row_hash) AS cles_uniques,
    COUNT(DISTINCT meteo.code_insee) AS communes
FROM calendrier
LEFT JOIN `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere` AS meteo
    ON calendrier.jour = DATE(meteo.time)
GROUP BY date_observation
HAVING lignes != 360 OR cles_uniques != 360 OR communes != 360
ORDER BY date_observation DESC;


-- CTRL 03 : fraîcheur Open-Meteo
-- ERA5-Seamless arrive volontairement avec environ six jours de retard.
SELECT
    MAX(DATE(time)) AS derniere_date,
    DATE_DIFF(
        CURRENT_DATE('Europe/Paris'),
        MAX(DATE(time)),
        DAY
    ) AS retard_en_jours
FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`;


-- CTRL 04 : état général Météo-France
-- Attendu : autant de lignes que de clés et 96 départements.
SELECT
    COUNT(*) AS lignes,
    COUNT(DISTINCT row_hash) AS cles_uniques,
    COUNTIF(row_hash IS NULL) AS hash_manquants,
    COUNT(DISTINCT reference_time) AS publications,
    COUNT(DISTINCT dep_code) AS departements,
    MIN(DATE(reference_time)) AS premiere_date,
    MAX(DATE(reference_time)) AS derniere_date
FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`;


-- CTRL 05 : publications Météo-France incomplètes
-- Attendu : aucune ligne.
SELECT
    reference_time,
    COUNT(*) AS lignes,
    COUNT(DISTINCT row_hash) AS cles_uniques,
    COUNT(DISTINCT dep_code) AS departements
FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`
GROUP BY reference_time
HAVING lignes != 96 OR cles_uniques != 96 OR departements != 96
ORDER BY reference_time DESC;


-- CTRL 06 : volumes du modèle en étoile
-- Chaque ligne Météo-France produit un fait J1 et un fait J2.
SELECT
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_commune`)
        AS communes,
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_departement`)
        AS departements,
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.dim_date`)
        AS dates,
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS faits_meteo,
    (SELECT COUNT(DISTINCT id_observation_meteo)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS ids_meteo_uniques,
    (SELECT COUNT(*)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS faits_incendie,
    (SELECT COUNT(DISTINCT id_danger_incendie)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS ids_incendie_uniques;


-- CTRL 07 : synchronisation des tables RAW et dbt
-- Attendu : les deux colonnes booléennes valent TRUE.
SELECT
    (SELECT MAX(DATE(time))
     FROM `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere`)
    =
    (SELECT MAX(date)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_meteo`)
        AS openmeteo_synchronise,
    (SELECT MAX(reference_time)
     FROM `fourcasters-openmeteo-loick.meteofrance_raw.meteo_forets`)
    =
    (SELECT MAX(reference_time)
     FROM `fourcasters-openmeteo-loick.openmeteo_analyse.fact_danger_incendie`)
        AS meteofrance_synchronise;


-- CTRL 08 : météo réellement associée aux bulletins dans la table Power BI
-- Ce contrôle porte sur la dernière météo présente au plus tard à la publication.
SELECT
    COUNT(*) AS lignes_incendie,
    COUNTIF(meteo_disponible) AS lignes_avec_meteo,
    COUNTIF(NOT meteo_disponible) AS lignes_sans_meteo,
    MAX(retard_meteo_jours) AS retard_maximum,
    ROUND(
        100 * SAFE_DIVIDE(COUNTIF(meteo_disponible), COUNT(*)),
        2
    ) AS taux_jointure
FROM `fourcasters-openmeteo-loick.openmeteo_analyse.pbi_risque_incendie`;


-- CTRL 09 : séparation entre variables ML complètes et incomplètes
SELECT
    COUNT(*) AS lignes,
    COUNT(DISTINCT id_apprentissage) AS cles_uniques,
    COUNTIF(meteo_disponible) AS lignes_exploitables,
    COUNTIF(NOT meteo_disponible) AS lignes_sans_fenetre_complete
FROM `fourcasters-openmeteo-loick.openmeteo_analyse.ml_train_incendie`;
