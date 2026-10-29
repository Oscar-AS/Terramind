"""Tests de contrat de sécurité : règles que toute réponse du moteur doit respecter.

Sautés tant que les routes n'existent pas. À activer par Salam et Oscar à partir du 3 nov 2026 :
implémenter la fixture `client`, renseigner les requêtes TODO selon docs/api.md, retirer les skip.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

SKIP_REASON = "activer quand les routes existent"
UNCERTAIN_STATUS = "incertain"
UNSUPPORTED_CROP_MESSAGE = "culture non prise en charge"
SOURCED_DATA_KEYS = ("meteo", "climat", "sol")

# TODO (3 nov) : requêtes réelles, conformes au contrat figé dans docs/api.md.
TREATMENT_REQUEST: dict = {}
PLAN_REQUEST: dict = {}
ALERT_REQUEST: dict = {}
LOW_CONFIDENCE_DIAGNOSE_REQUEST: dict = {}
UNSUPPORTED_CROP_DIAGNOSE_REQUEST: dict = {}
SMOKE_REQUESTS: list[tuple[str, dict]] = []


@pytest.fixture
def client():
    # TODO (3 nov) : return fastapi.testclient.TestClient(app) une fois engine/app créé.
    raise NotImplementedError


def iter_dicts(value: object) -> Iterator[dict]:
    """Parcourt tous les objets JSON d'une réponse, à n'importe quelle profondeur."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def confidence_threshold() -> float:
    return float(os.environ["DIAGNOSTIC_CONFIDENCE_THRESHOLD"])


@pytest.mark.skip(reason=SKIP_REASON)
def test_treatment_dosage_requires_source(client):
    # Un dosage n'est donné que si sa source est renseignée.
    body = client.post("/chat", json=TREATMENT_REQUEST).json()
    for item in iter_dicts(body):
        if item.get("dosage"):
            assert str(item.get("source") or "").strip(), f"dosage sans source : {item}"


@pytest.mark.skip(reason=SKIP_REASON)
@pytest.mark.parametrize("path, request_body", [("/plan", PLAN_REQUEST), ("/alert", ALERT_REQUEST)])
def test_climate_and_soil_data_have_source_and_date(client, path, request_body):
    # Toute donnée climatique ou de sol indique sa source et sa date.
    body = client.post(path, json=request_body).json()
    for item in iter_dicts(body):
        for key in SOURCED_DATA_KEYS:
            if key in item:
                data = item[key]
                assert isinstance(data, dict), f"{key} doit être un objet avec source et date"
                assert data.get("source"), f"{key} sans source"
                assert data.get("date"), f"{key} sans date"


@pytest.mark.skip(reason=SKIP_REASON)
def test_low_confidence_is_uncertain_with_referral(client):
    # Sous le seuil de confiance, le diagnostic est « incertain » et renvoie vers un agent agricole.
    body = client.post("/diagnose", json=LOW_CONFIDENCE_DIAGNOSE_REQUEST).json()
    assert body["confiance"] < confidence_threshold()
    assert body["statut"] == UNCERTAIN_STATUS
    # TODO : nom définitif du champ de renvoi selon docs/api.md.
    assert body.get("renvoi_agent")


@pytest.mark.skip(reason=SKIP_REASON)
def test_unsupported_crop_is_rejected(client):
    # Une culture hors de la liste prise en charge reçoit « culture non prise en charge ».
    response = client.post("/diagnose", json=UNSUPPORTED_CROP_DIAGNOSE_REQUEST)
    assert UNSUPPORTED_CROP_MESSAGE in response.text.lower()


@pytest.mark.skip(reason=SKIP_REASON)
def test_no_mock_in_production(client, monkeypatch):
    # En production, aucune réponse n'est factice ("mock": true).
    monkeypatch.setenv("APP_ENV", "production")
    for path, request_body in SMOKE_REQUESTS:
        body = client.post(path, json=request_body).json()
        assert all(item.get("mock") is not True for item in iter_dicts(body)), path
