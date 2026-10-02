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

Le support final indique un ordre de grandeur d'environ **71 000 observations exploitables**, réparties en environ **46 500 lignes d'apprentissage** et **24 400 lignes de test**. Les effectifs et performances exacts sont volontairement lus dans la sortie du dernier entraînement plutôt que recopiés ici avant la clôture du dataset.

La référence naïve est un `DummyClassifier(strategy="most_frequent")` : elle apprend la classe majoritaire uniquement sur les données d'apprentissage 2024-2025, puis applique cette règle au test 2026. Son accuracy et son F1 macro doivent être recalculés avec le même jeu de test final que le Random Forest.

La mesure CodeCarbon doit également être relancée sur le modèle final après le dernier `dbt build`. L'ancienne mesure n'est plus présentée comme résultat final car le jeu de données et le protocole ML ont évolué.

**Choix retenu :** garder un modèle simple, réentraîné manuellement, plutôt qu'une grosse recherche automatique de paramètres.

## 5. Restitution

Power BI présente les analyses et Streamlit présente uniquement le prototype ML. Les deux interfaces doivent rester simples : peu de visuels, des filtres utiles et pas de calcul inutile dans l'interface.

## Bilan

Les principaux choix de sobriété sont : collecte incrémentale, chargement par lots, fichiers générés exclus de Git, entraînement ML à la demande et absence d'optimisation massive des hyperparamètres.

Ce niveau est suffisant pour le besoin et le niveau du projet.
