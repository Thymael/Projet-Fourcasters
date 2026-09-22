# Audit de sobriété numérique

L'objectif n'est pas de rendre Fourcasters parfaitement optimisé, mais d'éviter les traitements inutiles tout en gardant un projet compréhensible.

## 1. Collecte

Open-Meteo est interrogé uniquement lorsqu'une journée est absente ou incomplète dans BigQuery. Les 360 points sont regroupés par lots et un CSV temporaire permet de reprendre une collecte interrompue.

Météo-France est récupéré séparément et les archives historiques ne sont pas retéléchargées chaque jour.

**Choix retenu :** ne pas recollecter des données déjà présentes.

## 2. Stockage

Les nouveaux lots passent par un fichier Parquet et une table Landing avant d'être fusionnés dans l'historique BigQuery. Cela crée quelques fichiers temporaires, mais permet de contrôler le lot avant de modifier l'historique.

Les CSV et Parquet générés sont exclus de Git.

**Choix retenu :** garder cette étape de contrôle plutôt que simplifier au prix de la fiabilité.

## 3. dbt et BigQuery

Les transformations dbt construisent les tables nécessaires à l'analyse, Power BI et au ML. Certaines tables pourraient être rendues incrémentales, mais cela ajouterait de la complexité.

Pour ce projet étudiant, la priorité reste un SQL lisible et facile à vérifier.

**Choix retenu :** faire simple avant d'optimiser.

## 4. Machine Learning

Le Random Forest a été comparé à des modèles plus simples :

| Modèle | Accuracy | F1 macro |
| --- | ---: | ---: |
| Classe majoritaire | 38,43 % | — |
| Régression logistique | 29,06 % | 0,253 |
| Arbre de décision | 37,46 % | 0,275 |
| Random Forest | 55,51 % | 0,338 |

Le modèle n'est pas réentraîné automatiquement chaque jour. Une mesure ponctuelle CodeCarbon a estimé l'entraînement à environ 0,000002 kg de CO2 sur la machine utilisée.

**Choix retenu :** pas de grosse recherche automatique de paramètres tant que les limites viennent surtout des données et des classes rares.

## 5. Restitution

Power BI présente les analyses et Streamlit présente uniquement le prototype ML. Les deux interfaces doivent rester simples : peu de visuels, des filtres utiles et pas de calcul inutile dans l'interface.

## Bilan

Les principaux choix de sobriété sont : collecte incrémentale, reprise après interruption, chargement par lots, fichiers générés exclus de Git, entraînement ML à la demande et absence d'optimisation massive des hyperparamètres.

Ce niveau est suffisant pour le besoin et le niveau du projet.
