"""Tests simples du modèle incendie."""

import pandas as pd
import pytest

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from fourcasters_dbt.ml_incendie import (
    ANNEE_TEST,
    ANNEES_APPRENTISSAGE,
    COLONNES_MODELE,
    DATE_FIN_TEST,
    VERSION_FEATURES,
    creer_modele,
    entrainer_modele,
    preparer_donnees,
    preparer_predictions_derniere_meteo,
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

    assert isinstance(modele, Pipeline)
    foret = modele.named_steps["modele"]
    assert isinstance(foret, RandomForestClassifier)
    assert foret.random_state == 42


def test_preparer_donnees():
    donnees = creer_donnees_test()

    x, y = preparer_donnees(donnees)

    assert list(x.columns) == COLONNES_MODELE
    assert len(x) == 2
    assert y.tolist() == [1, 2]


def test_ligne_incomplete_supprimee():
    donnees = creer_donnees_test()
    donnees.loc[1, "humidite_moyenne"] = None

    x, y = preparer_donnees(donnees)

    assert len(x) == 1
    assert len(y) == 1


def test_colonne_manquante():
    donnees = creer_donnees_test().drop(
        columns=["temperature_moyenne"]
    )

    with pytest.raises(ValueError):
        preparer_donnees(donnees)


def test_split_2024_2025_train_et_2026_test():
    dates = pd.Series(
        pd.to_datetime(
            [
                "2024-06-01",
                "2024-12-31",
                "2025-01-01",
                "2025-12-31",
                "2026-01-01",
                "2026-09-01",
            ]
        )
    )

    train, test = separer_dates(dates)

    assert dates[train].dt.year.isin(ANNEES_APPRENTISSAGE).all()
    assert dates[test].dt.year.eq(ANNEE_TEST).all()
    assert train.sum() == 4
    assert test.sum() == 2
    assert not (train & test).any()


def test_split_2026_sarrete_au_2_octobre():
    dates = pd.Series(
        pd.to_datetime(
            [
                "2024-06-01",
                "2026-10-01",
                "2026-10-02",
                "2026-10-03",
            ]
        )
    )

    train, test = separer_dates(dates)

    assert train.sum() == 1
    assert test.sum() == 2
    assert dates[test].max().normalize() == DATE_FIN_TEST
    assert not test.iloc[3]


def test_split_ignore_les_annees_hors_periode():
    dates = pd.Series(
        pd.to_datetime(
            [
                "2023-12-31",
                "2024-01-01",
                "2025-01-01",
                "2026-01-01",
                "2027-01-01",
            ]
        )
    )

    train, test = separer_dates(dates)
    hors_periode = ~(train | test)

    assert hors_periode.sum() == 2


@pytest.mark.parametrize("cible", [0, 5, 2.5])
def test_cible_hors_des_quatre_classes_refusee(cible):
    donnees = creer_donnees_test()
    donnees["cible_niveau_danger"] = [cible, 2]

    with pytest.raises(ValueError, match="entier de 1 à 4"):
        preparer_donnees(donnees)


def test_entrainement_2024_2025_et_test_2026():
    dates = []
    for annee in [2024, 2025, 2026]:
        dates.extend(
            pd.date_range(
                f"{annee}-06-01",
                periods=4,
                freq="D",
            ).repeat(4)
        )

    donnees = pd.DataFrame(
        {
            colonne: [1.0] * len(dates)
            for colonne in COLONNES_MODELE
        }
    )
    donnees["date_prevision"] = pd.to_datetime(dates)
    donnees["date_publication"] = (
        donnees["date_prevision"] - pd.Timedelta(days=1)
    )
    donnees["cible_niveau_danger"] = [1, 2, 3, 4] * 12

    modele, resultats = entrainer_modele(donnees)

    assert modele.classes_.tolist() == [1, 2, 3, 4]
    assert resultats["nb_train"] == 32
    assert resultats["nb_test"] == 16
    assert resultats["nb_hors_periode"] == 0
    assert resultats["debut_train"].year == 2024
    assert resultats["fin_train"].year == 2025
    assert resultats["debut_test"].year == 2026
    assert resultats["fin_test"].year == 2026
    assert resultats["accuracy_reference"] == 0.25
    assert resultats["f1_macro_reference"] == pytest.approx(0.1)
    assert resultats["date_fin_test"] == DATE_FIN_TEST.date()
    assert resultats["matrice_confusion"].shape == (4, 4)
    assert resultats["matrice_confusion"].sum() == 16
    assert resultats["fenetre_meteo"] == "J-6 à J"
    assert modele.fourcasters_feature_version == VERSION_FEATURES


def test_predictions_partent_du_dernier_jour_meteo():
    donnees = pd.DataFrame(
        {
            "meteo_date": pd.to_datetime(["2026-10-01", "2026-10-01"]),
            "numero_departement": ["13", "83"],
            "departement": ["Bouches-du-Rhône", "Var"],
            "region": ["Provence-Alpes-Côte d'Azur"] * 2,
            **{
                colonne: [1.0, 2.0]
                for colonne in COLONNES_MODELE
                if colonne != "horizon_jours"
            },
        }
    )

    contexte, x = preparer_predictions_derniere_meteo(donnees)

    assert len(contexte) == 4
    assert x["horizon_jours"].tolist() == [1.0, 1.0, 2.0, 2.0]
    assert contexte.loc[contexte["echeance"] == "J1", "date_prevision"].dt.date.unique().tolist() == [
        pd.Timestamp("2026-10-02").date()
    ]
    assert contexte.loc[contexte["echeance"] == "J2", "date_prevision"].dt.date.unique().tolist() == [
        pd.Timestamp("2026-10-03").date()
    ]


def test_predictions_refusent_plusieurs_dates_meteo():
    donnees = pd.DataFrame(
        {
            "meteo_date": pd.to_datetime(["2026-10-01", "2026-10-02"]),
            "numero_departement": ["13", "83"],
            "departement": ["Bouches-du-Rhône", "Var"],
            "region": ["Provence-Alpes-Côte d'Azur"] * 2,
            **{
                colonne: [1.0, 2.0]
                for colonne in COLONNES_MODELE
                if colonne != "horizon_jours"
            },
        }
    )

    with pytest.raises(ValueError, match="Une seule date météo"):
        preparer_predictions_derniere_meteo(donnees)
