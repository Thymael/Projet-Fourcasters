# Guide utilisateur Power BI — Fourcasters

## À quoi sert le tableau de bord ?

Le rapport Power BI sert à explorer les **niveaux de danger Météo-France** et les conditions météo associées par département.

Il ne présente pas la prédiction du modèle de Machine Learning. Le ML est montré séparément dans Streamlit.

## Source des données

Power BI utilise principalement la table BigQuery :

`pbi_risque_incendie`

Cette table est construite par dbt à partir :
- des niveaux de danger Météo-France ;
- de la météo agrégée par département ;
- du référentiel des départements.

La météo associée à un bulletin correspond à la dernière journée disponible au plus tard à la date de publication. La colonne `retard_meteo_jours` permet de voir ce décalage.

## Mise à jour

Le pipeline GitHub Actions actualise quotidiennement Open-Meteo, Météo-France et les modèles dbt.

La table BigQuery peut donc évoluer chaque jour. Le rapport Power BI doit ensuite être actualisé selon la configuration utilisée dans Power BI.

## Principaux indicateurs

| Indicateur | Définition |
| --- | --- |
| Niveau de danger | Niveau officiel Météo-France, de 1 à 4. |
| Température moyenne | Température moyenne agrégée à l'échelle du département. |
| Température maximale | Température maximale observée parmi les points du département. |
| Humidité moyenne | Humidité relative moyenne du département. |
| Précipitations | Précipitations issues des points météo du département. |
| Vitesse moyenne du vent | Vitesse moyenne du vent à l'échelle départementale. |
| Rafale maximale | Rafale maximale observée dans le département. |
| VPD maximal | Déficit de pression de vapeur maximal ; indicateur du caractère sec de l'air. |
| Retard météo | Écart en jours entre la date du bulletin et la météo utilisée. |

## Lire le niveau de danger

| Niveau | Lecture |
| ---: | --- |
| 1 | Faible |
| 2 | Modéré |
| 3 | Élevé |
| 4 | Très élevé |

Ces niveaux sont ceux publiés par Météo-France. Fourcasters ne les remplace pas.

## Utilisation

La lecture du rapport se fait principalement par :
- date ;
- département ou région ;
- échéance J1/J2 ;
- niveau de danger ;
- variables météo.

Les filtres exacts et la navigation dépendent de la version du fichier Power BI utilisée.

## Captures à conserver avec le livrable

Pour la version finale du projet, ajouter dans cette documentation :
1. une capture de la page d'accueil du rapport ;
2. une capture montrant les filtres principaux ;
3. une capture du modèle de données Power BI si celui-ci est présenté à l'oral.

Une courte légende sous chaque capture suffit.

## En cas de problème

Vérifier d'abord :
1. que le pipeline GitHub Actions s'est terminé correctement ;
2. que `dbt build` ne contient pas de test en erreur ;
3. que `pbi_risque_incendie` contient des données récentes ;
4. que Power BI a bien été actualisé.

Pour une question sur le projet, utiliser les Issues du dépôt GitHub ou contacter Loïck M.
