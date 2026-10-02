-- Contrat temporel du ML :
-- J = date de référence disposant de la météo.
-- météo J-6 à J -> horizons J+1 et J+2.

WITH anomalies_features AS (
    SELECT id_feature AS identifiant
    FROM {{ ref('ml_features_incendie') }}
    WHERE
        meteo_date != date_publication
        OR (meteo_disponible AND nombre_jours_meteo_7j != 7)
),

anomalies_cibles AS (
    SELECT id_apprentissage AS identifiant
    FROM {{ ref('ml_train_incendie') }}
    WHERE
        (echeance = 'J1' AND DATE_DIFF(date_prevision, date_publication, DAY) != 1)
        OR
        (echeance = 'J2' AND DATE_DIFF(date_prevision, date_publication, DAY) != 2)
)

SELECT * FROM anomalies_features
UNION ALL
SELECT * FROM anomalies_cibles
