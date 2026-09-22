# Dépendance technologique

Fourcasters utilise plusieurs services extérieurs : Google Cloud, GitHub, Open-Meteo, Météo-France, Power BI et Streamlit. Le projet utilise aussi Python, dbt Core et scikit-learn, qui sont open source.

## Principales dépendances

**Google Cloud** stocke les fichiers et les données BigQuery. Une panne ou une perte d'accès bloquerait une grande partie du pipeline.

**Open-Meteo et Météo-France** fournissent les données sources. Si leur API ou leur format change, les scripts de collecte doivent être adaptés.

**GitHub Actions** automatise l'actualisation quotidienne. Le projet pourrait toujours être lancé en local sans GitHub, mais il faudrait lancer les commandes manuellement.

**Power BI** sert à présenter les analyses. Les données resteraient dans BigQuery si Power BI n'était plus disponible.

**Streamlit** sert uniquement à présenter le prototype ML. Le modèle reste un Pipeline scikit-learn indépendant de l'interface.

ChatGPT a été utilisé comme aide pendant le développement. Il n'est pas intégré au fonctionnement du projet.

## Comment limiter cette dépendance ?

Deux choix simples permettent de garder le projet transportable :

- conserver les données importantes dans des formats ouverts comme CSV ou Parquet ;
- garder le code Python, SQL et dbt dans Git afin de pouvoir changer d'infrastructure si besoin.

Le projet reste assez dépendant de Google Cloud, mais la logique principale repose sur des formats et des outils standards.
