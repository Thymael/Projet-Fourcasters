# Soutenance Fourcasters - trame de 15 minutes

Objectif réel : terminer entre **14 min et 14 min 30** pour garder une marge de changement d'écran. Les questions ne sont pas comprises dans les 15 minutes.

## Déroulé chronométré

| Temps cumulé | Support | Idée à faire passer |
| --- | --- | --- |
| 0:00 à 0:20 | Slide 1 | Présenter le projet et préciser qu'il a commencé en groupe puis a été finalisé individuellement. |
| 0:20 à 1:05 | Slide 2 | Expliquer le besoin métier sans jouer un client fictif. |
| 1:05 à 1:40 | Slide 3 | Formuler la question : relier la météo à un niveau officiel de danger par département. |
| 1:40 à 2:30 | Slide 4 | Montrer l'organisation du projet, GitHub, le Kanban Notion et les documents livrés. |
| 2:30 à 3:20 | Slide 5 | Résumer le parcours complet de la donnée. |
| 3:20 à 4:00 | Slide 6 | Présenter Open-Meteo, les 360 points et le décalage de six jours. |
| 4:00 à 4:35 | Slide 7 | Présenter Météo-France, les 96 départements et les niveaux J1/J2. |
| 4:35 à 5:25 | Slide 8 | Expliquer staging, intermediate et marts, puis une difficulté rencontrée. |
| 5:25 à 6:00 | Slide 9 | Expliquer l'automatisation quotidienne et les contrôles. |
| 6:00 à 6:45 | Slide 10 | Présenter la séparation temporelle 2024-2025 / 2026. |
| 6:45 à 7:40 | Slide 11 | Expliquer la fenêtre J-6 à J et le sens exact de J+1/J+2. |
| 7:40 à 8:30 | Slide 12 | Justifier le Random Forest et annoncer ses limites sans survendre le résultat. |
| 8:30 à 10:35 | Slide 13 puis Power BI | Présenter le rapport et commenter un constat sur deux pages maximum. |
| 10:35 à 13:55 | Slide 14 puis Streamlit | Montrer la dernière météo disponible, choisir un département et lire J+1/J+2. |
| 13:55 à 14:25 | Streamlit | Conclure directement sur l'interface. |

## Trame orale

### Slide 1 - Introduction

« Fourcasters est mon projet de fin de formation Data Analyst. Il a commencé en groupe, puis j'ai poursuivi la partie finale individuellement. Le projet relie des données météo à la Météo des forêts de Météo-France, depuis la collecte jusqu'à la restitution. »

### Slide 2 - Contexte

« Le besoin de départ est de rassembler des informations dispersées pour mieux lire les périodes et territoires sensibles. Je ne présente pas Fourcasters comme un outil opérationnel. C'est un projet d'analyse qui montre comment construire une chaîne de données complète et explicable. »

### Slide 3 - Problématique

« La question centrale est la suivante : comment rapprocher des observations météo avec un niveau de danger départemental compris entre 1 et 4 ? La difficulté vient surtout des grains différents : la météo est collectée sur 360 points, alors que le danger est publié pour 96 départements. »

### Slide 4 - Gestion de projet

« J'ai suivi les tâches dans Notion et versionné le code sur GitHub. Le dépôt contient le code Python, les modèles dbt, les tests et la documentation. J'ai aussi produit un dictionnaire de données, un guide Power BI, une matrice des risques et des notes sur l'éthique, la sobriété et la dépendance technologique. »

### Slide 5 - Architecture

« Les deux sources sont collectées en Python, enregistrées en Parquet, chargées dans Google Cloud Storage puis BigQuery. dbt prépare les tables d'analyse. Elles alimentent ensuite les notebooks, Power BI et le Machine Learning. Le pipeline entraîné est utilisé dans Streamlit. »

### Slide 6 - Open-Meteo

« Open-Meteo fournit les variables quotidiennes sur 360 points. J'utilise ERA5-Seamless, avec un décalage de six jours. Le pipeline cherche une seule journée manquante ou incomplète par exécution, puis traite les points par lots de 20. »

### Slide 7 - Météo-France

« La seconde source est la Météo des forêts. Elle donne un niveau de danger de 1 à 4 pour chaque département, à J1 et J2. Il s'agit d'un danger officiel prévu, pas du nombre de feux réellement observés. »

### Slide 8 - Transformation

« Dans dbt, le staging renomme et contrôle les données brutes. La couche intermediate agrège la météo au département. Les marts produisent les tables pour Power BI et pour le modèle. Une limite importante est que l'agrégation départementale peut masquer des différences locales. »

### Slide 9 - Automatisation

« GitHub Actions exécute chaque jour la collecte puis dbt. Le workflow vérifie les volumes, les clés et les tests avant de terminer. Le modèle n'est pas réentraîné tous les jours : je l'entraîne à la demande, ce qui reste suffisant pour ce prototype. »

### Slide 10 - Séparation temporelle

« Le jeu final contient 67 584 observations. J'entraîne sur 46 080 lignes de 2024 et 2025, puis je teste sur 21 504 lignes de 2026 jusqu'au 2 octobre. Cette séparation temporelle évite de mélanger des observations futures dans l'apprentissage. »

### Slide 11 - Variables et dates

« Le modèle utilise 14 variables. Certaines décrivent le jour J, les autres résument les sept jours de J-6 à J. Le point important est que J désigne la dernière date météo disponible. Si J est le 1er octobre, J+1 est le 2 octobre et J+2 le 3 octobre. Je ne pars jamais de la date civile du jour. »

### Slide 12 - Modèle et limites

« J'ai comparé une référence naïve, une régression logistique, un arbre de décision et un Random Forest. Le Random Forest obtient la meilleure accuracy avec 64,35 %, contre 42,28 % pour la référence naïve. Son F1 macro est de 0,417. Le modèle reconnaît mieux les niveaux 1 et 2. Le niveau 4 est trop rare et n'est pas correctement reconnu. »

### Slide 13 et démonstration Power BI

« Power BI sert à analyser l'historique et les niveaux officiels. Je commence par la vue générale, puis je montre la page Danger incendie. Ici, je commente un seul constat visible après avoir choisi une période et un département. Les prédictions du modèle ne sont pas dans Power BI : je les montre maintenant dans Streamlit. »

### Slide 14 et démonstration Streamlit

« L'application affiche d'abord la dernière journée météo complète disponible. Les dates J+1 et J+2 sont calculées à partir de cette date. Je choisis un département, puis je lis les deux niveaux estimés et la météo utilisée. La probabilité affichée reste indicative. »

### Conclusion sans revenir aux slides

« Fourcasters m'a permis de construire une chaîne complète, de la collecte à une restitution automatisée. La proposition finale fonctionne pour explorer les données et tester une première approche de classification, mais les niveaux officiels Météo-France restent la référence. »

## Préparation juste avant le passage

1. Ouvrir le PowerPoint en mode diaporama.
2. Ouvrir le fichier Power BI et afficher la Vue générale.
3. Lancer Streamlit avec `uv run python -m streamlit run streamlit_app.py`.
4. Vérifier que la première vue affiche une date météo, J+1 et J+2.
5. Garder les trois fenêtres déjà ouvertes et ne pas saisir de mot de passe pendant la présentation.
6. Faire une répétition chronométrée. Couper un commentaire, jamais la démonstration finale, si le temps dépasse 14 min 30.
