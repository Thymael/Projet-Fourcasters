# Risques et points de vigilance

Fourcasters utilise des données météo et géographiques. Il ne traite pas de
données personnelles, mais cela ne supprime pas tous les risques.

## Synthèse

| Risque | Impact possible | Réponse du projet |
|---|---|---|
| Données incomplètes ou API indisponible | Analyse fausse ou pipeline bloqué | tentatives, délais maximum et contrôles de volume |
| Doublons pendant une relance | Résultats surestimés | clé `row_hash` et `MERGE` BigQuery |
| Biais géographique | Certaines zones sont mal représentées | documenter les 360 points et les limites du périmètre |
| Confusion entre danger et feux réels | Mauvaise interprétation | nommer clairement le danger **prévu** Météo-France |
| Dépendance aux services cloud | Pipeline indisponible ou coûteux | formats ouverts, code dbt et requêtes SQL versionnés |
| Fuite d'une clé | Accès non autorisé aux services | `.env`, GitHub Secrets et fichiers de clés ignorés par Git |

## Environnement

La collecte est incrémentale : une seule journée Open-Meteo et une publication
Météo-France sont ajoutées à chaque exécution. Les 360 communes sont demandées
par lots pour limiter le nombre d'appels. Les fichiers locaux sont générés dans
`data/` et ne sont pas versionnés.

Le principal point à surveiller reste le coût des reconstructions dbt. Si le
volume augmente beaucoup, `fact_meteo` pourra devenir incrémentale. Les variables
météo devront aussi être revues après l'EDA afin de ne garder que celles qui sont
utiles.

## Éthique et interprétation

- le périmètre couvre la France métropolitaine, pas les territoires ultramarins ;
- un point d'observation ne représente pas toujours tout le relief d'une zone ;
- le danger incendie est une prévision, pas une observation de départ de feu ;
- les résultats doivent aider l'analyse, pas remplacer l'avis des services
  spécialisés.

Ces limites doivent apparaître dans le rapport Power BI et dans le futur travail
de Machine Learning.

## Risque technique

Le projet dépend d'Open-Meteo, de Météo-France, de Google Cloud, de GitHub et de
dbt. Une panne, un changement d'API ou un quota peut interrompre le traitement.
Les données intermédiaires sont donc enregistrées en Parquet, tandis que le code
SQL et dbt restent portables. Les contrôles BigQuery permettent de repérer une
actualisation manquante.

## Utilisation de l'IA

L'IA peut aider à relire ou expliquer du code, mais les choix, les tests et la
validation finale restent humains. Aucun secret ni jeu de données confidentiel
ne doit lui être transmis. Une proposition générée doit être comprise avant
d'être intégrée au projet.
