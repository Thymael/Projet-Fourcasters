from pathlib import Path

import pandas as pd


DOSSIER_MOVIELENS = Path("data/raw/movielens/ml-latest-small")


def charger_donnees() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Charge les quatre fichiers du dataset MovieLens."""
    films = pd.read_csv(DOSSIER_MOVIELENS / "movies.csv")
    notes = pd.read_csv(DOSSIER_MOVIELENS / "ratings.csv")
    liens = pd.read_csv(DOSSIER_MOVIELENS / "links.csv")
    tags = pd.read_csv(DOSSIER_MOVIELENS / "tags.csv")

    return films, notes, liens, tags


def afficher_resume(
    films: pd.DataFrame,
    notes: pd.DataFrame,
    liens: pd.DataFrame,
    tags: pd.DataFrame,
) -> None:
    """Affiche les principales informations du dataset MovieLens."""
    print("\n🎬 RÉSUMÉ DU DATASET MOVIELENS")
    print(f"Films : {len(films):,}")
    print(f"Notes : {len(notes):,}")
    print(f"Utilisateurs : {notes['userId'].nunique():,}")
    print(f"Tags : {len(tags):,}")
    print(f"Note minimale : {notes['rating'].min()}")
    print(f"Note maximale : {notes['rating'].max()}")
    print(f"Note moyenne : {notes['rating'].mean():.2f}")

    print("\n🔗 IDENTIFIANTS EXTERNES")
    print(f"Identifiants IMDb manquants : {liens['imdbId'].isna().sum()}")
    print(f"Identifiants TMDb manquants : {liens['tmdbId'].isna().sum()}")

    print("\n📋 PREMIERS FILMS")
    print(films.head())


def verifier_donnees(
    films: pd.DataFrame,
    notes: pd.DataFrame,
) -> None:
    """Contrôle les doublons de films et les notes hors limites."""
    doublons_films = films["movieId"].duplicated().sum()
    notes_invalides = (~notes["rating"].between(0.5, 5)).sum()

    print("\n🔎 CONTRÔLES")
    print(f"movieId en double : {doublons_films}")
    print(f"Notes invalides : {notes_invalides}")

    if doublons_films == 0 and notes_invalides == 0:
        print("✅ Les contrôles principaux sont réussis.")
    else:
        print("⚠️ Certaines données doivent être vérifiées.")


def main() -> None:
    """Charge MovieLens, affiche son résumé et contrôle ses données."""
    films, notes, liens, tags = charger_donnees()
    afficher_resume(films, notes, liens, tags)
    verifier_donnees(films, notes)


if __name__ == "__main__":
    main()