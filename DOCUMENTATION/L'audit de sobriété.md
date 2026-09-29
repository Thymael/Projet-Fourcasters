# Audit de sobriété numérique

L'objectif n'est pas de rendre Fourcasters parfaitement optimisé, mais d'éviter les traitements inutiles tout en gardant un projet compréhensible.

## 1. Collecte

Open-Meteo est interrogé uniquement lorsqu'une journée est absente ou incomplète dans BigQuery. Les 360 points sont regroupés par lots et un fichier Parquet permet de charger proprement le lot.

Météo-France est récupéré séparément et les archives historiques ne sont pas retéléchargées chaque jour.

**Choix retenu :** ne pas recollecter des données déjà présentes.

## 2. Stockage

Les nouveaux lots passent par un fichier Parquet et une table Landing avant d'être fusionnés dans l'historique BigQuery. Cela crée quelques fichiers temporaires, mais permet de contrôler le lot avant de modifier l'historique.

Les fichiers générés sont exclus de Git.

**Choix retenu :** garder cette étape de contrôle plutôt que simplifier au prix de la fiabilité.

## 3. dbt et BigQuery

Les transformations dbt construisent les tables nécessaires à l'analyse, Power BI et au ML. Certaines tables pourraient être rendues incrémentales, mais cela ajouterait de la complexité.

Pour ce projet étudiant, la priorité reste un SQL lisible et facile à vérifier.

**Choix retenu :** faire simple avant d'optimiser.

## 4. Machine Learning

Le Random Forest n'est pas réentraîné automatiquement chaque jour. Il est lancé à la demande, après construction des tables dbt.

Dernier entraînement après correction de la fenêtre météo D-6 à D :

| Modèle | Accuracy | F1 macro |
| --- | ---: | ---: |
| Classe majoritaire | 35,48 % | — |
| Random Forest | 62,54 % | 0,404 |

L'ancienne version du modèle utilisait une fenêtre D-13 à D-7 et obtenait 55,51 % d'accuracy pour 0,338 de F1 macro. La correction temporelle améliore donc les résultats, sans ajouter de collecte API ni d'entraînement automatique.

Une mesure ponctuelle CodeCarbon a estimé l'entraînement à environ 0,000002 kg de CO2 sur la machine utilisée.

**Choix retenu :** garder un modèle simple, réentraîné manuellement, plutôt qu'une grosse recherche automatique de paramètres.

## 5. Restitution

Power BI présente les analyses et Streamlit présente uniquement le prototype ML. Les deux interfaces doivent rester simples : peu de visuels, des filtres utiles et pas de calcul inutile dans l'interface.

## Bilan

Les principaux choix de sobriété sont : collecte incrémentale, chargement par lots, fichiers générés exclus de Git, entraînement ML à la demande et absence d'optimisation massive des hyperparamètres.

Ce niveau est suffisant pour le besoin et le niveau du projet.
