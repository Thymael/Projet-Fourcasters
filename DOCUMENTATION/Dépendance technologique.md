## NOTRE DÉPENDANCE TECHNOLOGIQUE
### CONTEXTE
Fourcasters utilise plusieurs services et technologies externes :
* Google Cloud Storage et BigQuery pour le stockage et les traitements des données ;
* GitHub pour le dépôt du code ;
* GitHub Actions pour l’actualisation automatique ;
* Power BI pour les tableaux de bord ;
* dbt pour transformer les données ;
* Open-Meteo et Météo-France comme sources de données ;
* Python et scikit-learn pour le Machine Learning ;
* ChatGPT comme outil d’aide pendant le développement et la documentation.
Certaines de ces technologies sont propriétaires alors que d’autres sont open source.

### RISQUES REPÉRÉS
Si nous perdions l’accès à Google Cloud, une grande partie du pipeline serait bloquée car les données sont stockées dans BigQuery et les fichiers d’actualisation passent par Cloud Storage.
Sans GitHub, le projet pourrait toujours fonctionner localement, mais nous perdrions le dépôt distant et l’automatisation avec GitHub Actions.
Sans Power BI, les données resteraient disponibles dans BigQuery, mais il faudrait reconstruire les tableaux de bord avec un autre outil.
dbt Core, Python et scikit-learn sont open source. Ils sont donc plus faciles à déplacer vers une autre infrastructure.
Open-Meteo et Météo-France restent également des dépendances importantes : si leur API change, le pipeline de collecte doit être adapté.
ChatGPT n’est pas intégré au fonctionnement de Fourcasters. Sa disparition ralentirait surtout le travail de développement ou de recherche, mais ne bloquerait ni les collectes, ni BigQuery, ni dbt, ni Power BI.

### DEUX IDÉES POUR RÉDUIRE CETTE DÉPENDANCE
* Sauvegarder les données importantes dans des formats ouverts comme CSV ou Parquet et conserver tout le code SQL, Python et dbt dans Git.
  **Bénéfice attendu :** pouvoir déplacer plus facilement le projet vers une autre infrastructure sans perdre les données ou la logique des traitements.
* Documenter des solutions alternatives pour les principaux services. Par exemple PostgreSQL ou DuckDB pour certaines données et Metabase ou Apache Superset pour la dataviz.
  **Bénéfice attendu :** savoir vers quelle solution se tourner si un service devient indisponible ou trop coûteux.

### CONCLUSION
Fourcasters dépend encore beaucoup de Google Cloud, GitHub et Power BI.
Cette dépendance reste cependant limitée par le fait que les données peuvent être exportées dans des formats standards et qu’une grande partie du code utilise des technologies ouvertes comme Python, SQL, dbt Core et scikit-learn.
Le projet pourrait donc être déplacé vers d’autres outils, même si cela demanderait du travail d’adaptation.