# Règles Clean Code du projet Fourcasters

Ce document sert de référence pour les prochaines modifications du projet. Il
reprend le cours « Clean Code, Modules et Refactorisation » en l'adaptant au
pipeline Fourcasters.

## Ce qui est déjà bien construit

- les deux sources ont chacune une orchestration clairement séparée ;
- les secrets ne sont pas écrits dans le code ;
- les appels API possèdent des tentatives et un délai maximum ;
- les collectes contrôlent le nombre de communes ou de départements ;
- les `row_hash` empêchent les doublons ;
- le pipeline Open-Meteo reprend les communes manquantes ;
- le mode `--local-only` permet de tester l'API incendie sans écrire dans GCP.

Ces règles métier doivent être conservées pendant une refactorisation.

## Problèmes repérés avant la refactorisation

| Problème | Conséquence | Correction retenue |
|---|---|---|
| Scripts d'environ 370 lignes | Lecture difficile | Déplacer les fonctions dans `src/fourcasters_dbt/` |
| Code exécuté directement au chargement | Import et test difficiles | Utiliser une fonction `main()` |
| Fonctions de plus de 50 lignes | Plusieurs responsabilités mélangées | Extraire de petites fonctions |
| Paramètres en minuscules | Valeurs métier peu visibles | Utiliser des constantes en majuscules |
| Code GCS et BigQuery répété | Deux endroits à corriger | Créer un module `google_cloud.py` |
| Commentaires sur presque chaque ligne | Le code devient plus long | Commenter uniquement les choix non évidents |

## Règles à conserver pour la suite

1. Une variable est un nom clair : `nombre_departements`, pas `n`.
2. Une fonction commence par un verbe : `preparer_donnees()`.
3. Une fonction réalise une tâche principale.
4. Une valeur métier ou technique stable devient une constante en majuscules.
5. Un bloc utilisé par plusieurs pipelines devient une fonction partagée.
6. Une fonction réutilisable possède une courte docstring.
7. Un commentaire explique **pourquoi**, pas ce que la ligne dit déjà.
8. Le code inutilisé est supprimé ou déplacé dans `ARCHIVES/`.
9. Les secrets viennent de l'environnement ou de GitHub Secrets.
10. Le fichier principal contient les orchestrations, tandis que les fonctions
    métier restent dans les modules du dossier `src/`.

Les annotations de type sont utiles lorsqu'elles restent simples. Elles ne
doivent pas rendre un script étudiant plus difficile à lire.

## Structure retenue

```text
scripts/
├── actualiser_fourcasters.py
└── importer_archives_meteofrance.py

src/fourcasters_dbt/
├── configuration.py
├── google_cloud.py
├── openmeteo.py
└── incendie.py
```

- `actualiser_fourcasters.py` contient `main_openmeteo()`, `main_incendie()` et
  le `main()` général appelé par le workflow ;
- `importer_archives_meteofrance.py` reste un outil ponctuel séparé ;
- `configuration.py` contient les chemins et constantes partagés ;
- `google_cloud.py` contient le code commun à GCS et BigQuery ;
- `openmeteo.py` et `incendie.py` gardent leurs règles métier séparées.

## Méthode obligatoire avant chaque refactorisation

1. Exécuter ou contrôler la version actuelle et noter le résultat de référence.
2. Modifier un seul sujet : organisation **ou** nouvelle fonctionnalité.
3. Vérifier la syntaxe :

   ```bash
   uv run python -m py_compile \
     scripts/actualiser_fourcasters.py \
     scripts/importer_archives_meteofrance.py \
     src/fourcasters_dbt/*.py
   ```

4. Tester le traitement concerné sans écrire dans le cloud lorsque c'est
   possible.
5. Comparer les volumes, dates, colonnes et `row_hash` avec la référence.
6. Exécuter `uv run dbt build --project-dir fourcasters` si les tables ou les
   modèles sont concernés.
7. Faire un commit au message précis, puis pousser la branche.

## Checklist avant commit

- [ ] noms explicites ;
- [ ] une responsabilité principale par fonction ;
- [ ] aucune duplication évitable ;
- [ ] constantes nommées ;
- [ ] docstrings sur les fonctions partagées ;
- [ ] commentaires utiles uniquement ;
- [ ] aucun code mort ;
- [ ] aucun secret suivi par Git ;
- [ ] comportement et résultats inchangés pour une refactorisation ;
- [ ] README mis à jour uniquement si l'utilisation du projet change.
