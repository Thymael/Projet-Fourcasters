{% macro fusionner_actualisation() %}

    {# Fusionne la journée temporaire avec l'historique. #}
    {% set requete_fusion %}

        MERGE `fourcasters-openmeteo-loick.openmeteo_raw.meteo_journaliere` AS historique

        USING {{ source(
            'openmeteo_landing',
            'meteo_actualisation') }} AS actualisation

        ON historique.row_hash = actualisation.row_hash

        {# Seules les lignes absentes de l'historique sont ajoutées. #}
        WHEN NOT MATCHED THEN
            INSERT ROW

    {% endset %}

    {# Envoie la requête SQL à BigQuery. #}
    {% do run_query(requete_fusion) %}

    {{ log("✅ Fusion de l'actualisation terminée.", info=True) }}

{% endmacro %}