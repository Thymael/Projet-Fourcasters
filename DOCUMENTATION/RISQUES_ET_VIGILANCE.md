# Risques et limites

Le dépôt consulté traite la météo, la géographie et le danger prévu. Il ne
contient pas d'application avec des comptes utilisateurs. Les cinq risques
liés aux comptes dans la matrice Excel sont donc des scénarios futurs.
Leurs cotations ont été conservées, sans les présenter comme des incidents
ou des fonctionnalités actuelles.

| Risque actuel | Réponse du projet | Limite restante |
|---|---|---|
| API indisponible ou quota | délai maximum, trois essais, arrêt sur échec | le service externe reste nécessaire |
| Données incomplètes | contrôle des dates, colonnes, codes, volumes et fenêtres ML | la fraîcheur Météo-France doit être interprétée selon la saison |
| Doublons lors d'une relance | hash stable, MERGE et contrôle dans une transaction | les données historiques déjà incorrectes demandent une investigation |
| Mauvaise jointure | grain documenté, clés uniques, relation département/jour | ne pas additionner les bulletins comme des feux réels |
| Clé publiée par erreur | secrets hors du code et des logs | les droits effectifs du compte cloud restent à vérifier |
| Évaluation ML trompeuse | séparation par dates, écart J1/J2, référence majoritaire et F1 par classe | validation rétrospective ; seulement 1 % de rappel sur le niveau 4 lors de l'essai du 11 septembre 2026 |

## Interprétation

Les 360 points couvrent la métropole mais ne décrivent pas tous les reliefs
et microclimats. Les niveaux Météo-France sont des prévisions, pas des départs
de feu. Les variables météo seules ne décrivent ni la végétation, ni l'activité
humaine, ni les moyens d'intervention.

Pour comparer la pluie entre départements, utiliser une moyenne des points,
puis un cumul dans le temps sur une période comparable. Une donnée absente
n'est pas un zéro.

## Calcul et stockage

Open-Meteo récupère les journées manquantes par lots de dix points, jusqu'à
sept journées par exécution. Les tables finales dbt restent reconstruites
entièrement. Une évolution incrémentale sera utile si le coût mesuré le
justifie, à condition de traiter aussi les corrections de journées anciennes.

La jointure Power BI utilise des périodes de validité pour retrouver la
dernière météo disponible, sans produire toutes les combinaisons antérieures
à chaque bulletin. Aucun gain de coût réel n'est annoncé sans mesure BigQuery.

Le profil dbt est configuré en US. Il reprend le projet existant ; aucune
migration géographique n'a été effectuée. Les sauvegardes et règles de
conservation du bucket ne sont pas contrôlées depuis ce dépôt.

## Logs et reprise

GitHub conserve la sortie console des workflows. Les fichiers locaux de
reprise sont exclus de Git et ne survivent pas aux machines éphémères de
GitHub Actions. Les Parquet envoyés dans Cloud Storage restent utiles au rejeu.

Une source déjà chargée n'est pas annulée si l'autre échoue. Chaque source a
son propre historique et sa propre transaction. Les scripts s'arrêtent sur
l'erreur et la construction dbt n'est pas lancée par le workflow si une collecte
échoue.
