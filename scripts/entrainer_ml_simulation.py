"""Entraîne le modèle utilisé par le simulateur Streamlit."""

import logging

from fourcasters_dbt.journal import configurer_logs
from fourcasters_dbt.ml_simulation import (
    FICHIER_PIPELINE_SIMULATION,
    charger_donnees_simulation,
    entrainer_modele_simulation,
    sauvegarder_modele_simulation,
)


def main() -> None:
    configurer_logs()

    print("Chargement du jeu de simulation depuis BigQuery...")
    donnees = charger_donnees_simulation()
    print(f"{len(donnees):,} lignes chargées")

    print("\nEntraînement du modèle de simulation...")
    modele, resultats = entrainer_modele_simulation(donnees)
    sauvegarder_modele_simulation(modele)

    print(f"Train : {resultats['nb_train']:,} lignes")
    print(f"Test  : {resultats['nb_test']:,} lignes")
    print(f"Dernier jour du train : {resultats['fin_train']}")
    print(f"Premier jour du test  : {resultats['debut_test']}")
    print(f"\nAccuracy : {resultats['accuracy']:.2%}")
    print(
        "Référence (classe majoritaire) : "
        f"{resultats['accuracy_reference']:.2%}"
    )
    print(f"F1 macro : {resultats['f1_macro']:.3f}")
    print(
        f"\nPipeline enregistré : "
        f"{FICHIER_PIPELINE_SIMULATION.name}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.getLogger(__name__).exception(
            "Entraînement du simulateur interrompu"
        )
        raise SystemExit(1)
