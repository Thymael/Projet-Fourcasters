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

Le résultat de **62,54 % d'accuracy** et **0,404 de F1 macro** correspond à l'ancien split temporel 80/20. Il reste une référence historique et doit être remplacé par les métriques du nouveau test 2026 après réentraînement.

L'accuracy seule ne suffit pas : le F1 macro, le rappel par classe et la matrice de confusion doivent être présentés.

L'application Streamlit est une démonstration du modèle, pas un outil d'aide à la décision opérationnelle.

### Données personnelles

Le projet utilise des données météo, géographiques et des niveaux de danger. Il ne contient pas de données personnelles.

## Principe retenu

Les données officielles Météo-France restent la référence. Les résultats du modèle servent à apprendre, comparer et comprendre les limites d'une première approche de Machine Learning.
