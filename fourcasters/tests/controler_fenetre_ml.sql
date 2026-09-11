-- Une météo annoncée complète doit contenir sept jours et précéder la publication.
SELECT id_feature
FROM {{ ref('ml_features_incendie') }}
WHERE meteo_date != DATE_SUB(date_publication, INTERVAL 7 DAY)
    OR (meteo_disponible AND nombre_jours_meteo_7j != 7)
