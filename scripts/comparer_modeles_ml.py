import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from fourcasters_dbt.ml_incendie import (
    charger_donnees,
    creer_modele,
    preparer_donnees,
    separer_dates,
)


def main() -> None:
    """Entraîne plusieurs modèles sur les mêmes données et compare les résultats."""

    print("Chargement des données...")
    donnees = charger_donnees().reset_index(drop=True)

    x, y = preparer_donnees(donnees)

    dates = pd.to_datetime(donnees.loc[x.index, "date_publication"])
    train, test = separer_dates(dates)

    x_train = x.loc[train]
    x_test = x.loc[test]

    y_train = y.loc[train]
    y_test = y.loc[test]

    modeles = {
        "Classe majoritaire": DummyClassifier(
            strategy="most_frequent",
        ),
        "Régression logistique": make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42,
            ),
        ),
        "Arbre de décision": DecisionTreeClassifier(
            max_depth=8,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=42,
        ),
        "Random Forest": creer_modele(),
    }

    print()
    print("COMPARAISON DES MODÈLES")
    print("=" * 65)

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


if __name__ == "__main__":
    main()