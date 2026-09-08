/* Une ligne météo par département et par jour.
   Cette table évite de refaire la même agrégation dans Power BI et dans le ML. */
SELECT
    date,
    numero_departement,
    ANY_VALUE(departement) AS departement,
    ANY_VALUE(region) AS region,
    COUNT(DISTINCT code_insee) AS nombre_points_meteo,

    AVG(temperature_moyenne) AS temperature_moyenne,
    MIN(temperature_minimale) AS temperature_minimale,
    MAX(temperature_maximale) AS temperature_maximale,
    AVG(humidite_moyenne) AS humidite_moyenne,
    SUM(precipitations_totales) AS precipitations_totales,
    AVG(vitesse_vent_moyenne) AS vitesse_vent_moyenne,
    MAX(rafale_vent_maximale) AS rafale_vent_maximale,
    AVG(couverture_nuageuse_moyenne) AS couverture_nuageuse_moyenne,
    MAX(deficit_pression_vapeur_maximal) AS deficit_pression_vapeur_maximal

FROM {{ ref('int_meteo_communes') }}
GROUP BY date, numero_departement
