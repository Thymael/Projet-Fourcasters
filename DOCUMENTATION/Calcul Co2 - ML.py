# Outil ponctuel pour mesurer l'impact de l'entraînement ML.
# À installer si besoin : uv add --group analyse codecarbon

from codecarbon import EmissionsTracker

from fourcasters_dbt.ml_incendie import charger_donnees, entrainer_modele


print("Chargement des données...")
donnees = charger_donnees()

tracker = EmissionsTracker(project_name="fourcasters_ml")
tracker.start()

print("Entraînement du modèle...")
_, resultats = entrainer_modele(donnees)

emissions = tracker.stop()

print()
print(f"Accuracy : {resultats['accuracy']:.2%}")
print(f"F1 macro : {resultats['f1_macro']:.3f}")
print(f"Ce traitement a émis environ {emissions:.6f} kg de CO2.")

# 11/09/2026 - Ce traitement a émis environ 0.000002 kg de CO2.