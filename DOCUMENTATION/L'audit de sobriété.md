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

La fenêtre météo finale est **J-6 à J**, avec J défini comme la date de référence disposant de la météo nécessaire. Le modèle apprend uniquement sur les cibles Météo-France de **2024 et 2025**, puis il est évalué sur les cibles **2026 jusqu'au 2 octobre inclus**.

Le dernier entraînement de la version gelée utilise **46 080 lignes d'apprentissage** et **21 696 lignes de test**, soit **67 776 lignes** au total dans le split final. La période de test réellement disponible va du **29/05/2026 au 26/09/2026**. Le Random Forest obtient **64,39 % d'accuracy** et **0,417 de F1 macro**.

La référence naïve est un `DummyClassifier(strategy="most_frequent")` : elle apprend la classe majoritaire uniquement sur les données d'apprentissage 2024-2025, puis applique cette règle au test 2026. Son accuracy et son F1 macro doivent être recalculés avec le même jeu de test final que le Random Forest.

La mesure CodeCarbon du modèle final est de **0,000003 kg CO2e**, soit **0,003 g CO2e** pour l'entraînement mesuré. Cette valeur est conservée avec les métriques et le périmètre du run final.

**Choix retenu :** garder un modèle simple, réentraîné manuellement, plutôt qu'une grosse recherche automatique de paramètres.

## 5. Restitution

Power BI présente les analyses et Streamlit présente uniquement le prototype ML. Les deux interfaces doivent rester simples : peu de visuels, des filtres utiles et pas de calcul inutile dans l'interface.

## Bilan

Les principaux choix de sobriété sont : collecte incrémentale, chargement par lots, fichiers générés exclus de Git, entraînement ML à la demande et absence d'optimisation massive des hyperparamètres.

Ce niveau est suffisant pour le besoin et le niveau du projet.
