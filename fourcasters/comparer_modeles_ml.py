from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, f1_score

from fourcasters_dbt.ml_incendie import (
    charger_donnees,
    preparer_donnees,
    separer_dates,
)

import pandas as pd


donnees = charger_donnees().reset_index(drop=True)

x, y = preparer_donnees(donnees)

dates = pd.to_datetime(donnees.loc[x.index, "date_publication"])
train, test = separer_dates(dates)

x_train = x.loc[train]
x_test = x.loc[test]

y_train = y.loc[train]
y_test = y.loc[test]


modeles = {
    "Classe majoritaire": DummyClassifier(strategy="most_frequent"),

    "Regression logistique": make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        ),
    ),

    "Arbre de decision": DecisionTreeClassifier(
        max_depth=8,
        min_samples_leaf=20,
        class_weight="balanced",
        random_state=42,
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
}


print()
print("COMPARAISON DES MODELES")
print("=" * 60)

for nom, modele in modeles.items():

    modele.fit(x_train, y_train)

    predictions = modele.predict(x_test)

    accuracy = accuracy_score(y_test, predictions)

    f1 = f1_score(
        y_test,
        predictions,
        labels=[1, 2, 3, 4],
        average="macro",
        zero_division=0,
    )

    print(
        f"{nom:<25} "
        f"Accuracy : {accuracy:.2%} | "
        f"F1 macro : {f1:.3f}"
    )


"""
COMPARAISON DES MODELES
============================================================
Classe majoritaire        Accuracy : 32.35% | F1 macro : 0.122
Regression logistique     Accuracy : 29.06% | F1 macro : 0.253
Arbre de decision         Accuracy : 37.46% | F1 macro : 0.275
Random Forest             Accuracy : 52.59% | F1 macro : 0.311
"""