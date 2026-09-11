"""Entraîne simplement le modèle de danger incendie."""

import logging

from fourcasters_dbt.journal import configurer_logs
from fourcasters_dbt.ml_incendie import (
    charger_donnees,
    entrainer_modele,
)


def main() -> None:
    """Lance l'entraînement et affiche les résultats."""

    configurer_logs()
    print("🌲 Modèle de danger Météo-France")
    print()

    print("Chargement des données depuis BigQuery...")

    donnees = charger_donnees()

    print(f"✅ {len(donnees):,} lignes chargées")
    print()

    print("Entraînement du modèle...")

    _, resultats = entrainer_modele(donnees)

    print()
    print(f"Train : {resultats['nb_train']:,} lignes")
    print(f"Test  : {resultats['nb_test']:,} lignes")
    print(f"Dernier jour d'apprentissage : {resultats['fin_train']}")
    print(f"Premier jour de test : {resultats['debut_test']}")
    print(f"Lignes écartées entre les périodes : {resultats['nb_ecartes']}")

    print()
    print(f"🎯 Accuracy : {resultats['accuracy']:.2%}")

    print()
    print(f"Référence (classe majoritaire) : {resultats['accuracy_reference']:.2%}")
    print(f"F1 macro : {resultats['f1_macro']:.3f}")
    print("📊 Rapport de classification")
    print(resultats["rapport"])

    print("Matrice de confusion (lignes : réel, colonnes : prédit, niveaux 1 à 4)")
    print(resultats["matrice_confusion"])
    print("Variables les plus importantes")
    print(resultats["importance"].head(10).to_string())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.getLogger(__name__).exception("❌ Entraînement interrompu")
        raise SystemExit(1)
