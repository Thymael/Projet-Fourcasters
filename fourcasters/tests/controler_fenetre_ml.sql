-- La fenêtre ML doit utiliser les 7 derniers jours connus au moment
-- de la publication : D-6 à D. meteo_date correspond donc au jour D.
SELECT id_feature
FROM {{ ref('ml_features_incendie') }}
WHERE
    meteo_date != date_publication
    OR (meteo_disponible AND nombre_jours_meteo_7j != 7)
