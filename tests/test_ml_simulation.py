import pandas as pd

from fourcasters_dbt.ml_simulation import (
    COLONNES_MODELE_SIMULATION,
    creer_entrees_simulation,
    preparer_donnees_simulation,
    separer_dates_simulation,
)


def test_creer_entrees_simulation():
    entrees = creer_entrees_simulation(
        latitude=50.63,
        longitude=3.06,
        temperature_moyenne=25.0,
        temperature_maximale=31.0,
        humidite_moyenne=45.0,
        precipitations=0.0,
        rafale_vent_maximale=35.0,
        deficit_pression_vapeur_maximal=2.1,
    )

    assert list(entrees.columns) == COLONNES_MODELE_SIMULATION
    assert entrees["horizon_jours"].tolist() == [0, 1, 2]
    assert len(entrees) == 3


def test_preparer_donnees_simulation():
    donnees = pd.DataFrame(
        {
            "horizon_jours": [0, 1, 2],
            "latitude": [50.63, 50.63, 50.63],
            "longitude": [3.06, 3.06, 3.06],
            "temperature_moyenne": [25, 25, 25],
            "temperature_maximale": [31, 31, 31],
            "humidite_moyenne": [45, 45, 45],
            "precipitations": [0, 0, 0],
            "rafale_vent_maximale": [35, 35, 35],
            "deficit_pression_vapeur_maximal": [2.1, 2.1, 2.1],
            "cible_niveau_danger": [1, 2, 3],
        }
    )

    x, y = preparer_donnees_simulation(donnees)

    assert list(x.columns) == COLONNES_MODELE_SIMULATION
    assert y.tolist() == [1, 2, 3]


def test_separer_dates_simulation():
    dates = pd.Series(pd.date_range("2026-06-01", periods=20))

    train, test = separer_dates_simulation(dates)

    assert train.any()
    assert test.any()
    assert not (train & test).any()
