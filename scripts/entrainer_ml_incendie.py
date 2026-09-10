"""Entraîne simplement le modèle de danger incendie."""

from fourcasters_dbt.ml_incendie import (
    charger_donnees,
    entrainer_modele,
)


def main() -> None:
    """Lance l'entraînement et affiche les résultats."""

    print("🌲 APPRENTISSAGE DU DANGER MÉTÉO-FRANCE")
    print()

    print("📥 Chargement des données depuis BigQuery...")

    donnees = charger_donnees()

    print(f"✅ {len(donnees):,} lignes chargées")
    print()

    print("🤖 Entraînement du modèle...")

    _, resultats = entrainer_modele(donnees)

    print()
    print(f"Train : {resultats['nb_train']:,} lignes")
    print(f"Test  : {resultats['nb_test']:,} lignes")

    print()
    print(
        f"🎯 Accuracy : "
        f"{resultats['accuracy']:.2%}"
    )

    print()
    print("📊 Rapport de classification")
    print(resultats["rapport"])

    print("🔥 Variables les plus importantes")
    print(
        resultats["importance"]
        .head(10)
        .to_string()
    )


if __name__ == "__main__":
    main()