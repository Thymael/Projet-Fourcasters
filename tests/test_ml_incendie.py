"""Tests simples du modèle incendie."""

import pandas as pd
import pytest

from sklearn.ensemble import RandomForestClassifier

from fourcasters_dbt.ml_incendie import (
    COLONNES_MODELE,
    creer_modele,
    preparer_donnees,
)


def creer_donnees_test():
    """Crée deux lignes fictives complètes."""

    donnees = {
        colonne: [1.0, 2.0]
        for colonne in COLONNES_MODELE
    }

    donnees["cible_niveau_danger"] = [1, 2]

    return pd.DataFrame(donnees)


def test_creer_modele():
    modele = creer_modele()

    assert isinstance(
        modele,
        RandomForestClassifier,
    )

    assert modele.random_state == 42


def test_preparer_donnees():
    donnees = creer_donnees_test()

    x, y = preparer_donnees(donnees)

    assert list(x.columns) == COLONNES_MODELE
    assert len(x) == 2
    assert y.tolist() == [1, 2]


def test_ligne_incomplete_supprimee():
    donnees = creer_donnees_test()

    donnees.loc[
        1,
        "humidite_moyenne",
    ] = None

    x, y = preparer_donnees(donnees)

    assert len(x) == 1
    assert len(y) == 1


def test_colonne_manquante():
    donnees = creer_donnees_test()

    donnees = donnees.drop(
        columns=["temperature_moyenne"]
    )

    with pytest.raises(ValueError):
        preparer_donnees(donnees)