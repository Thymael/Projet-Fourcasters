## ÉTAPE 1/5 – À la source : Open-Meteo et Météo-France
### CONTEXTE
Fourcasters récupère des données météo pour 360 points en France métropolitaine afin d’étudier les conditions météorologiques et le danger d’incendie.
Le projet utilise deux sources :
* Open-Meteo pour les données météorologiques ;
* Météo-France pour le niveau de danger de la Météo des forêts.

### CONSTAT
L’historique Open-Meteo couvre la période du 1er janvier 2000 au 31 juillet 2026. Depuis août 2026, le projet cherche chaque jour la première journée absente ou incomplète dans BigQuery.
Un retard volontaire de 6 jours est conservé pour attendre la disponibilité des données ERA5.
Les 360 points ne sont pas demandés un par un. Ils sont regroupés par lots de 10 communes. Une journée complète représente donc au maximum 36 lots.
Le script garde également un fichier CSV temporaire permettant de reprendre une collecte interrompue sans recommencer les communes déjà récupérées.
Pour Météo-France, le projet récupère les niveaux de danger J1 et J2 pour les 96 départements métropolitains.

### GASPILLAGES REPÉRÉS
* Open-Meteo fournit de nombreuses variables météo. Certaines sont utilisées dans Power BI ou dans le Machine Learning, mais toutes n’ont pas forcément la même utilité.
* Une nouvelle journée nécessite plusieurs appels à l’API Open-Meteo.
* Les deux sources sont interrogées régulièrement alors qu’il peut arriver qu’aucune nouvelle donnée ne soit nécessaire.

### ACTIONS PROPOSÉES
* Conserver la vérification de BigQuery avant la collecte.
  **Bénéfice attendu :** ne pas télécharger une journée déjà complète.
* Continuer à regrouper les communes par lots.
  **Bénéfice attendu :** réduire le nombre de requêtes envoyées à Open-Meteo.
* Faire une liste des variables réellement utilisées dans l’EDA, Power BI et le Machine Learning avant d’en supprimer.
  **Bénéfice attendu :** éviter de collecter et stocker des données inutiles sans supprimer trop vite une variable intéressante.

### CONCLUSION
La collecte est maintenant incrémentale et sait reprendre une journée incomplète. Elle évite donc de recommencer inutilement tout l’historique.
Le principal point de vigilance restant concerne le nombre de variables météo conservées.

---

## ÉTAPE 2/5 – Au stockage : fichiers temporaires, Cloud Storage et BigQuery
### CONTEXTE
Après la collecte, Fourcasters prépare les nouvelles données avant de les intégrer dans l’historique.

### CONSTAT
Pour Open-Meteo, les lots récupérés sont d’abord enregistrés dans un CSV de reprise. Une fois la journée complète et contrôlée, un fichier Parquet est créé.
Pour Météo-France, un fichier Parquet est également préparé.
Les fichiers sont ensuite envoyés dans Google Cloud Storage puis chargés dans une table de réception BigQuery.
Après validation, un `MERGE` ajoute ou met à jour les données dans les tables historiques :
* `openmeteo_raw.meteo_journaliere` ;
* `meteofrance_raw.meteo_forets`.
Cette organisation ajoute quelques étapes de stockage, mais elle permet de contrôler les données avant de modifier l’historique.

### GASPILLAGES REPÉRÉS
* Une même actualisation peut temporairement exister en CSV, en Parquet, dans Cloud Storage, dans une table landing puis dans la table historique.
* Les fichiers stockés dans Cloud Storage peuvent s’accumuler s’ils sont conservés sans limite.
* Les fichiers locaux peuvent également prendre de la place s’ils ne sont jamais nettoyés.
* Le volume historique augmente tous les jours, même si l’ajout quotidien reste relativement faible.

### ACTIONS PROPOSÉES
* Conserver les fichiers intermédiaires seulement lorsqu’ils sont utiles pour la reprise ou la traçabilité.
  **Bénéfice attendu :** éviter les copies inutiles.
* Prévoir à terme une règle de conservation pour les anciens fichiers de Cloud Storage.
  **Bénéfice attendu :** empêcher l’accumulation permanente de fichiers qui ne servent plus.
* Continuer à exclure du dépôt Git les fichiers de données, `.venv`, les logs, les caches et les fichiers générés.
  **Bénéfice attendu :** garder un dépôt léger.

### CONCLUSION
Le pipeline utilise davantage d’étapes qu’une écriture directe dans BigQuery, mais cela permet de valider une actualisation avant de toucher à l’historique.
Pour ce projet, nous avons préféré la fiabilité à la suppression de toutes les étapes intermédiaires.

---

## ÉTAPE 3/5 – Aux requêtes : BigQuery et dbt
### CONTEXTE
BigQuery conserve les données historiques et dbt construit les tables utilisées pour l’analyse, Power BI et le Machine Learning.

### CONSTAT
La météo représente plusieurs millions de lignes.
dbt construit notamment :
* les tables de staging ;
* les tables intermédiaires ;
* les dimensions ;
* les tables de faits ;
* les tables utilisées par Power BI ;
* les données préparées pour le Machine Learning.
Le projet final réalise un `dbt build` complet avec 101 étapes réussies, sans erreur ni avertissement.
Les tables finales restent volontairement simples et sont principalement reconstruites complètement.
Ce choix n’est pas le plus économique en calcul, mais il rend le projet plus facile à comprendre et à maintenir dans le cadre de notre formation.

### GASPILLAGES REPÉRÉS
* Plusieurs millions de lignes peuvent être relues ou recalculées alors qu’une actualisation quotidienne ne représente qu’une petite quantité de nouvelles données.
* Les tests dbt sont eux aussi relancés sur l’ensemble du projet.
* Une requête BigQuery mal filtrée peut lire beaucoup plus de données que nécessaire.
* Les reconstructions complètes utilisent davantage de calcul qu’un modèle incrémental.

### ACTIONS PROPOSÉES
* Garder les filtres sur les dates et sélectionner uniquement les colonnes nécessaires dans les analyses.
  **Bénéfice attendu :** limiter les données lues par BigQuery.
* Si le projet devait grossir fortement, rendre certaines grosses tables dbt incrémentales.
  **Bénéfice attendu :** traiter principalement les nouvelles données au lieu de reconstruire plusieurs années.
* Pour le projet de formation, conserver pour l’instant la version simple tant que les temps d’exécution restent raisonnables.
  **Bénéfice attendu :** éviter d’ajouter de la complexité uniquement pour optimiser quelques minutes de calcul.

### CONCLUSION
C’est probablement à ce niveau que se trouve la principale amélioration possible en matière de sobriété.
Le projet pourrait être davantage optimisé avec des modèles incrémentaux, mais nous avons volontairement privilégié un pipeline simple, compréhensible et testé.

---

## ÉTAPE 4/5 – Au Machine Learning
### CONTEXTE
Fourcasters contient maintenant un premier modèle de Machine Learning permettant d’essayer de reproduire le niveau de danger Météo-France.
La cible comporte quatre niveaux de danger.

### CONSTAT
Le modèle utilisé est un `RandomForestClassifier`.
Il utilise :
* 200 arbres ;
* 14 variables ;
* une séparation chronologique entre apprentissage et test ;
* un équilibrage des classes ;
* aucune recherche automatique de centaines de combinaisons de paramètres.
Lors du dernier test, 66 432 lignes ont été utilisées.
Le modèle atteint environ 52,6 % d’accuracy contre 32,4 % pour une prédiction utilisant toujours la classe majoritaire.
Les niveaux 1 et 2 sont les mieux reconnus. Les niveaux 3 et surtout 4 restent difficiles à prédire.
Le modèle est uniquement un prototype. Il n’est pas déployé et il n’est pas réentraîné automatiquement chaque jour.

### GASPILLAGES REPÉRÉS
* Une forêt de 200 arbres demande plus de calcul qu’un modèle très simple.
* Relancer l’entraînement plusieurs fois sans modification des données ou du modèle serait inutile.
* Une recherche automatique très large de paramètres pourrait entraîner des dizaines ou centaines de modèles pour un gain limité.
* Les données sont rechargées depuis BigQuery à chaque lancement du script.

### ACTIONS PROPOSÉES
* Continuer à lancer l’entraînement uniquement lorsqu’il est nécessaire.
  **Bénéfice attendu :** éviter des calculs sans intérêt.
* Ne pas lancer de grosse recherche automatique de paramètres tant que les limites principales viennent surtout du manque d’exemples des niveaux 3 et 4.
  **Bénéfice attendu :** éviter de consommer beaucoup de calcul pour optimiser un jeu de données encore limité.
* Mesurer ponctuellement la consommation du modèle avec CodeCarbon.
  **Bénéfice attendu :** avoir une mesure réelle plutôt qu’une estimation de l’impact du Machine Learning.
* Comparer éventuellement le modèle actuel avec une version plus petite, par exemple avec moins d’arbres.
  **Bénéfice attendu :** vérifier si un modèle plus léger donne des résultats proches.

### CONCLUSION
Le modèle reste relativement simple pour un premier prototype.
Nous n’avons pas cherché à entraîner de nombreux modèles ou à lancer une grosse optimisation automatique.
La priorité reste surtout d’améliorer les données disponibles pour les niveaux de danger élevés plutôt que d’augmenter la puissance de calcul.

---

## ÉTAPE 5/5 – À l’application et à la dataviz
### CONTEXTE
Les résultats du projet sont présentés dans Power BI.
Le rapport contient cinq pages permettant d’explorer la météo, son évolution et le danger incendie.

### CONSTAT
Power BI utilise les tables préparées dans BigQuery par dbt.
Le modèle contient notamment :
* `dim_date` ;
* `dim_commune` ;
* `dim_departement` ;
* `fact_meteo` ;
* `fact_danger_incendie` ;
* `pbi_risque_incendie`.
Le rapport utilise également plusieurs mesures DAX.
Les données météo et incendie n’ont pas exactement la même granularité.
La météo est disponible par point géographique et par jour alors que le danger incendie est fourni au niveau du département.
Les données incendie couvrent également une période beaucoup plus courte que les données météo.

### GASPILLAGES REPÉRÉS
* Un rapport contenant trop de visuels peut générer beaucoup de requêtes.
* Des filtres inutiles ou incompatibles peuvent interroger les données pour finalement afficher un résultat vide.
* Les pages trop chargées sont également plus difficiles à comprendre pour l’utilisateur.
* Les données météo anciennes peuvent être interrogées alors qu’une page concerne uniquement la période couverte par la Météo des forêts.

### ACTIONS PROPOSÉES
* Garder uniquement les visuels qui apportent réellement une information.
  **Bénéfice attendu :** réduire les requêtes et rendre le tableau de bord plus lisible.
* Utiliser le département comme niveau géographique principal sur la page danger incendie.
  **Bénéfice attendu :** respecter la granularité réelle des données Météo-France.
* Adapter les filtres de dates aux périodes réellement disponibles.
  **Bénéfice attendu :** éviter des requêtes qui ne peuvent produire aucun résultat.
* Ne pas multiplier les actualisations ou interactions sans besoin.
  **Bénéfice attendu :** réduire les requêtes envoyées vers BigQuery.

### CONCLUSION
Power BI permet de rendre les données beaucoup plus accessibles, mais la sobriété passe aussi par une interface simple.
Le but n’est donc pas d’ajouter le maximum de graphiques possibles, mais de garder ceux qui permettent réellement de comprendre les données.

---

## BILAN FINAL
Fourcasters n’est pas un projet parfaitement optimisé en matière de sobriété numérique.
Certaines tables sont encore reconstruites entièrement et plusieurs copies temporaires d’une actualisation existent pendant le pipeline.
En revanche, plusieurs choix limitent déjà les traitements inutiles :
* collecte incrémentale ;
* reprise après interruption ;
* appels Open-Meteo par lots ;
* contrôle avant chargement ;
* fichiers de données exclus de Git ;
* Machine Learning relativement simple ;
* absence de recherche massive de paramètres ;
* entraînement du modèle uniquement à la demande ;
* limitation du projet à la France métropolitaine et aux données nécessaires à notre sujet.

Pour notre projet étudiant, le niveau de sobriété nous semble donc **plutôt satisfaisant**, tout en gardant plusieurs pistes d’amélioration.