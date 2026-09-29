# Schéma des données Fourcasters

Ce schéma présente les principales tables d'analyse construites par dbt dans BigQuery.

## Modèle principal

```mermaid
erDiagram
    DIM_COMMUNE ||--o{ FACT_METEO : "code_insee"
    DIM_DATE ||--o{ FACT_METEO : "date"

    DIM_DEPARTEMENT ||--o{ FACT_DANGER_INCENDIE : "numero_departement"
    DIM_DATE ||--o{ FACT_DANGER_INCENDIE : "date_prevision"

    FACT_DANGER_INCENDIE ||--|| PBI_RISQUE_INCENDIE : "id_danger_incendie"
    DIM_DEPARTEMENT ||--o{ PBI_RISQUE_INCENDIE : "numero_departement"

    DIM_COMMUNE {
        STRING code_insee PK
        STRING commune
        STRING numero_departement
        STRING departement
        STRING region
        FLOAT latitude
        FLOAT longitude
    }

    DIM_DEPARTEMENT {
        STRING numero_departement PK
        STRING departement
        STRING region
    }

    DIM_DATE {
        DATE date PK
        INT annee
        INT numero_mois
        STRING mois
        STRING saison
    }

    FACT_METEO {
        STRING id_observation_meteo PK
        DATE date FK
        STRING code_insee FK
        STRING numero_departement
        INT code_meteo
        FLOAT temperature_moyenne
        FLOAT humidite_moyenne
        FLOAT precipitations_totales
        FLOAT rafale_vent_maximale
    }

    FACT_DANGER_INCENDIE {
        STRING id_danger_incendie PK
        TIMESTAMP reference_time
        DATE date_publication
        DATE date_prevision FK
        STRING numero_departement FK
        STRING echeance
        INT niveau_danger
    }

    PBI_RISQUE_INCENDIE {
        STRING id_danger_incendie PK
        DATE date_publication
        DATE date_prevision
        STRING numero_departement FK
        STRING departement
        STRING region
        STRING echeance
        INT niveau_danger
        DATE date_meteo_utilisee
        INT retard_meteo_jours
        BOOL meteo_disponible
    }
```

## Lecture simple

- **dim_commune** décrit les 360 points météo du projet.
- **dim_departement** contient les 96 départements métropolitains.
- **dim_date** sert de calendrier commun.
- **fact_meteo** contient une observation météo par point et par jour.
- **fact_danger_incendie** contient une ligne par publication, département et échéance J1/J2.
- **pbi_risque_incendie** est une table plate préparée spécialement pour Power BI.

Une commune possède plusieurs observations météo dans le temps : relation **1,N** entre `dim_commune` et `fact_meteo`.

Un département possède plusieurs prévisions de danger : relation **1,N** entre `dim_departement` et `fact_danger_incendie`.

## Tables Machine Learning

Les tables ML sont séparées du modèle d'analyse principal :

```text
int_meteo_departement_jour
          |
          v
ml_features_incendie
          |
          +---- fact_danger_incendie
                    |
                    v
             ml_train_incendie
                    |
                    v
              pipeline.pkl
```

- `ml_features_incendie` prépare les variables météo des 7 derniers jours connus au moment de la publication, de D-6 à D.
- `ml_train_incendie` ajoute la cible Météo-France : J1 = D+1 et J2 = D+2.
- Ces tables servent à l'entraînement du modèle et ne remplacent pas les tables Power BI.
