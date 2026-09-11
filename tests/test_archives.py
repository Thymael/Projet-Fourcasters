"""Les archives et l'API doivent produire les mêmes clés."""

import pandas as pd
import pytest

from fourcasters_dbt.archives_meteofrance import preparer_archives
from fourcasters_dbt.incendie import CODES_DEPARTEMENTS, preparer_donnees


def exemple_publication():
    return [
        {"reference_time": "2025-07-01T06:00:00Z", "dep_code": code,
         "dep_nom": f"Département {code}", "niveau_j1": 2, "niveau_j2": 3}
        for code in sorted(CODES_DEPARTEMENTS)
    ]


def test_api_et_archives_produisent_les_memes_cles():
    api = exemple_publication()
    archives = pd.DataFrame(api).rename(columns={"dep_nom": "nom_dep"})
    archives["annee_archive"] = 2025
    assert preparer_archives(archives)["row_hash"].tolist() == preparer_donnees(api)["row_hash"].tolist()


@pytest.mark.parametrize("champ,valeur", [
    ("reference_time", None), ("dep_nom", " "), ("dep_code", "99"), ("niveau_j1", 2.5),
])
def test_publication_invalide_refusee(champ, valeur):
    api = exemple_publication()
    api[0][champ] = valeur
    with pytest.raises((ValueError, TypeError)):
        preparer_donnees(api)


def test_departement_duplique_refuse():
    api = exemple_publication()
    api[-1] = api[0].copy()
    with pytest.raises(ValueError, match="plusieurs fois"):
        preparer_donnees(api)


def test_archive_dune_autre_annee_refusee():
    archives = pd.DataFrame(exemple_publication()).rename(columns={"dep_nom": "nom_dep"})
    archives["annee_archive"] = 2024
    with pytest.raises(ValueError, match="bonne archive annuelle"):
        preparer_archives(archives)
