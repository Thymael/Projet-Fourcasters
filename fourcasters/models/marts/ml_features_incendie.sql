/* Variables météo disponibles avant une publication.
   Le niveau de danger n'est volontairement pas repris : ce n'est pas une cible observée. */
WITH meteo_avec_rolling AS (
    SELECT
        date,
        numero_departement,
        departement,
        region,
        nombre_points_meteo,
        temperature_moyenne,
        temperature_maximale,
        humidite_moyenne,
        precipitations_totales,
        rafale_vent_maximale,
        deficit_pression_vapeur_maximal,

        AVG(temperature_moyenne) OVER fenetre_7j AS temperature_moyenne_7j,
        MAX(temperature_maximale) OVER fenetre_7j AS temperature_maximale_7j,
        AVG(humidite_moyenne) OVER fenetre_7j AS humidite_moyenne_7j,
        SUM(precipitations_totales) OVER fenetre_7j AS precipitations_7j,
        MAX(rafale_vent_maximale) OVER fenetre_7j AS rafale_vent_maximale_7j,
        MAX(deficit_pression_vapeur_maximal) OVER fenetre_7j
            AS deficit_pression_vapeur_maximal_7j,
        COUNTIF(precipitations_totales = 0) OVER fenetre_7j
            AS jours_sans_pluie_7j

    FROM {{ ref('int_meteo_departement_jour') }}
    WINDOW fenetre_7j AS (
        PARTITION BY numero_departement
        ORDER BY UNIX_DATE(date)
        RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
    )
),

dates_publication AS (
    SELECT DISTINCT
        date_publication,
        numero_departement
    FROM {{ ref('fact_danger_incendie') }}
)

SELECT
    CONCAT(
        CAST(publication.date_publication AS STRING),
        '|',
        publication.numero_departement
    ) AS id_feature,
    publication.date_publication,
    DATE_SUB(publication.date_publication, INTERVAL 1 DAY) AS meteo_date,
    publication.numero_departement,
    meteo.departement,
    meteo.region,
    meteo.nombre_points_meteo,
    meteo.temperature_moyenne,
    meteo.temperature_maximale,
    meteo.humidite_moyenne,
    meteo.precipitations_totales,
    meteo.rafale_vent_maximale,
    meteo.deficit_pression_vapeur_maximal,
    meteo.temperature_moyenne_7j,
    meteo.temperature_maximale_7j,
    meteo.humidite_moyenne_7j,
    meteo.precipitations_7j,
    meteo.rafale_vent_maximale_7j,
    meteo.deficit_pression_vapeur_maximal_7j,
    meteo.jours_sans_pluie_7j,
    meteo.date IS NOT NULL AS meteo_disponible

FROM dates_publication AS publication
LEFT JOIN meteo_avec_rolling AS meteo
    ON DATE_SUB(publication.date_publication, INTERVAL 1 DAY) = meteo.date
    AND publication.numero_departement = meteo.numero_departement
