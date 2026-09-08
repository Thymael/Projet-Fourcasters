# EDA, Power BI et ML

## Tables préparées

| Table | Grain | Utilisation |
|---|---|---|
| `int_meteo_departement_jour` | département + jour | base commune pour les agrégations |
| `pbi_risque_incendie` | publication + département + échéance | rapport Power BI |
| `ml_features_incendie` | date de publication + département | variables d'un futur modèle |
| `ml_train_incendie` | publication + département + échéance | apprentissage J1/J2 |

`pbi_risque_incendie` associe le danger prévu à la météo disponible à la date
de publication. La jointure ne se fait donc pas sur la date J1 ou J2 : cela
évite de présenter une météo future comme une information connue au moment de
la prévision.

## Power BI

La table `pbi_risque_incendie` peut être importée comme table principale.
Ajouter ensuite :

- une relation sur `date_publication` vers `dim_date.date` ;
- une relation sur `numero_departement` vers `dim_departement.numero_departement`.

Quelques indicateurs simples à créer : nombre de publications, niveau moyen de
danger, part des niveaux 3 et 4, et taux de lignes avec météo disponible.

## Machine Learning

`ml_features_incendie` contient notamment les moyennes, maxima et cumuls météo
sur les sept derniers jours connus avant la publication. Le niveau de danger
n'est pas copié dans cette table pour éviter une fuite de cible.

`ml_train_incendie` ajoute ensuite la cible `cible_niveau_danger` issue de
Météo-France, avec l'échéance `J1` ou `J2`. Le projet cherche donc à reproduire
la classe de danger publiée par Météo-France, et non à prévoir si un incendie
réel va effectivement se déclarer.

Pour le ML, on pourra commencer par un modèle de classification à quatre
classes. L'échéance peut être utilisée comme variable, ou bien on peut
entraîner un modèle séparé pour J1 et pour J2.

## EDA

Le notebook [`notebooks/01_eda_fourcasters.ipynb`](../notebooks/01_eda_fourcasters.ipynb)
contrôle les volumes, les périodes, les valeurs manquantes et la répartition
des niveaux de danger. Il sert de point de départ avant de construire les
graphiques du rapport Power BI.
