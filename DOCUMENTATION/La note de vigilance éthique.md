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

Le Random Forest obtient environ 55,5 % d'accuracy sur la période de test. Les niveaux 3 et 4 restent difficiles à reconnaître. L'accuracy seule ne suffit donc pas : le F1 macro et la matrice de confusion sont aussi présentés.

L'application Streamlit est une démonstration du modèle, pas un outil d'aide à la décision opérationnelle.

### Données personnelles

Le projet utilise des données météo, géographiques et des niveaux de danger. Il ne contient pas de données personnelles.

## Principe retenu

Les données officielles Météo-France restent la référence. Les résultats du modèle servent à apprendre, comparer et comprendre les limites d'une première approche de Machine Learning.
