"""Tests du bot Telegram, sans appel réel à Telegram (envoi remplacé)."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient  # noqa: E402

from engine.app import config  # noqa: E402
from engine.app.main import app  # noqa: E402
from engine.app.routes import telegram  # noqa: E402

START = {"update_id": 1, "message": {"chat": {"id": 42}, "text": "/start"}}


class Telegram(unittest.TestCase):
    def setUp(self):
        self.c = TestClient(app)
        telegram.ETATS.clear()

    def test_non_configure(self):
        with mock.patch.object(config, "TELEGRAM_BOT_TOKEN", ""), mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", ""):
            self.assertEqual(self.c.post("/webhook/telegram", json=START).status_code, 503)

    def test_secret_invalide(self):
        with mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "t"), mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", "s"):
            r = self.c.post("/webhook/telegram", json=START, headers={"X-Telegram-Bot-Api-Secret-Token": "faux"})
            self.assertEqual(r.status_code, 403)

    def test_start_puis_alertes_sans_position(self):
        with mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "t"), mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", "s"), \
                mock.patch.object(telegram, "envoyer") as envoyer:
            h = {"X-Telegram-Bot-Api-Secret-Token": "s"}
            self.assertEqual(self.c.post("/webhook/telegram", json=START, headers=h).status_code, 200)
            self.assertIn("Bienvenue", envoyer.call_args.args[1])
            self.c.post("/webhook/telegram", headers=h,
                        json={"update_id": 2, "message": {"chat": {"id": 42}, "text": telegram.B_ALERTES}})
            self.assertIn("position", envoyer.call_args.args[1])

    def test_date_de_repiquage(self):
        telegram.ETATS[7] = {"culture": "tomato", "attend_date": True}
        with mock.patch.object(telegram, "envoyer"):
            telegram.traiter({"message": {"chat": {"id": 7}, "text": "15/10"}})
        self.assertEqual(telegram.ETATS[7]["repiquage"].month, 10)
        self.assertFalse(telegram.ETATS[7]["attend_date"])


if __name__ == "__main__":
    unittest.main()


def test_fiche_telegram_en_4_parties():
    from engine.app.routes.telegram import texte_fiche

    t = texte_fiche("bacterial_wilt", "tomato")
    for titre in ("1. Ce que c'est", "2. Pourquoi c'est arrivé", "3. Que faire maintenant", "4. Pour que ça ne revienne pas"):
        assert titre in t
    assert "Sources" in t
    assert texte_fiche("healthy", "tomato") is None
