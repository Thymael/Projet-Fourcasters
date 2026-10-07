# Note de vigilance éthique

Fourcasters rapproche des données météo de 360 points en France métropolitaine avec les niveaux de danger Météo-France pour 96 départements.

## Limites à garder en tête

### Représentativité

Les 360 points ne représentent pas toutes les communes françaises et ne sont pas des stations météo physiques. Une moyenne départementale peut aussi masquer des différences locales.

### Périodes différentes

L'historique météo commence en 2000 alors que la Météo des forêts disponible dans le projet commence en 2024. Les comparaisons doivent donc être faites uniquement sur la période commune.

### Danger prévu, pas incendies observés

La cible du modèle est le niveau de danger publié par Météo-France. Fourcasters ne prédit pas le nombre réel de feux.

### Limites du modèle

Le modèle est désormais entraîné uniquement sur les cibles Météo-France de **2024 et 2025** puis évalué sur les cibles **2026** disponibles. Cette séparation annuelle évite d'utiliser une partie de 2026 pendant l'apprentissage.

L'évaluation finale est réalisée sur **24 288 observations** de 2026, avec des dates prévues du 29 mai au 2 octobre. Le Random Forest atteint **64,94 % d'accuracy** et **0,417 de F1 macro**. La référence naïve atteint **43,17 % d'accuracy** ; elle apprend sur l'entraînement 2024-2025 que le niveau 1 est la classe la plus fréquente.

Les niveaux 1 et 2 sont les mieux reconnus. Le niveau 3 reste difficile avec un rappel de **20 %**. Le niveau 4 compte seulement **147 observations** dans le test et n'est pas correctement reconnu par le modèle (rappel **0 %**).

L'accuracy seule ne suffit donc pas : le F1 macro, le rappel par classe et la matrice de confusion doivent être présentés.

L'application Streamlit part de la dernière date météo complète et affiche des estimations J+1 et J+2. Elle reste une démonstration du modèle, pas un outil d'aide à la décision opérationnelle.

### Données personnelles

Le projet utilise des données météo, géographiques et des niveaux de danger. Il ne contient pas de données personnelles.

## Principe retenu

Les données officielles Météo-France restent la référence. Les résultats du modèle servent à apprendre, comparer et comprendre les limites d'une première approche de Machine Learning.
