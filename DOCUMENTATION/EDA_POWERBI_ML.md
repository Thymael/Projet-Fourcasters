# Analyse, Power BI et ML

| Table | Une ligne représente | Utilisation |
|---|---|---|
| `int_meteo_departement_jour` | un département et un jour | météo agrégée |
| `pbi_risque_incendie` | un horodatage de bulletin, un département et J1/J2 | comparaison descriptive |
| `ml_features_incendie` | une date de publication et un département | météo décalée de sept jours |
| `ml_train_incendie` | une date de publication, un département et J1/J2 | apprentissage du dernier bulletin du jour |

## Lire les dates

`date_publication` est le jour du bulletin. `date_prevision` est le jour concerné
par son niveau de danger. Dans le PBIX fourni, le calendrier filtre les faits
incendie sur **date_prevision**.

La table `pbi_risque_incendie` associe chaque bulletin à la dernière journée
météo présente en base, antérieure ou égale à sa date de publication. Elle
conserve `date_meteo_utilisee` et `retard_meteo_jours` pour montrer le décalage.
C'est un rapprochement descriptif avec l'historique disponible aujourd'hui,
pas une preuve de ce qui était connu lors du bulletin.

Pour l'apprentissage, les tables ML utilisent un recul séparé de sept jours.
La règle de `pbi_risque_incendie` ne doit pas servir à construire leurs variables.

## Lire la pluie

Dans la table départementale, `precipitations_totales` est la somme des points.
Cette colonne historique est conservée pour la compatibilité, mais ce n'est
pas une hauteur de pluie représentative du département.

Pour comparer les départements, utiliser `precipitations_moyennes`. Pour un
cumul dans le temps, additionner ces moyennes journalières et vérifier la
période couverte. Le notebook et le ML suivent cette distinction.

## Notebook

[`01_eda_fourcasters.ipynb`](../notebooks/01_eda_fourcasters.ipynb) contrôle les
volumes, les périodes, la couverture, les valeurs manquantes et la répartition
du danger. Les graphiques et classements restent descriptifs. Aucun résultat
n'est prérempli : il faut exécuter le notebook avec les accès BigQuery.

Voir aussi le [modèle Power BI](MODELE_POWERBI.md) et la [méthode ML](ML_INCENDIE.md).
