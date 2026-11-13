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
            self.assertIn("Bonjour, je suis TerraMind", envoyer.call_args.args[1])
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

    corps, sources = texte_fiche("bacterial_wilt", "tomato")
    t = corps + sources
    for titre in ("1. Ce que c'est", "2. Pourquoi c'est arrivé", "3. Que faire maintenant", "4. Pour que ça ne revienne pas"):
        assert titre in t
    assert "Sources" in t
    assert texte_fiche("healthy", "tomato") is None


def test_pas_d_emoji_et_html_valide():
    import re
    from engine.app.routes import telegram as tg

    textes = [tg.ACCUEIL, tg.CONSEILS_PHOTO, tg.DEMANDE_POSITION, tg.B_POSITION, tg.B_PHOTO, tg.B_PLAN,
              tg.B_ALERTES, tg.B_AIDE, "".join(tg.texte_fiche("fusarium", "onion"))]
    emoji = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for t in textes:
        assert not emoji.search(t), t[:60]
        assert t.count("<b>") == t.count("</b>") and t.count("<i>") == t.count("</i>")


def test_date_inconnue():
    from engine.app.routes import telegram as tg

    tg.ETATS[8] = {"culture": "tomato", "attend_date": True}
    with mock.patch.object(tg, "envoyer"):
        tg.traiter({"message": {"chat": {"id": 8}, "text": "je ne sais pas"}})
    assert tg.ETATS[8]["repiquage"] is None and not tg.ETATS[8]["attend_date"]


def test_long_message_coupe():
    from engine.app.routes import telegram as tg

    morceaux = tg._morceaux("\n\n".join(["x" * 1500] * 4))
    assert len(morceaux) > 1 and all(len(m) <= tg.LIMITE for m in morceaux)
