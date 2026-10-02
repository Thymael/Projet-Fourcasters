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

Le projet est gelé au **2 octobre 2026**, mais la période de test réellement disponible dans le run final va du **29 mai au 26 septembre 2026**, en raison du décalage de disponibilité des données météo. Le Random Forest final est évalué sur **21 696 lignes** et obtient **64,39 % d'accuracy** et **0,417 de F1 macro**. La référence naïve continue d'apprendre sa classe majoritaire uniquement sur l'apprentissage 2024-2025.

Les niveaux 1 et 2 sont les mieux reconnus. Le niveau 3 reste difficile avec un rappel de **20 %**. Le niveau 4 compte seulement **141 observations** dans le test et n'est pas correctement reconnu par le modèle (rappel **0 %**).

L'accuracy seule ne suffit donc pas : le F1 macro, le rappel par classe et la matrice de confusion doivent être présentés.

L'application Streamlit est une démonstration du modèle, pas un outil d'aide à la décision opérationnelle.

### Données personnelles

Le projet utilise des données météo, géographiques et des niveaux de danger. Il ne contient pas de données personnelles.

## Principe retenu

Les données officielles Météo-France restent la référence. Les résultats du modèle servent à apprendre, comparer et comprendre les limites d'une première approche de Machine Learning.
