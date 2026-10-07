"""Contrôles de la collecte Open-Meteo sans appel réseau."""

import pandas as pd
import pytest

from fourcasters_dbt.openmeteo import (
    VARIABLES_METEO,
    creer_parquet,
    preparer_reponse_lot,
    recuperer_lot,
)


def exemple_lot():
    """Crée une réponse Open-Meteo fictive pour une commune."""

    communes = pd.DataFrame(
        {
            "commune": ["Lille"],
            "code_insee": ["59350"],
        }
    )

    daily = {
        "time": ["2026-09-01"],
        **{
            nom: [1.0]
            for nom in VARIABLES_METEO
        },
    }

    return communes, {"daily": daily}


def test_reponse_avec_une_autre_date_refusee():
    communes, reponse = exemple_lot()

    with pytest.raises(
        ValueError,
        match="ne correspond pas",
    ):
        preparer_reponse_lot(
            reponse,
            communes,
            "2026-09-02",
        )


def test_variable_absente_refusee():
    communes, reponse = exemple_lot()

    del reponse["daily"]["temperature_2m_mean"]

    with pytest.raises(
        ValueError,
        match="Colonnes météo absentes",
    ):
        preparer_reponse_lot(
            reponse,
            communes,
            "2026-09-01",
        )


def test_reponse_partielle_refusee():
    communes, _ = exemple_lot()

    with pytest.raises(ValueError):
        preparer_reponse_lot(
            [],
            communes,
            "2026-09-01",
        )


def test_variable_ml_nulle_refusee(tmp_path):
    communes, reponse = exemple_lot()
    reponse["daily"]["temperature_2m_mean"] = [None]
    lot = preparer_reponse_lot(reponse, communes, "2026-09-01")

    with pytest.raises(
        ValueError,
        match="nécessaire au ML",
    ):
        creer_parquet(
            lot,
            tmp_path / "meteo.parquet",
            communes,
            "2026-09-01",
        )


def test_repli_era5_si_seamless_incomplet(monkeypatch):
    communes, reponse_complete = exemple_lot()
    communes["latitude"] = 50.63
    communes["longitude"] = 3.06
    reponse_incomplete = {
        "daily": {
            **reponse_complete["daily"],
            "precipitation_sum": [None],
        }
    }
    appels = []

    class Reponse:
        def __init__(self, contenu):
            self.contenu = contenu

        def json(self):
            return self.contenu

    def faux_appel(_url, params, timeout):
        appels.append((params["models"], timeout))
        contenu = (
            reponse_incomplete
            if params["models"] == "era5_seamless"
            else reponse_complete
        )
        return Reponse(contenu)

    monkeypatch.setattr(
        "fourcasters_dbt.openmeteo.recuperer_reponse",
        faux_appel,
    )

    resultat = recuperer_lot(communes, "2026-09-01")

    assert resultat["precipitation_sum"].notna().all()
    assert [modele for modele, _ in appels] == [
        "era5_seamless",
        "era5",
    ]


def test_parquet_conserve_code_et_hash(tmp_path):
    communes, reponse = exemple_lot()

    communes["code_insee"] = "01034"

    lot = preparer_reponse_lot(
        reponse,
        communes,
        "2026-09-01",
    )

    fichier_parquet = tmp_path / "meteo.parquet"

    resultat = creer_parquet(
        lot,
        fichier_parquet,
        communes,
        "2026-09-01",
    )

    assert resultat["code_insee"].tolist() == [
        "01034"
    ]

    assert resultat["row_hash"].tolist() == (
        lot["row_hash"].tolist()
    )

    assert len(
        pd.read_parquet(fichier_parquet)
    ) == 1


def test_autre_point_refuse(tmp_path):
    communes, reponse = exemple_lot()

    lot = preparer_reponse_lot(
        reponse,
        communes,
        "2026-09-01",
    )

    communes["code_insee"] = "59009"

    fichier_parquet = tmp_path / "meteo.parquet"

    with pytest.raises(
        ValueError,
        match="exactement les communes",
    ):
        creer_parquet(
            lot,
            fichier_parquet,
            communes,
            "2026-09-01",
        )

    assert not fichier_parquet.exists()


def test_commune_dupliquee_refusee(tmp_path):
    communes, reponse = exemple_lot()

    lot = preparer_reponse_lot(
        reponse,
        communes,
        "2026-09-01",
    )

    lot_duplique = pd.concat(
        [lot, lot],
        ignore_index=True,
    )

    fichier_parquet = tmp_path / "meteo.parquet"

    with pytest.raises(
        ValueError,
        match="Une seule ligne par commune",
    ):
        creer_parquet(
            lot_duplique,
            fichier_parquet,
            communes,
            "2026-09-01",
        )

    assert not fichier_parquet.exists()
