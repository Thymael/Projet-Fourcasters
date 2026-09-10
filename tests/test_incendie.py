"""Tests simples de la collecte Météo-France."""

import pandas as pd
import pytest

from fourcasters_dbt.incendie import (
    convertir_niveaux_danger,
    normaliser_code_departement,
    preparer_donnees,
)


def test_normaliser_code_departement():
    """Les codes doivent toujours avoir le bon format."""

    assert normaliser_code_departement("1") == "01"
    assert normaliser_code_departement("59") == "59"
    assert normaliser_code_departement("2A") == "2A"
    assert normaliser_code_departement("2b") == "2B"


def test_niveau_danger_valide():
    """Les niveaux autorisés vont de 1 à 4."""

    donnees = pd.DataFrame(
        {
            "niveau_j1": [1, 2, 3, 4],
            "niveau_j2": [4, 3, 2, 1],
        }
    )

    convertir_niveaux_danger(donnees)

    assert donnees["niveau_j1"].between(1, 4).all()
    assert donnees["niveau_j2"].between(1, 4).all()


def test_niveau_danger_invalide():
    """Un niveau hors de 1 à 4 doit arrêter le traitement."""

    donnees = pd.DataFrame(
        {
            "niveau_j1": [1, 5],
            "niveau_j2": [1, 2],
        }
    )

    with pytest.raises(ValueError):
        convertir_niveaux_danger(donnees)


def test_nombre_departements_incorrect():
    """Une publication incomplète ne doit pas être chargée."""

    donnees = [
        {
            "reference_time": "2026-09-10T06:00:00Z",
            "dep_code": "59",
            "dep_nom": "Nord",
            "niveau_j1": 2,
            "niveau_j2": 3,
        }
    ]

    with pytest.raises(ValueError):
        preparer_donnees(donnees)
