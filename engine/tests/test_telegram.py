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
            self.assertIn("En quelle langue", envoyer.call_args.args[1])
            with mock.patch.object(telegram, "_appel_silencieux"):
                self.c.post("/webhook/telegram", headers=h, json={"update_id": 3, "callback_query": {
                    "id": "q", "data": "langue:fr", "message": {"chat": {"id": 42}}}})
            self.assertEqual(telegram.ETATS[42]["langue"], "fr")
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


def test_voix_wolof_seulement_en_wolof(tmp_path=None):
    import tempfile
    from engine.app.routes import telegram as tg

    with tempfile.TemporaryDirectory() as d:
        Path(d, "accueil.mp3").write_bytes(b"ID3")
        with mock.patch.object(tg, "AUDIO_WO", Path(d)), \
                mock.patch.object(tg, "_envoyer_fichier", return_value={"result": {"voice": {"file_id": "F"}}}) as f, \
                mock.patch.object(tg, "_appel") as appel:
            tg.VOIX_DEJA_ENVOYEES.clear()
            tg.ETATS[9] = {"langue": "fr"}
            tg.dire(9, "accueil")
            assert not f.called
            tg.ETATS[9]["langue"] = "wo"
            tg.dire(9, "accueil")          # 1re fois : le fichier est envoyé
            tg.dire(9, "accueil")          # ensuite : on réutilise l'identifiant Telegram
            tg.dire(9, "audio_absent")     # pas de fichier : rien, sans erreur
            assert f.call_count == 1 and appel.call_args.kwargs["voice"] == "F"


def test_toutes_les_cles_du_bot_sont_au_catalogue():
    import csv
    import re
    from engine.app.routes import telegram as tg
    from engine.app.routes.v1 import FICHES_ETIQUETTES
    from engine.app.modules.planification.cultures import CULTURES

    racine = Path(__file__).resolve().parents[2]
    catalogue = {r["cle"] for r in csv.DictReader(open(racine / "content/voix/messages_wolof.csv", encoding="utf-8"))}
    source = (racine / "engine/app/routes/telegram.py").read_text(encoding="utf-8")
    fixes = set(re.findall(r'dire\(chat, "([a-z_]+)"', source))
    attendues = fixes | {f"fiche_{f}" for f in FICHES_ETIQUETTES.values()} | \
        {f"culture_{k}_{a}" for k in CULTURES for a in ("conseillee", "possible")} | \
        {f"alerte_{r}" for r in ("late_blight", "alternaria", "tuta_absoluta", "plutella_xylostella")}
    assert attendues <= catalogue, sorted(attendues - catalogue)
