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
    print("RÉSULTATS")
    print("=" * 40)
    print(f"Accuracy : {resultats['accuracy']:.2%}")
    print(f"F1 macro : {resultats['f1_macro']:.3f}")
    print(f"Émissions estimées : {emissions:.6f} kg de CO2")


if __name__ == "__main__":
    main()


# Mesure réalisée le 11/09/2026 :
# environ 0.000002 kg de CO2 pour l'entraînement du modèle.