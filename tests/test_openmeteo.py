"""Contrôles d'une réponse API et d'un fichier de reprise, sans appel réseau."""

import pandas as pd
import pytest

from fourcasters_dbt.openmeteo import VARIABLES_METEO, creer_parquet, preparer_reponse_lot


def exemple_lot():
    communes = pd.DataFrame({"commune": ["Lille"], "code_insee": ["59350"]})
    daily = {"time": ["2026-09-01"], **{nom: [1.0] for nom in VARIABLES_METEO}}
    return communes, {"daily": daily}


def test_reponse_avec_une_autre_date_refusee():
    communes, reponse = exemple_lot()
    with pytest.raises(ValueError, match="ne correspond pas"):
        preparer_reponse_lot(reponse, communes, "2026-09-02")


def test_variable_absente_refusee():
    communes, reponse = exemple_lot()
    del reponse["daily"]["temperature_2m_mean"]
    with pytest.raises(ValueError, match="Colonnes météo absentes"):
        preparer_reponse_lot(reponse, communes, "2026-09-01")


def test_reponse_partielle_refusee():
    communes, _ = exemple_lot()
    with pytest.raises(ValueError):
        preparer_reponse_lot([], communes, "2026-09-01")


def test_reprise_csv_conserve_les_codes_et_les_cles(tmp_path):
    communes, reponse = exemple_lot()
    communes["code_insee"] = "01034"
    lot = preparer_reponse_lot(reponse, communes, "2026-09-01")
    csv, parquet = tmp_path / "meteo.csv", tmp_path / "meteo.parquet"
    pd.concat([lot, lot]).to_csv(csv, index=False)
    resultat = creer_parquet(csv, parquet, communes, "2026-09-01")
    assert resultat["code_insee"].tolist() == ["01034"]
    assert resultat["row_hash"].tolist() == lot["row_hash"].tolist()
    assert len(pd.read_parquet(parquet)) == 1


def test_csv_avec_un_autre_point_refuse(tmp_path):
    communes, reponse = exemple_lot()
    lot = preparer_reponse_lot(reponse, communes, "2026-09-01")
    lot.to_csv(tmp_path / "meteo.csv", index=False)
    communes["code_insee"] = "59009"
    with pytest.raises(ValueError, match="exactement les communes"):
        creer_parquet(tmp_path / "meteo.csv", tmp_path / "meteo.parquet", communes, "2026-09-01")
    assert not (tmp_path / "meteo.parquet").exists()
