"""Entraîne le modèle incendie et enregistre le Pipeline."""

import logging

from fourcasters_dbt.journal import configurer_logs
from fourcasters_dbt.ml_incendie import (
    FICHIER_PIPELINE,
    charger_donnees,
    entrainer_modele,
    sauvegarder_modele,
)


def main() -> None:
    configurer_logs()

    print("Chargement des données depuis BigQuery...")
    donnees = charger_donnees()
    print(f"{len(donnees):,} lignes chargées")

    print("\nEntraînement du modèle...")
    modele, resultats = entrainer_modele(donnees)
    sauvegarder_modele(modele)

    print(f"Train : {resultats['nb_train']:,} lignes")
    print(f"Test  : {resultats['nb_test']:,} lignes")
    print(f"Dernier jour du train : {resultats['fin_train']}")
    print(f"Premier jour du test  : {resultats['debut_test']}")
    print(f"Lignes laissées entre les deux périodes : {resultats['nb_ecartes']}")

    print(f"\nAccuracy : {resultats['accuracy']:.2%}")
    print(f"Référence (classe majoritaire) : {resultats['accuracy_reference']:.2%}")
    print(f"F1 macro : {resultats['f1_macro']:.3f}")

    print("\nRapport de classification")
    print(resultats["rapport"])

    print("Matrice de confusion (réel en lignes, prédit en colonnes)")
    print(resultats["matrice_confusion"])

    print("\nVariables les plus importantes")
    print(resultats["importance"].head(10).to_string())

    print(f"\nPipeline enregistré : {FICHIER_PIPELINE.name}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.getLogger(__name__).exception("Entraînement interrompu")
        raise SystemExit(1)
