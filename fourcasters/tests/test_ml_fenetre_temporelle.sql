SELECT *
FROM {{ ref('ml_train_incendie') }}
WHERE
    meteo_disponible
    AND (
        meteo_date != date_publication
        OR (
            echeance = 'J1'
            AND DATE_DIFF(date_prevision, meteo_date, DAY) != 1
        )
        OR (
            echeance = 'J2'
            AND DATE_DIFF(date_prevision, meteo_date, DAY) != 2
        )
    )
