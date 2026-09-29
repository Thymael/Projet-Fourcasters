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

La fenêtre météo utilisée est D-6 à D. Le modèle apprend maintenant uniquement sur les cibles Météo-France de 2024 et 2025, puis il est évalué sur toutes les cibles 2026 disponibles.

Avec le split annuel final, le Random Forest est entraîné sur **46 080 lignes** de 2024-2025 et testé sur **21 504 lignes** de 2026. Il obtient **64,35 % d'accuracy** et **0,417 de F1 macro**.

La référence naïve obtient **42,28 % d'accuracy**. C'est un `DummyClassifier(strategy="most_frequent")` : il prédit toujours la classe la plus fréquente dans les données d'apprentissage et sert seulement de repère minimal à battre.

L'ancien split temporel 80/20 obtenait 62,54 % d'accuracy et 0,404 de F1 macro. Il est conservé uniquement comme repère historique.

Une mesure ponctuelle CodeCarbon a estimé l'entraînement à environ 0,000002 kg de CO2 sur la machine utilisée.

**Choix retenu :** garder un modèle simple, réentraîné manuellement, plutôt qu'une grosse recherche automatique de paramètres.

## 5. Restitution

Power BI présente les analyses et Streamlit présente uniquement le prototype ML. Les deux interfaces doivent rester simples : peu de visuels, des filtres utiles et pas de calcul inutile dans l'interface.

## Bilan

Les principaux choix de sobriété sont : collecte incrémentale, chargement par lots, fichiers générés exclus de Git, entraînement ML à la demande et absence d'optimisation massive des hyperparamètres.

Ce niveau est suffisant pour le besoin et le niveau du projet.
