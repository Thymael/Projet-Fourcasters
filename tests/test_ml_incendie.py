"""Tests simples du modèle incendie."""

import pandas as pd
import pytest

from sklearn.ensemble import RandomForestClassifier

from fourcasters_dbt.ml_incendie import (
    COLONNES_MODELE,
    creer_modele,
    entrainer_modele,
    preparer_donnees,
    separer_dates,
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


def test_une_journee_ne_chevauche_pas_apprentissage_et_test():
    dates = pd.Series(pd.date_range("2025-07-01", periods=20).repeat(192))
    train, test = separer_dates(dates)
    assert not (train & test).any()
    assert dates[train].max() + pd.Timedelta(days=2) < dates[test].min()
    assert set(dates[train]).isdisjoint(set(dates[test]))
    assert test.sum() == 4 * 192


@pytest.mark.parametrize("cible", [0, 5, 2.5])
def test_cible_hors_des_quatre_classes_refusee(cible):
    donnees = creer_donnees_test()
    donnees["cible_niveau_danger"] = [cible, 2]
    with pytest.raises(ValueError, match="entier de 1 à 4"):
        preparer_donnees(donnees)


def test_entrainement_complet_sur_donnees_fictives():
    donnees = pd.DataFrame({colonne: [1.0] * 80 for colonne in COLONNES_MODELE})
    donnees["date_publication"] = pd.date_range("2025-07-01", periods=20).repeat(4)
    donnees["cible_niveau_danger"] = [1, 2, 3, 4] * 20

    modele, resultats = entrainer_modele(donnees)

    assert modele.classes_.tolist() == [1, 2, 3, 4]
    assert (resultats["nb_train"], resultats["nb_test"], resultats["nb_ecartes"]) == (56, 16, 8)
    assert resultats["accuracy_reference"] == 0.25
    assert resultats["matrice_confusion"].shape == (4, 4)
    assert resultats["matrice_confusion"].sum() == 16
