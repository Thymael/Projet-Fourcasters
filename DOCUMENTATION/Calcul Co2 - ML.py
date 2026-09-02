# à installer une fois : pip install codecarbon
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()
tracker.start()
# ... ici, le code qui consomme : entraînement d'un modèle, gros calcul ...
model.fit(X_train, y_train)
emissions = tracker.stop() # emissions en kg de CO2
print(f"Ce traitement a émis {emissions:.4f} kg de CO2")