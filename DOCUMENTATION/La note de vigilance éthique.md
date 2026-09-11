# NOTE DE VIGILANCE ÉTHIQUE – FOURCASTERS
## CONTEXTE
Fourcasters analyse des données météo pour 360 points en France métropolitaine et les rapproche des niveaux de danger incendie publiés par Météo-France pour 96 départements.
Le projet contient également un premier modèle de Machine Learning.

## POINTS DE VIGILANCE REPÉRÉS
1. Représentativité des données
Les 360 points Open-Meteo couvrent la France métropolitaine mais pas les territoires d’outre-mer.
Ils ne correspondent pas à 360 stations météorologiques physiques. Il s’agit de points utilisés pour interroger les données de réanalyse Open-Meteo.
Le nombre de points n’est pas forcément identique dans chaque département.
Les zones rurales, urbaines, montagneuses et côtières peuvent donc être représentées différemment.
Une moyenne départementale peut également masquer des différences importantes à l’intérieur d’un même département.

2. Différence entre météo et danger incendie
L’historique météo commence en 2000 alors que les données Météo des forêts disponibles dans notre projet commencent en 2024.
Les deux sources ne doivent donc être comparées que sur leur période commune.
Les données Météo-France représentent également un niveau de danger prévu et non le nombre réel de feux qui se sont produits.
Il faut éviter de présenter notre modèle comme un modèle capable de prédire directement les incendies.

3. Limites du Machine Learning
Le modèle obtient environ 52,6 % d’accuracy sur le jeu de test.
Ce résultat est meilleur que la classe majoritaire, mais les performances sont très différentes selon le niveau de danger.
Les classes 1 et 2 sont les mieux reconnues.
Les classes 3 et surtout 4 restent mal prédites. Lors du dernier test, une seule ligne de niveau 4 sur 96 a été correctement classée.
Le modèle ne serait donc pas suffisamment fiable pour être utilisé dans une situation opérationnelle.
Utiliser uniquement son accuracy globale pourrait donner une impression trop positive de ses performances.

4. Impact possible des analyses
À terme, ce type d’analyse pourrait servir à identifier les territoires exposés ou à préparer des décisions concernant des moyens humains ou matériels.
Une erreur du modèle ou une zone géographique mal représentée pourrait alors faire sous-estimer un danger.
Les résultats doivent donc rester une aide à l’analyse et ne jamais remplacer les données officielles de Météo-France ou l’avis des professionnels concernés.

5. Données personnelles
Le projet actuel utilise uniquement des données météorologiques, géographiques et des niveaux de danger.
Il ne contient pas de noms, d’adresses personnelles ou d’informations concernant des individus.
Il faut conserver ce principe.
Si une gestion de comptes utilisateurs était ajoutée plus tard, ces données devraient être séparées du reste du projet et faire l’objet de protections adaptées.

## PRÉCAUTIONS PROPOSÉES
* Présenter clairement que les 360 points sont un échantillon géographique et non l’ensemble des communes françaises.
  **Bénéfice attendu :** éviter de donner une impression de précision supérieure à celle des données.
* Comparer uniquement les données météo et incendie sur les périodes où les deux sources sont disponibles.
  **Bénéfice attendu :** éviter des conclusions basées sur des périodes non comparables.
* Présenter l’accuracy avec le F1 macro, les résultats par classe et la matrice de confusion.
  **Bénéfice attendu :** rendre visibles les mauvaises performances sur les niveaux de danger élevés.
* Continuer à considérer les niveaux officiels Météo-France comme la référence.
  **Bénéfice attendu :** éviter qu’un modèle expérimental soit utilisé à la place d’une source officielle.
* Garder uniquement les données nécessaires au projet et ne pas ajouter de données personnelles sans raison précise.
  **Bénéfice attendu :** limiter les risques liés à la vie privée.

## CONCLUSION
Fourcasters ne traite pas directement de données personnelles et ne prend aucune décision automatiquement.
Les principaux risques concernent surtout la représentativité géographique, les différences de périodes entre les sources et les limites du modèle de Machine Learning.
Le point le plus important est de ne pas présenter les résultats comme des certitudes et de garder les données officielles et l’expertise humaine comme références.