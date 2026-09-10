# Conventions du projet

Nous gardons des fonctions courtes, des noms explicites et un parcours facile
à suivre : récupérer, contrôler, enregistrer, charger.

- Les commandes sont dans `scripts/`, les fonctions dans `src/fourcasters_dbt/`.
- Une fonction a un rôle principal. Les appels HTTP, le logging et le chargement
  communs sont regroupés, sans ajouter de classes ou de framework.
- Les noms sont en français. Les constantes sont en majuscules.
- Une courte docstring explique les fonctions utiles. Les commentaires précisent
  une règle métier ou une décision qui ne se voit pas directement dans le code.
- Les collectes utilisent `logging`, avec quelques emojis pour identifier les étapes.
  Le script ML garde `print` pour présenter ses tableaux de résultats.
- Les erreurs temporaires sont réessayées trois fois. Une erreur de format ou
  d'identification arrête le traitement. Aucun `except` ne masque un échec.
- Les secrets restent dans `.env` ou GitHub Secrets. Les logs n'affichent pas
  les en-têtes d'authentification.

## Fiabilité des chargements

Les collectes sont validées avant l'envoi. Le chargement remplace une table de
réception, jamais l'historique. Le `row_hash` identifie une date et un point
Open-Meteo, ou un horodatage de bulletin et un département Météo-France.

La fusion et son contrôle final partagent une transaction BigQuery. Si une
instruction échoue avant `COMMIT`, BigQuery annule cette transaction. Les
fichiers Cloud Storage et la table de réception restent disponibles pour
comprendre l'erreur. Chaque source a sa propre transaction : l'échec de
Météo-France n'annule pas une journée Open-Meteo déjà validée.
[Comportement des transactions BigQuery](https://docs.cloud.google.com/bigquery/docs/transactions).

L'import d'archives a sa propre table de réception pour ne pas écraser celle
de la collecte quotidienne. Deux lancements identiques depuis des machines
différentes doivent néanmoins être évités.

## Vérifier une modification

```bash
uv run pytest -q
uv run dbt parse --project-dir fourcasters
git diff --check
```

Les tests utilisent des données fictives. Deux tests HTTP simulent des réponses
avec `monkeypatch` : cela évite un appel réel et une attente pendant les tests.
Après un changement SQL, exécuter aussi `dbt build` avec les accès BigQuery.
Une analyse syntaxique seule ne valide pas les données du cloud.

Ces choix reprennent les cours Clean Code, fiabilité, logging et validation
consultés dans le Drive de formation. La validation reste faite avec pandas et
des conditions simples ; ajouter Pydantic n'était pas nécessaire ici.
