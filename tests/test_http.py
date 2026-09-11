"""Les réessais attendent sur un quota et s'arrêtent sur une clé refusée."""

import pytest
import requests

from fourcasters_dbt import http


def test_quota_puis_succes(monkeypatch):
    appels, pauses = [], []

    def repondre(*args, **kwargs):
        appels.append(1)
        reponse = requests.Response()
        reponse.status_code = 429 if len(appels) == 1 else 200
        return reponse

    monkeypatch.setattr(http.requests, "get", repondre)
    monkeypatch.setattr(http.time, "sleep", pauses.append)
    assert http.recuperer_reponse("https://exemple.test").status_code == 200
    assert len(appels) == 2
    assert pauses == [60]


def test_cle_refusee_sans_reessai(monkeypatch):
    appels = []

    def repondre(*args, **kwargs):
        appels.append(1)
        reponse = requests.Response()
        reponse.status_code = 401
        return reponse

    monkeypatch.setattr(http.requests, "get", repondre)
    with pytest.raises(requests.HTTPError):
        http.recuperer_reponse("https://exemple.test")
    assert len(appels) == 1
