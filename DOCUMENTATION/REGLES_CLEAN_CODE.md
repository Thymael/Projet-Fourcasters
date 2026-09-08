# Règles Clean Code

Ces règles servent de repère pour garder Fourcasters simple à lire et à
modifier. Le but n'est pas d'avoir le code le plus sophistiqué, mais un pipeline
que nous pouvons expliquer.

## Organisation

| Dossier | Rôle |
|---|---|
| `scripts/` | Points d'entrée lancés à la main ou par GitHub Actions |
| `src/fourcasters_dbt/` | Fonctions Python classées par sujet |
| `fourcasters/` | Modèles, sources et tests dbt |
| `DOCUMENTATION/` | Contrôles et décisions utiles au projet |

## Nos règles

1. Choisir des noms explicites en français : `nombre_departements` plutôt que
   `nb_dep`.
2. Commencer le nom d'une fonction par un verbe : `preparer_donnees()`.
3. Donner une seule responsabilité principale à chaque fonction.
4. Mettre les valeurs fixes en constantes majuscules.
5. Écrire une courte docstring pour les fonctions réutilisées.
6. Commenter une raison ou une règle métier, pas une ligne déjà évidente.
7. Mutualiser uniquement le code réellement commun aux deux sources.
8. Supprimer le code mort et les brouillons au lieu de les archiver dans le
   dépôt.
9. Lire les secrets depuis `.env` ou GitHub Secrets, jamais depuis le code.
10. Garder des affichages courts : `✅` succès, `⏳` attente, `❌` erreur.

Les annotations de type sont utiles quand elles rendent la fonction plus claire.
Elles ne sont pas obligatoires sur chaque variable.

## Avant un commit

```bash
uv run python -m py_compile \
  scripts/*.py \
  src/fourcasters_dbt/*.py

uv run dbt parse --project-dir fourcasters
git diff --check
```

Si les données ou les modèles changent, il faut aussi lancer :

```bash
uv run dbt build --project-dir fourcasters
```

Checklist rapide :

- [ ] le comportement attendu est conservé ;
- [ ] aucun secret ou fichier généré n'est suivi par Git ;
- [ ] les noms et commentaires sont compréhensibles ;
- [ ] les contrôles de volume et de doublons sont toujours présents ;
- [ ] le README correspond aux commandes actuelles.
