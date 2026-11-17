"""Tests de l'écoute des notes vocales (Octopus et Gemini remplacés : aucun appel réel ni dépense)."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.app import config  # noqa: E402
from engine.app.modules import ecoute  # noqa: E402
from engine.app.routes import telegram  # noqa: E402


class _Reponse:
    def __init__(self, d):
        self.d = d

    def read(self):
        return json.dumps(self.d).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def octopus(monkeypatch):
    monkeypatch.setattr(config, "OCTOPUS_API_KEY", "jeton-test")
    monkeypatch.setattr(config, "OCTOPUS_PROJECT_ID", "proj-test")
    monkeypatch.setattr(config, "OCTOPUS_MINUTES_PAR_JOUR", 1.0)
    monkeypatch.setattr(ecoute, "COMPTEUR", ecoute._Compteur())


def test_desactive_sans_jeton(monkeypatch):
    monkeypatch.setattr(config, "OCTOPUS_API_KEY", "")
    with pytest.raises(ecoute.EcouteIndisponible):
        ecoute.transcrire(b"x", "audio/ogg", 5)


def test_note_trop_longue_refusee_sans_appel(octopus):
    with mock.patch("urllib.request.urlopen") as appel, pytest.raises(ecoute.NoteTropLongue):
        ecoute.transcrire(b"x", "audio/ogg", 90)
    appel.assert_not_called()


def test_transcription_et_plafond_du_jour(octopus):
    with mock.patch(
        "urllib.request.urlopen", return_value=_Reponse({"text": " naka ", "duration_seconds": 40})
    ) as appel:
        assert ecoute.transcrire(b"x", "audio/ogg", 40) == "naka"
        req = appel.call_args.args[0]
        assert "project_id=proj-test" in req.full_url and "language=wo" in req.full_url
        assert req.get_header("Authorization") == "Bearer jeton-test"
        # 40 s déjà utilisées sur 60 : une note de 30 s dépasse le plafond, aucun appel
        with pytest.raises(ecoute.EcouteIndisponible):
            ecoute.transcrire(b"x", "audio/ogg", 30)
        assert appel.call_count == 1


def test_traduction_incomprise():
    with mock.patch("engine.app.modules.rag.reponse.gemini", return_value="INCOMPRIS"):
        assert ecoute.traduire("bla") is None
    with mock.patch(
        "engine.app.modules.rag.reponse.gemini", return_value="« Comment soigner le mildiou ? »"
    ):
        assert ecoute.traduire("naka") == "Comment soigner le mildiou ?"


def test_bot_note_vocale_comprise():
    telegram.ETATS.clear()
    telegram.ETATS[5] = {"langue": "fr"}
    with (
        mock.patch.object(ecoute, "disponible", return_value=True),
        mock.patch.object(telegram, "_telecharger", return_value=b"ogg"),
        mock.patch.object(
            ecoute,
            "comprendre",
            return_value={"wolof": "naka", "francais": "Comment éviter le mildiou ?"},
        ),
        mock.patch.object(telegram, "_question") as question,
        mock.patch.object(telegram, "envoyer") as envoyer,
    ):
        telegram.traiter(
            {
                "message": {
                    "chat": {"id": 5},
                    "voice": {"file_id": "f", "duration": 4, "mime_type": "audio/ogg"},
                }
            }
        )
    assert "Comment éviter le mildiou ?" in envoyer.call_args.args[1]
    question.assert_called_once_with(5, "Comment éviter le mildiou ?")


def test_bot_note_vocale_sans_octopus_ou_trop_longue():
    telegram.ETATS.clear()
    telegram.ETATS[5] = {"langue": "fr"}
    with (
        mock.patch.object(ecoute, "disponible", return_value=False),
        mock.patch.object(telegram, "envoyer") as envoyer,
    ):
        telegram.traiter({"message": {"chat": {"id": 5}, "voice": {"file_id": "f", "duration": 4}}})
    assert "pour le moment" in envoyer.call_args.args[1]
    with (
        mock.patch.object(ecoute, "disponible", return_value=True),
        mock.patch.object(telegram, "envoyer") as envoyer,
        mock.patch.object(telegram, "_telecharger") as telecharger,
    ):
        telegram.traiter(
            {"message": {"chat": {"id": 5}, "voice": {"file_id": "f", "duration": 120}}}
        )
    assert "trop longue" in envoyer.call_args.args[1]
    telecharger.assert_not_called()
