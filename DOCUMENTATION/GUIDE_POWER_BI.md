# Guide utilisateur Power BI — Fourcasters

## À quoi sert le tableau de bord ?

Le rapport Power BI sert à explorer les données météo du projet et les **niveaux de danger Météo-France** par territoire et dans le temps.

Il ne présente pas la prédiction du modèle de Machine Learning. Le ML est montré séparément dans Streamlit.

## Organisation du rapport

Le rapport suit une lecture du général au détail :

1. **Vue générale** : couverture des données, volumes et tendance générale.
2. **Météo des territoires** : comparaison des conditions météo entre régions, départements et communes.
3. **Évolution temporelle** : évolution et saisonnalité des principaux indicateurs météo.
4. **Danger incendie** : niveaux de danger Météo-France et contexte météo associé.
5. **Détail département** : fiche détaillée du territoire sélectionné.

Chaque page répond à une question principale et évite de multiplier les graphiques qui racontent la même chose.

Le fichier livré est `Fourcasters - Modèle Open-Meteo et danger incendie Météo-France.pbix`.

## Source des données

Power BI utilise les tables préparées par dbt dans BigQuery.

Pour l'analyse du danger incendie, la table principale est :

`pbi_risque_incendie`

Elle rapproche :
- les niveaux de danger Météo-France ;
- la météo agrégée par département ;
- le référentiel des départements.

La météo associée à un bulletin correspond à la dernière journée disponible au plus tard à la date de publication. La colonne `retard_meteo_jours` permet de rendre ce décalage visible.

## Mise à jour

Le pipeline GitHub Actions actualise quotidiennement Open-Meteo, Météo-France et les modèles dbt.

La table BigQuery peut donc évoluer chaque jour. Le rapport Power BI doit ensuite être actualisé selon la configuration utilisée dans Power BI.

## Filtres

### Pages météo

Les pages météo utilisent la période complète disponible dans `dim_date`.

### Pages danger incendie

Sur **Danger incendie** et **Détail département**, le filtre s'appelle **Période de prévision**.

Il reste basé sur la dimension de dates commune au rapport afin de conserver les interactions entre météo et danger, mais les dates proposées sont limitées aux jours où la mesure **Nombre previsions** est supérieure à 0.

Cela évite de sélectionner une période couverte par Open-Meteo mais absente des données de prévision Météo-France.

Sur la page Danger incendie, les trois filtres principaux sont regroupés en haut :

- Période de prévision ;
- Département ;
- Échéance J1/J2.

Le filtre de période incendie n'est plus synchronisé avec les pages purement météo.

## Principaux indicateurs

| Indicateur | Définition |
| --- | --- |
| Niveau de danger | Niveau officiel Météo-France, de 1 à 4. |
| Température moyenne | Température moyenne agrégée à l'échelle du département. |
| Température maximale | Température maximale observée parmi les points du département. |
| Humidité moyenne | Humidité relative moyenne du département. |
| Précipitations | Précipitations issues des points météo du département. |
| Vitesse moyenne du vent | Vitesse moyenne du vent à l'échelle départementale. |
| Rafale maximale | Rafale maximale observée dans le département. |
| VPD maximal | Déficit de pression de vapeur maximal ; indicateur du caractère sec de l'air. |
| Retard météo | Écart en jours entre la date du bulletin et la météo utilisée. |

## Lire le niveau de danger

| Niveau | Lecture |
| ---: | --- |
| 1 | Faible |
| 2 | Modéré |
| 3 | Élevé |
| 4 | Très élevé |

Les couleurs associées aux niveaux ont une signification constante dans le rapport :

- vert : niveau 1 ;
- jaune : niveau 2 ;
- orange : niveau 3 ;
- rouge : niveau 4.

La couleur n'est pas utilisée seule : le numéro et le libellé du niveau restent affichés.

Ces niveaux sont ceux publiés par Météo-France. Fourcasters ne les remplace pas.

## Principes de présentation utilisés

Les graphiques ont été simplifiés pour faciliter la lecture :

- titres descriptifs : mesure puis axe d'analyse ;
- suppression des quadrillages inutiles ;
- légendes supprimées lorsqu'une seule série est affichée ;
- étiquettes directement sur les barres de comparaison quand elles restent lisibles ;
- axes conservés sur les graphiques temporels car l'échelle peut changer avec les filtres ;
- tris décroissants sur les classements territoriaux ;
- même couleur pour une même signification ;
- rouge réservé à un niveau de danger élevé, pas à un simple élément à mettre en avant.

Les pages utilisent des titres descriptifs plutôt que des conclusions figées, car les données changent avec les filtres et les actualisations.

## Comment utiliser le rapport

Commencer par la **Vue générale**, puis choisir la page correspondant à la question recherchée.

Pour analyser le danger incendie :

1. choisir une **Période de prévision** ;
2. sélectionner éventuellement un département ;
3. choisir J1 ou J2 si nécessaire ;
4. lire d'abord les chiffres clés ;
5. observer ensuite l'évolution des niveaux ;
6. comparer les territoires ;
7. ouvrir le détail d'un département si nécessaire.

## Présenter un graphique à l'oral

Pour les graphiques principaux, garder toujours le même ordre :

1. annoncer ce que le graphique représente ;
2. donner le constat principal avec un chiffre ;
3. expliquer rapidement les axes et la période ;
4. proposer une explication seulement si elle est réellement étayée par les données.

Une présentation orale n'a pas besoin de commenter tous les visuels du rapport. Trois ou quatre graphiques principaux suffisent généralement ; les autres restent disponibles pour répondre aux questions.

## Accessibilité

Le rapport utilise des contrastes élevés et évite de transmettre une information uniquement par la couleur.

Des textes alternatifs sont renseignés sur les principaux graphiques et filtres. Les niveaux de danger conservent également leur numéro et leur libellé en plus de leur couleur.

## Démonstration pendant la soutenance

La démonstration tient en environ deux minutes :

1. ouvrir la **Vue générale** et préciser le périmètre des données ;
2. passer à **Danger incendie** ;
3. choisir une période et un département ;
4. commenter un constat visible, sans parcourir tous les graphiques ;
5. rappeler que les niveaux affichés dans Power BI sont les niveaux officiels Météo-France ;
6. passer ensuite à Streamlit pour montrer les prédictions du modèle.

## En cas de problème

Vérifier d'abord :

1. que le pipeline GitHub Actions s'est terminé correctement ;
2. que `dbt build` ne contient pas de test en erreur ;
3. que `pbi_risque_incendie` contient des données récentes ;
4. que Power BI a bien été actualisé ;
5. sur les pages incendie, que la période choisie appartient bien à la période de prévision proposée par le segment.

Pour une question sur le projet, utiliser les Issues du dépôt GitHub ou contacter Loïck M.
