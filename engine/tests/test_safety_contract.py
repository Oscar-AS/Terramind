"""Tests de contrat de sécurité : règles que toute réponse du moteur doit respecter.

Les routes /plan, /alert et /diagnose sont actives et testées.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from engine.app.routes.agronomie import (
    traiter_requete_alert,
    traiter_requete_diagnose,
    traiter_requete_plan,
)

SKIP_REASON = "activer quand la route /chat existe"
UNCERTAIN_STATUS = "incertain"
UNSUPPORTED_CROP_MESSAGE = "culture non prise en charge"
SOURCED_DATA_KEYS = ("meteo", "climat", "sol")

TREATMENT_REQUEST: dict = {}
PLAN_REQUEST: dict = {
    "lat": 14.76,
    "lon": -17.21,
    "date": "2026-11-05",
    "eau_puits_salee": "non",
    "champ_en_bas_fond": "oui",
    "utilisateur": "sha256_test",
    "canal": "whatsapp",
    "langue": "fr",
}
ALERT_REQUEST: dict = {
    "lat": 15.09,
    "lon": -16.65,
    "culture": "tomato",
    "date_repiquage": "2026-12-01",
    "date": "2027-02-10",
    "utilisateur": "sha256_test",
    "canal": "whatsapp",
    "langue": "wo",
}
LOW_CONFIDENCE_DIAGNOSE_REQUEST: dict = {
    "culture_declaree": "tomato",
    "qualite_image": "floue",
    "utilisateur": "sha256_test",
    "canal": "whatsapp",
    "langue": "fr",
}
UNSUPPORTED_CROP_DIAGNOSE_REQUEST: dict = {
    "culture_declaree": "carrot",
    "qualite_image": "nette",
    "utilisateur": "sha256_test",
    "canal": "whatsapp",
    "langue": "fr",
}
SMOKE_REQUESTS: list[tuple[str, dict]] = [
    ("/plan", PLAN_REQUEST),
    ("/alert", ALERT_REQUEST),
    ("/diagnose", {"culture_declaree": "tomato", "qualite_image": "nette", "langue": "fr"}),
]


@dataclass
class _ReponseLocale:
    status_code: int
    payload: dict

    def json(self) -> dict:
        return self.payload

    @property
    def text(self) -> str:
        return json.dumps(self.payload, ensure_ascii=False)


class _ClientLocal:
    """Adaptateur léger appelant directement les gestionnaires quand FastAPI n'est pas installé."""

    def post(self, path: str, json: dict) -> _ReponseLocale:
        if path in ("/plan", "/v1/plan"):
            code, payload = traiter_requete_plan(json)
            return _ReponseLocale(code, payload)
        if path in ("/alert", "/v1/alert"):
            code, payload = traiter_requete_alert(json, autoriser_reseau=False)
            return _ReponseLocale(code, payload)
        if path in ("/diagnose", "/v1/diagnose"):
            code, payload = traiter_requete_diagnose(json)
            return _ReponseLocale(code, payload)
        raise NotImplementedError(f"Route non branchée : {path}")


@pytest.fixture
def client():
    try:
        from fastapi.testclient import TestClient

        from engine.app.main import app

        return TestClient(app)
    except ImportError:
        return _ClientLocal()


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
    return float(os.environ.get("DIAGNOSTIC_CONFIDENCE_THRESHOLD", "0.60"))


@pytest.mark.skip(reason=SKIP_REASON)
def test_treatment_dosage_requires_source(client):
    # Un dosage n'est donné que si sa source est renseignée.
    body = client.post("/chat", json=TREATMENT_REQUEST).json()
    for item in iter_dicts(body):
        if item.get("dosage"):
            assert str(item.get("source") or "").strip(), f"dosage sans source : {item}"


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


def test_low_confidence_is_uncertain_with_referral(client, monkeypatch):
    # Sous le seuil de confiance, le diagnostic est « incertain » et renvoie vers un agent agricole.
    monkeypatch.setenv("DIAGNOSTIC_CONFIDENCE_THRESHOLD", "0.60")
    body = client.post("/diagnose", json=LOW_CONFIDENCE_DIAGNOSE_REQUEST).json()
    assert body["confiance"] < confidence_threshold()
    assert body["statut"] == UNCERTAIN_STATUS
    assert body.get("renvoi_agent") is True


def test_unsupported_crop_is_rejected(client):
    # Une culture hors de la liste prise en charge reçoit « culture non prise en charge ».
    response = client.post("/diagnose", json=UNSUPPORTED_CROP_DIAGNOSE_REQUEST)
    assert UNSUPPORTED_CROP_MESSAGE in response.text.lower()


def test_no_mock_in_production(client, monkeypatch):
    # En production, aucune réponse n'est factice ("mock": true).
    monkeypatch.setenv("APP_ENV", "production")
    for path, request_body in SMOKE_REQUESTS:
        body = client.post(path, json=request_body).json()
        assert all(item.get("mock") is not True for item in iter_dicts(body)), path
