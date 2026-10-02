from codecarbon import EmissionsTracker

from fourcasters_dbt.ml_incendie import (
    charger_donnees,
    entrainer_modele,
)


def main() -> None:
    """Entraîne le modèle et mesure les émissions estimées par CodeCarbon."""

    print("Chargement des données...")
    donnees = charger_donnees()

    print("Démarrage de la mesure CodeCarbon...")

    tracker = EmissionsTracker(
        project_name="fourcasters_ml",
    )

    tracker.start()

    print("Entraînement du modèle...")
    _, resultats = entrainer_modele(donnees)

    emissions = tracker.stop()

    print()
    print("Résultats")
    print("=" * 40)
    print(f"Train : {resultats['nb_train']:,} lignes")
    print(f"Test  : {resultats['nb_test']:,} lignes")
    print(f"Période test : {resultats['debut_test']} -> {resultats['fin_test']}")
    print(f"Accuracy : {resultats['accuracy']:.2%}")
    print(f"F1 macro : {resultats['f1_macro']:.3f}")
    print(f"Émissions estimées : {emissions:.6f} kg CO2e")
    print(f"Émissions estimées : {emissions * 1000:.3f} g CO2e")


if __name__ == "__main__":
    main()
