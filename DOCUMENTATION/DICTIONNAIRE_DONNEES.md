# Dictionnaire de données Fourcasters

Ce dictionnaire décrit les principales tables finales du projet. Les exemples sont indicatifs et servent seulement à comprendre le format des données.

## dim_commune

Grain : **une ligne par point météo du référentiel**.

| Colonne | Type | Description | Exemple / contrainte |
| --- | --- | --- | --- |
| code_insee | STRING | Identifiant INSEE du point météo. | `59350` — unique, non nul |
| commune | STRING | Nom de la commune ou du point. | Lille |
| numero_departement | STRING | Code du département. | `59` |
| departement | STRING | Nom du département. | Nord |
| region | STRING | Région administrative. | Hauts-de-France |
| latitude | FLOAT64 | Latitude du point. | 50.63 |
| longitude | FLOAT64 | Longitude du point. | 3.06 |
| service | STRING | Information de service présente dans le référentiel. | selon référentiel |
| centroide | BOOL | Indique si le point correspond à un centroïde. | true / false |

## dim_departement

Grain : **une ligne par département métropolitain**.

| Colonne | Type | Description | Exemple / contrainte |
| --- | --- | --- | --- |
| numero_departement | STRING | Code du département. | `59` — unique, non nul |
| departement | STRING | Nom du département. | Nord |
| region | STRING | Région administrative. | Hauts-de-France |

## dim_date

Grain : **une ligne par date**.

| Colonne | Type | Description | Exemple |
| --- | --- | --- | --- |
| date | DATE | Date du calendrier. | 2026-07-15 |
| annee | INT64 | Année. | 2026 |
| trimestre | INT64 | Trimestre de 1 à 4. | 3 |
| numero_mois | INT64 | Numéro du mois. | 7 |
| mois | STRING | Nom du mois. | Juillet |
| numero_semaine | INT64 | Numéro de semaine. | 28 |
| jour_du_mois | INT64 | Numéro du jour dans le mois. | 15 |
| numero_jour_semaine | INT64 | Numéro BigQuery du jour de semaine. | 4 |
| jour_semaine | STRING | Nom du jour. | Mercredi |
| saison | STRING | Saison selon le mois. | Été |
| est_weekend | BOOL | Indique si la date tombe un samedi ou dimanche. | false |

## fact_meteo

Grain : **une ligne par date et par point météo**.

| Colonne | Type | Description |
| --- | --- | --- |
| id_observation_meteo | STRING | Identifiant unique de l'observation météo. |
| date | DATE | Date de l'observation. |
| code_insee | STRING | Point météo concerné. |
| numero_departement | STRING | Département du point météo. |
| code_meteo | INT64 | Code météo WMO renvoyé par Open-Meteo. |
| temperature_moyenne | FLOAT64 | Température moyenne journalière. |
| temperature_minimale | FLOAT64 | Température minimale journalière. |
| temperature_maximale | FLOAT64 | Température maximale journalière. |
| temperature_ressentie_moyenne | FLOAT64 | Température ressentie moyenne. |
| temperature_ressentie_minimale | FLOAT64 | Température ressentie minimale. |
| temperature_ressentie_maximale | FLOAT64 | Température ressentie maximale. |
| humidite_moyenne | FLOAT64 | Humidité relative moyenne. |
| humidite_minimale | FLOAT64 | Humidité relative minimale. |
| humidite_maximale | FLOAT64 | Humidité relative maximale. |
| point_de_rosee_moyen | FLOAT64 | Point de rosée moyen. |
| precipitations_totales | FLOAT64 | Total journalier des précipitations. |
| pluie_totale | FLOAT64 | Total journalier de pluie. |
| neige_totale | FLOAT64 | Total journalier de neige. |
| heures_de_precipitations | FLOAT64 | Nombre d'heures avec précipitations. |
| vitesse_vent_moyenne | FLOAT64 | Vitesse moyenne du vent. |
| vitesse_vent_maximale | FLOAT64 | Vitesse maximale du vent. |
| rafale_vent_maximale | FLOAT64 | Rafale maximale. |
| direction_vent_dominante | FLOAT64 | Direction dominante du vent. |
| couverture_nuageuse_moyenne | FLOAT64 | Couverture nuageuse moyenne. |
| pression_moyenne | FLOAT64 | Pression moyenne au niveau de la mer. |
| duree_ensoleillement | FLOAT64 | Durée d'ensoleillement journalière. |
| rayonnement_solaire_total | FLOAT64 | Rayonnement solaire journalier. |
| evapotranspiration | FLOAT64 | Évapotranspiration de référence. |
| deficit_pression_vapeur_maximal | FLOAT64 | Déficit de pression de vapeur maximal (VPD). |
| humidite_sol_0_7cm | FLOAT64 | Humidité moyenne du sol entre 0 et 7 cm. |
| humidite_sol_7_28cm | FLOAT64 | Humidité moyenne du sol entre 7 et 28 cm. |
| humidite_sol_28_100cm | FLOAT64 | Humidité moyenne du sol entre 28 et 100 cm. |
| temperature_sol_0_7cm | FLOAT64 | Température moyenne du sol entre 0 et 7 cm. |

## fact_danger_incendie

Grain : **une ligne par publication Météo-France, département et échéance**.

| Colonne | Type | Description | Exemple / contrainte |
| --- | --- | --- | --- |
| id_danger_incendie | STRING | Identifiant unique de la prévision. | unique, non nul |
| reference_time | TIMESTAMP | Horodatage du bulletin Météo-France. | 2026-07-15 16:00 UTC |
| date_publication | DATE | Date du bulletin. | 2026-07-15 |
| date_prevision | DATE | Date concernée par la prévision. | 2026-07-16 |
| numero_departement | STRING | Département concerné. | `59` |
| echeance | STRING | Horizon de la prévision. | J1 ou J2 |
| niveau_danger | INT64 | Niveau de danger Météo-France. | 1 à 4 |
| insere_a | TIMESTAMP | Date d'insertion dans le pipeline. | horodatage technique |

## int_meteo_departement_jour

Grain : **une ligne par département et par jour**.

| Colonne | Type | Description |
| --- | --- | --- |
| date | DATE | Date de la météo. |
| numero_departement | STRING | Département. |
| departement | STRING | Nom du département. |
| region | STRING | Région. |
| nombre_points_meteo | INT64 | Nombre de points météo utilisés dans l'agrégation. |
| mesures_completes | BOOL | Vrai si les variables nécessaires sont disponibles sur tous les points. |
| temperature_moyenne | FLOAT64 | Moyenne des températures moyennes des points du département. |
| temperature_minimale | FLOAT64 | Température minimale parmi les points. |
| temperature_maximale | FLOAT64 | Température maximale parmi les points. |
| humidite_moyenne | FLOAT64 | Humidité moyenne des points. |
| precipitations_totales | FLOAT64 | Somme des précipitations des points. |
| precipitations_moyennes | FLOAT64 | Moyenne des précipitations des points. |
| vitesse_vent_moyenne | FLOAT64 | Vitesse moyenne du vent. |
| rafale_vent_maximale | FLOAT64 | Rafale maximale observée dans le département. |
| couverture_nuageuse_moyenne | FLOAT64 | Couverture nuageuse moyenne. |
| deficit_pression_vapeur_maximal | FLOAT64 | VPD maximal observé dans le département. |

## pbi_risque_incendie

Grain : **une ligne par prévision Météo-France utilisée dans Power BI**.

| Colonne | Type | Description |
| --- | --- | --- |
| id_danger_incendie | STRING | Identifiant unique de la prévision. |
| reference_time | TIMESTAMP | Horodatage du bulletin. |
| date_publication | DATE | Date de publication. |
| date_prevision | DATE | Date prévue. |
| echeance | STRING | J1 ou J2. |
| numero_departement | STRING | Code du département. |
| departement | STRING | Nom du département. |
| region | STRING | Région. |
| niveau_danger | INT64 | Niveau Météo-France de 1 à 4. |
| date_meteo_utilisee | DATE | Dernière date météo disponible associée au bulletin. |
| retard_meteo_jours | INT64 | Nombre de jours entre le bulletin et la météo utilisée. |
| nombre_points_meteo | INT64 | Nombre de points météo utilisés pour le département. |
| temperature_moyenne | FLOAT64 | Température moyenne départementale. |
| temperature_minimale | FLOAT64 | Température minimale départementale. |
| temperature_maximale | FLOAT64 | Température maximale départementale. |
| humidite_moyenne | FLOAT64 | Humidité moyenne départementale. |
| precipitations_totales | FLOAT64 | Précipitations agrégées du département. |
| vitesse_vent_moyenne | FLOAT64 | Vitesse moyenne du vent. |
| rafale_vent_maximale | FLOAT64 | Rafale maximale. |
| couverture_nuageuse_moyenne | FLOAT64 | Couverture nuageuse moyenne. |
| deficit_pression_vapeur_maximal | FLOAT64 | VPD maximal. |
| meteo_disponible | BOOL | Indique si une météo a pu être associée à la prévision. |

## ml_features_incendie

Grain : **une ligne par date de publication et département**.

| Colonne | Type | Description |
| --- | --- | --- |
| id_feature | STRING | Identifiant unique de la ligne de features. |
| date_publication | DATE | Date du bulletin Météo-France. |
| meteo_date | DATE | Date météo de référence utilisée pour le ML, publication - 7 jours. |
| numero_departement | STRING | Département. |
| departement | STRING | Nom du département. |
| region | STRING | Région. |
| nombre_points_meteo | INT64 | Nombre de points météo utilisés. |
| temperature_moyenne | FLOAT64 | Température moyenne du jour météo retenu. |
| temperature_maximale | FLOAT64 | Température maximale du jour météo retenu. |
| humidite_moyenne | FLOAT64 | Humidité moyenne du jour météo retenu. |
| precipitations_totales | FLOAT64 | Précipitations agrégées du jour. |
| precipitations_moyennes | FLOAT64 | Précipitations moyennes des points. |
| rafale_vent_maximale | FLOAT64 | Rafale maximale. |
| deficit_pression_vapeur_maximal | FLOAT64 | VPD maximal. |
| temperature_moyenne_7j | FLOAT64 | Température moyenne sur la fenêtre de 7 jours. |
| temperature_maximale_7j | FLOAT64 | Température maximale sur la fenêtre. |
| humidite_moyenne_7j | FLOAT64 | Humidité moyenne sur la fenêtre. |
| precipitations_7j | FLOAT64 | Somme des précipitations agrégées sur la fenêtre. |
| precipitations_moyennes_7j | FLOAT64 | Somme des précipitations moyennes sur la fenêtre complète. |
| rafale_vent_maximale_7j | FLOAT64 | Rafale maximale sur la fenêtre. |
| deficit_pression_vapeur_maximal_7j | FLOAT64 | VPD maximal sur la fenêtre. |
| jours_sans_pluie_7j | INT64 | Nombre de jours sans pluie sur la fenêtre. |
| nombre_jours_meteo_7j | INT64 | Nombre de jours météo complets disponibles. |
| meteo_disponible | BOOL | Vrai lorsque les 7 jours nécessaires sont complets. |

## ml_train_incendie

Grain : **une ligne par date de publication, département et échéance J1/J2**.

Les variables météo viennent de `ml_features_incendie`. Les colonnes supplémentaires sont :

| Colonne | Type | Description | Exemple / contrainte |
| --- | --- | --- | --- |
| id_apprentissage | STRING | Identifiant unique de la ligne d'apprentissage. | unique |
| reference_time | TIMESTAMP | Horodatage du bulletin. | horodatage Météo-France |
| date_publication | DATE | Date du bulletin. | 2026-07-15 |
| date_prevision | DATE | Date ciblée par le bulletin. | 2026-07-16 |
| numero_departement | STRING | Département. | `59` |
| departement | STRING | Nom du département. | Nord |
| region | STRING | Région. | Hauts-de-France |
| echeance | STRING | Échéance Météo-France. | J1 / J2 |
| horizon_jours | INT64 | Échéance sous forme numérique. | 1 / 2 |
| cible_niveau_danger | INT64 | Cible du modèle ML. | 1 à 4 |
| meteo_date | DATE | Date météo de référence. | publication - 7 jours |
| meteo_disponible | BOOL | Indique si la fenêtre météo est complète. | true / false |

Les autres colonnes de `ml_train_incendie` reprennent les variables météo simples et sur 7 jours décrites dans `ml_features_incendie`.
