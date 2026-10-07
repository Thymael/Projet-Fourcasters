# Soutenance Fourcasters - texte oral pour le PowerPoint d'origine

Support utilisé : `Fourcasters_Meteo_Incendies.pptx`, 47 diapositives avec plusieurs étapes d'animation. Le fichier n'a pas été modifié.

Objectif : finir entre **13 min 30 et 14 min 30**, démonstrations comprises. Les questions viennent ensuite.

## Repères importants avant de commencer

Plusieurs diapositives sont des étapes successives du même visuel. Il faut continuer à parler pendant les clics, sans recommencer l'explication à chaque slide.

Les chiffres reproduits le 7 octobre 2026 sont ceux à dire à l'oral :

- jeu complet : **67 776 observations** ;
- apprentissage : **46 080 observations** ;
- test : **21 696 observations** ;
- Random Forest : **64,39 % d'accuracy** et **0,417 de F1 macro** ;
- référence naïve : niveau 1, **42,18 % d'accuracy** ;
- régression logistique : **48,79 %** ;
- arbre de décision : **52,66 %** ;
- fenêtre météo : **J-6 à J**, soit sept jours ;
- CodeCarbon : environ **0,002 g CO2e** pour l'entraînement mesuré.

Les slides 35, 36, 37 et 39 montrent encore quelques anciennes valeurs. Le texte ci-dessous donne les valeurs finales. Ne pas lire les anciens nombres affichés.

## Déroulé chronométré

| Temps | Support | Sujet |
| --- | --- | --- |
| 0:00 à 1:30 | Slides 1 à 3 | Présentation, contexte et problématique |
| 1:30 à 2:30 | Slides 4 à 10 | Gestion du projet, étapes et outils |
| 2:30 à 3:40 | Slides 11 à 18 | Architecture et parcours de la donnée |
| 3:40 à 5:00 | Slides 19 à 23 | Collecte Open-Meteo et Météo-France |
| 5:00 à 6:20 | Slides 24 à 31 | Stockage, dbt et difficultés de transformation |
| 6:20 à 6:50 | Slides 32 à 33 | Rôle de Power BI |
| 6:50 à 9:20 | Slides 34 à 42 | Machine Learning, résultats et limites |
| 9:20 à 10:10 | Slides 43 à 44 | Automatisation GitHub Actions |
| 10:10 à 10:55 | Slides 45 à 47 | Conclusion et transition vers les dashboards |
| 10:55 à 12:30 | Power BI | Démonstration descriptive |
| 12:30 à 14:10 | Streamlit | Prédictions J+1 et J+2, puis conclusion |

## Texte à dire

### Slide 1 - Introduction

« Bonjour. Je vais vous présenter Fourcasters, mon projet de fin de formation Data Analyst.

Le projet a commencé en groupe avec Angélique, Christophe et Eddy, puis j'ai poursuivi sa finalisation individuellement. L'objectif était de construire une chaîne complète, depuis la récupération de données météo jusqu'à leur analyse dans Power BI et à une première expérimentation de Machine Learning dans Streamlit. »

### Slide 2 - Contexte

« Le cas de départ met en scène une responsable qui doit mieux comprendre les périodes et les territoires sensibles au danger incendie.

Je ne vais pas jouer le rôle d'un prestataire face à un faux client. Ce qui m'intéresse ici, c'est le problème de données : les informations sont dispersées, elles n'arrivent pas au même niveau géographique et elles doivent être rendues comparables.

Le but de Fourcasters est donc de collecter, historiser et restituer ces informations de manière compréhensible. »

### Slide 3 - Problématique

« La question centrale est : comment rapprocher des observations météo avec un niveau officiel de danger compris entre 1 et 4 ?

La principale difficulté vient du grain. La météo est collectée sur 360 points, tandis que Météo-France publie le danger pour 96 départements. Les données n'ont donc pas eu la politesse d'arriver déjà alignées. Il a fallu construire ce rapprochement. »

### Slides 4 à 10 - Gestion du projet et outils

« J'ai organisé le travail dans Notion avec un Kanban, puis versionné le code et les évolutions dans GitHub.

Le projet suit six grandes étapes : la collecte en Python, le stockage dans Google Cloud, la transformation avec dbt, l'analyse avec les notebooks et Power BI, le Machine Learning avec scikit-learn et Streamlit, puis l'automatisation avec GitHub Actions.

Le dépôt contient aussi la documentation livrée : schéma et dictionnaire des données, guide Power BI, matrice des risques, note éthique, audit de sobriété, dépendance technologique et positionnement face à l'AI Act. »

### Slides 11 à 18 - Architecture

« Voici le parcours complet de la donnée.

Open-Meteo et Météo-France constituent les deux sources. Python contrôle les réponses, les dates, les schémas et les doublons. Les lots validés passent par des fichiers Parquet, puis par Google Cloud Storage et BigQuery.

Dans BigQuery, je distingue une zone Landing pour le nouveau lot et une zone RAW pour l'historique. dbt transforme ensuite les données en trois couches : staging, intermediate et marts.

Les tables finales alimentent les notebooks, Power BI et le Machine Learning. Le modèle entraîné est enregistré dans un pipeline scikit-learn, puis utilisé par Streamlit. »

### Slides 19 et 20 - Open-Meteo

« La première source est Open-Meteo avec ERA5-Seamless. Le référentiel contient 360 points, principalement des préfectures, sous-préfectures et centroïdes.

La collecte traite les points par lots de 20. Elle attend six jours avant d'interroger une date, car les données historiques ne sont pas immédiatement disponibles. À chaque exécution, le pipeline récupère une seule journée absente ou incomplète.

Ce choix évite de recollecter tout l'historique quotidiennement. Mon ordinateur et l'API apprécient tous les deux. »

### Slides 21 à 23 - Historiques et Météo-France

« L'historique météo remonte à l'année 2000 et représente environ 3,4 millions de lignes.

La seconde source est la Météo des forêts de Météo-France. Elle publie, pour chaque département, un niveau pour le lendemain et un niveau pour le surlendemain.

Il faut bien distinguer ce niveau de danger d'un incendie observé. Le projet ne prédit pas un départ de feu et ne compte pas les incendies réels. Sa cible est le niveau officiel publié par Météo-France. »

### Slides 24 et 25 - Stockage

« Avant de modifier l'historique, chaque lot passe par un fichier Parquet et une table Landing. Je peux ainsi contrôler le nombre de lignes, les colonnes et les clés avant la fusion dans la table RAW.

Cette étape ajoute un intermédiaire, mais elle rend le chargement plus fiable et rejouable sans créer de doublons. »

### Slides 26 à 31 - Transformation avec dbt

« dbt prépare ensuite les données.

Le staging renomme, type et déduplique. La couche intermediate joint les référentiels et agrège la météo au niveau départemental. Les marts exposent les tables finales pour l'analyse, Power BI et le Machine Learning.

J'ai volontairement limité les transformations : normalisation des identifiants, gestion des noms avec apostrophes ou tirets, agrégations et contrôles de qualité. Une donnée ne devient pas propre simplement parce qu'on la regarde avec confiance.

Le modèle final reste lisible : dimensions pour les dates et les territoires, tables de faits pour la météo et le danger, puis tables spécialisées pour Power BI et le ML. »

### Slides 32 et 33 - Power BI

« Power BI constitue la restitution descriptive du projet. Il contient cinq pages : une vue générale, la météo des territoires, l'évolution temporelle, le danger incendie et le détail d'un département.

Il présente les données historiques et les niveaux officiels Météo-France. Les prédictions du modèle sont séparées et seront montrées dans Streamlit.

Je garde la démonstration détaillée pour la fin afin de terminer sur les dashboards, comme demandé. »

### Slides 34 à 37 - Préparation du Machine Learning

« Pour le Machine Learning, j'ai choisi une séparation temporelle plutôt qu'un découpage aléatoire.

Après la dernière reconstruction des tables, le jeu contient exactement 67 776 observations. L'apprentissage utilise 46 080 lignes de 2024 et 2025. Le test utilise 21 696 lignes de 2026, avec des dates prévues du 29 mai au 26 septembre.

Le modèle utilise 14 variables. Certaines décrivent le jour J et d'autres résument une fenêtre de sept jours, de J-6 à J.

J désigne toujours la dernière météo réellement disponible. Si ma météo s'arrête au 1er octobre, J+1 correspond au 2 octobre et J+2 au 3 octobre. Je ne tente pas de sauter artificiellement jusqu'à la date civile du jour. »

### Slides 38 et 39 - Comparaison des modèles

« J'ai comparé quatre approches sur exactement le même jeu de test.

La référence naïve prédit toujours le niveau 1, qui est la classe la plus fréquente dans l'apprentissage. Elle obtient 42,18 % d'accuracy.

La régression logistique obtient 48,79 %, l'arbre de décision 52,66 % et le Random Forest 64,39 %. Le F1 macro du Random Forest est de 0,417.

J'ai retenu le Random Forest parce qu'il donne le meilleur résultat parmi les modèles testés, tout en restant compréhensible et adapté au niveau du projet. Je n'ai pas lancé une recherche massive d'hyperparamètres pour gagner quelques décimales difficiles à expliquer. »

### Slides 40 et 41 - Limites du modèle

« L'accuracy seule ne suffit pas. Les niveaux 1 et 2 sont les mieux reconnus, mais le rappel du niveau 3 reste proche de 20 %.

Le niveau 4 ne compte que 141 observations dans le test et le modèle n'en retrouve aucune. C'est la limite principale du prototype : les classes rares et les niveaux élevés sont encore mal reconnus.

La matrice de confusion montre que le modèle confond surtout ces niveaux avec les classes voisines. Les résultats ne doivent donc pas servir à une décision opérationnelle. »

### Slide 42 - Streamlit

« Streamlit rend le modèle manipulable. La nouvelle vue part de la dernière météo complète disponible, calcule J+1 et J+2 et permet de sélectionner un département.

Je vous montrerai l'application en direct juste après Power BI. »

### Slides 43 et 44 - Automatisation

« GitHub Actions exécute chaque jour la collecte Open-Meteo, la collecte Météo-France et le dbt build.

Le workflow affiche chaque étape, son heure et son résultat. Lors du dernier contrôle, les dix dernières exécutions étaient réussies. La plus récente avait validé l'authentification, les deux collectes et tous les modèles et tests dbt.

Le Machine Learning reste volontairement entraîné à la demande. Cela évite un calcul quotidien inutile alors que la cible évolue lentement. »

### Slides 45 à 47 - Conclusion et transition

« Fourcasters m'a permis de travailler toute la chaîne d'un projet Data Analyst : la collecte, la qualité, le stockage, la transformation, l'analyse, la restitution et une première expérimentation de Machine Learning.

Les principales limites restent la couverture de 360 points, l'agrégation départementale, les calendriers différents entre les sources et le faible nombre de dangers très élevés.

Je vais maintenant terminer par les deux interfaces du projet : d'abord Power BI pour l'analyse descriptive, puis Streamlit pour les estimations du modèle. »

## Démonstration Power BI - environ 1 min 35

« Je commence par la Vue générale. Elle permet de vérifier le périmètre des données, les volumes et la période disponible.

Je passe ensuite à la page Danger incendie. Les filtres du haut permettent de choisir une période, un département et l'échéance J1 ou J2.

Cette page met en regard le niveau officiel Météo-France et la météo départementale associée. L'objectif est de comparer les périodes et les territoires, sans prétendre démontrer une causalité.

Enfin, la page Détail département permet d'approfondir un territoire précis. Pour rester dans le temps, je m'arrête à ces deux niveaux de lecture. »

## Démonstration Streamlit et conclusion - environ 1 min 40

« Je termine avec Streamlit.

En haut, l'application affiche la dernière météo complète disponible. Ici, je lis la date affichée : [lire la date]. J+1 et J+2 sont calculés directement à partir de cette référence.

Je sélectionne un département, par exemple le Var. L'application affiche le niveau estimé pour les deux horizons, avec la probabilité la plus élevée du modèle. Cette probabilité reste indicative.

Je peux également ouvrir la météo utilisée et consulter les prédictions de l'ensemble des départements. Un second onglet permet de comparer un ancien cas avec le niveau officiel, et le dernier rappelle la méthode et les limites.

Fourcasters propose donc une chaîne fonctionnelle et automatisée, avec une restitution descriptive dans Power BI et un prototype prédictif dans Streamlit. Le résultat est utile pour explorer et apprendre, mais les niveaux officiels Météo-France restent la référence.

Merci. »

## Checklist juste avant le passage

1. Ouvrir `Fourcasters_Meteo_Incendies.pptx` en mode diaporama.
2. Ouvrir le PBIX sur la page **Vue générale**.
3. Ouvrir Streamlit sur l'onglet **Prédictions** et sélectionner le Var.
4. Fermer ou masquer les notifications.
5. Garder les trois fenêtres ouvertes avant de commencer.
6. Faire défiler rapidement les slides d'animation sans répéter le texte.
7. Si le temps dépasse 14 min 30, raccourcir l'architecture et la transformation, pas les deux démonstrations finales.
