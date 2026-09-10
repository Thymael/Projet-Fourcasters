# Modèle du Power BI fourni

Référence : `Fourcasters_Dashboard.pbix`, consulté le 10 septembre 2026.
Le fichier contient 7 tables, 87 colonnes, 7 relations et 37 mesures DAX.
Les six tables métier viennent de `openmeteo_analyse` dans BigQuery.
`Mesures` est une table technique créée dans Power BI.

## Tables

| Table | Colonnes | Rôle |
|---|---:|---|
| `dim_date` | 11 | calendrier, saisons et jours |
| `dim_commune` | 9 | 360 points météo |
| `dim_departement` | 3 | 96 départements |
| `fact_meteo` | 33 | météo par point et par jour |
| `fact_danger_incendie` | 8 | danger par bulletin, département et échéance |
| `pbi_risque_incendie` | 22 | danger et dernière météo associée |
| `Mesures` | 1 | colonne de support des 37 mesures DAX |

Les mesures DAX ne sont pas des colonnes stockées. Elles ne sont donc pas
ajoutées aux champs métier du schéma JSON.

## Relations présentes

Toutes sont de type un-à-plusieurs, avec un filtre simple de la dimension
vers la table de faits.

| Dimension et clé | Table et clé filtrées | État |
|---|---|---|
| `dim_date.date` | `fact_meteo.date` | active |
| `dim_commune.code_insee` | `fact_meteo.code_insee` | active |
| `dim_departement.numero_departement` | `fact_meteo.numero_departement` | active |
| `dim_date.date` | `fact_danger_incendie.date_prevision` | active |
| `dim_departement.numero_departement` | `fact_danger_incendie.numero_departement` | active |
| `dim_date.date` | `pbi_risque_incendie.date_prevision` | active |
| `dim_departement.numero_departement` | `pbi_risque_incendie.numero_departement` | inactive |

L'ancien JSON reliait le danger au calendrier sur `date_publication` et
reliait `dim_departement` à `dim_commune`. Ces relations ne correspondent pas
au PBIX reçu. Le JSON actualisé reprend les relations du tableau ci-dessus.
La relation inactive est nommée explicitement : le format de diagramme ne
possède pas de commande native d'activation Power BI.

## Pages et mesures

Le rapport contient Vue générale, Météo des territoires, Évolution temporelle,
Danger incendie et Détail département. Les mesures couvrent la météo, le danger,
la couverture des données et les libellés de lecture du rapport.

La mesure `Precipitations cumulees` calcule le cumul par commune puis la
moyenne des communes sélectionnées. Cette logique est cohérente pour éviter
de sommer les hauteurs de pluie de plusieurs points géographiques.

## Une formule à corriger dans Power BI Desktop

`Derniere publication` utilise `REMOVEFILTERS(dim_date_publication)`, mais
cette table est absente du modèle reçu. Cette référence invalide doit être
retirée. La formule proposée, sous le même nom de mesure, est :

```dax
Derniere publication =
CALCULATE(
    MAX(fact_danger_incendie[reference_time]),
    REMOVEFILTERS(dim_date),
    REMOVEFILTERS(fact_danger_incendie[echeance])
)
```

Le PBIX a été conservé sans modification. Cette formule n'y a donc pas été
appliquée. Le rendu des visuels et leur connexion effective à BigQuery restent
à vérifier dans Power BI Desktop.

La relation inactive vers `pbi_risque_incendie` est également conservée. Si un
visuel utilise cette table et doit suivre le filtre département, vérifier
son comportement avant de modifier la relation.

## Limites de cette consultation

Les définitions des cinq pages, leurs visuels, les requêtes Power Query,
les colonnes, les relations et les 37 mesures ont été inspectées. Le modèle
est connecté à BigQuery en DirectQuery ; l'extraction de sa structure ne
permet pas de confirmer le contenu actuel des tables ni le rendu du rapport.
