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
        with (
            mock.patch.object(config, "TELEGRAM_BOT_TOKEN", ""),
            mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", ""),
        ):
            self.assertEqual(self.c.post("/webhook/telegram", json=START).status_code, 503)

    def test_secret_invalide(self):
        with (
            mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "t"),
            mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", "s"),
        ):
            r = self.c.post(
                "/webhook/telegram", json=START, headers={"X-Telegram-Bot-Api-Secret-Token": "faux"}
            )
            self.assertEqual(r.status_code, 403)

    def test_start_puis_alertes_sans_position(self):
        with (
            mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "t"),
            mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", "s"),
            mock.patch.object(telegram, "envoyer") as envoyer,
        ):
            h = {"X-Telegram-Bot-Api-Secret-Token": "s"}
            self.assertEqual(
                self.c.post("/webhook/telegram", json=START, headers=h).status_code, 200
            )
            self.assertIn("En quelle langue", envoyer.call_args.args[1])
            with mock.patch.object(telegram, "_appel_silencieux"):
                self.c.post(
                    "/webhook/telegram",
                    headers=h,
                    json={
                        "update_id": 3,
                        "callback_query": {
                            "id": "q",
                            "data": "langue:fr",
                            "message": {"chat": {"id": 42}},
                        },
                    },
                )
            self.assertEqual(telegram.ETATS[42]["langue"], "fr")
            self.assertIn("Bonjour, je suis TerraMind", envoyer.call_args.args[1])
            self.c.post(
                "/webhook/telegram",
                headers=h,
                json={"update_id": 2, "message": {"chat": {"id": 42}, "text": telegram.B_ALERTES}},
            )
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
    for titre in (
        "1. Ce que c'est",
        "2. Pourquoi c'est arrivé",
        "3. Que faire maintenant",
        "4. Pour que ça ne revienne pas",
    ):
        assert titre in t
    assert "Sources" in t
    assert texte_fiche("healthy", "tomato") is None


def test_pas_d_emoji_et_html_valide():
    import re

    from engine.app.routes import telegram as tg

    textes = [
        tg.ACCUEIL,
        tg.CONSEILS_PHOTO,
        tg.DEMANDE_POSITION,
        tg.B_POSITION,
        tg.B_PHOTO,
        tg.B_PLAN,
        tg.B_ALERTES,
        tg.B_QUESTION,
        "".join(tg.texte_fiche("fusarium", "onion")),
    ]
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
        with (
            mock.patch.object(tg, "AUDIO_WO", Path(d)),
            mock.patch.object(
                tg, "_envoyer_fichier", return_value={"result": {"voice": {"file_id": "F"}}}
            ) as f,
            mock.patch.object(tg, "_appel") as appel,
        ):
            tg.VOIX_DEJA_ENVOYEES.clear()
            tg.ETATS[9] = {"langue": "fr"}
            tg.dire(9, "accueil")
            assert not f.called
            tg.ETATS[9]["langue"] = "wo"
            tg.dire(9, "accueil")  # 1re fois : le fichier est envoyé
            tg.dire(9, "accueil")  # ensuite : on réutilise l'identifiant Telegram
            tg.dire(9, "audio_absent")  # pas de fichier : rien, sans erreur
            assert f.call_count == 1 and appel.call_args.kwargs["voice"] == "F"


def test_toutes_les_cles_du_bot_sont_au_catalogue():
    import csv
    import re

    from engine.app.modules.planification.cultures import CULTURES
    from engine.app.routes.v1 import FICHES_ETIQUETTES

    racine = Path(__file__).resolve().parents[2]
    catalogue = {
        r["cle"]
        for r in csv.DictReader(open(racine / "content/voix/messages_wolof.csv", encoding="utf-8"))
    }
    source = (racine / "engine/app/routes/telegram.py").read_text(encoding="utf-8")
    fixes = set(re.findall(r'dire\(chat, "([a-z_]+)"', source))
    attendues = (
        fixes
        | {f"fiche_{f}" for f in FICHES_ETIQUETTES.values()}
        | {f"culture_{k}_{a}" for k in CULTURES for a in ("conseillee", "possible")}
        | {
            f"alerte_{r}"
            for r in ("late_blight", "alternaria", "tuta_absoluta", "plutella_xylostella")
        }
    )
    assert attendues <= catalogue, sorted(attendues - catalogue)


def test_culture_sans_regle_meteo_pas_de_faux_rien_a_signaler():
    telegram.ETATS.clear()
    telegram.ETATS[9] = {"langue": "fr", "lat": 14.7, "lon": -17.2, "culture": "onion"}
    vide = {
        "alertes": [],
        "meteo": {"source": "NASA POWER", "periode": ["2026-11-01", "2026-11-08"]},
    }
    with (
        mock.patch.object(telegram, "calculer", return_value=vide),
        mock.patch.object(telegram, "envoyer") as envoyer,
    ):
        telegram._alertes(9)
    texte = envoyer.call_args.args[1]
    assert "je ne surveille pas encore la météo" in texte
    assert "Bonne nouvelle" not in texte


def test_questions_eau_et_bas_fond_avant_le_plan():
    tg = telegram
    tg.ETATS.clear()
    tg.ETATS[11] = {"langue": "fr"}
    plan = ({"sol": {"sable_pct": 80, "ph": 6.5}, "cultures": []}, [])
    with (
        mock.patch.object(tg, "envoyer") as envoyer,
        mock.patch.object(tg, "_appel_silencieux"),
        mock.patch.object(tg, "planifier", return_value=plan) as planifier,
    ):
        tg.traiter(
            {
                "message": {
                    "chat": {"id": 11},
                    "location": {"latitude": 14.761, "longitude": -17.209},
                }
            }
        )
        assert "puits est-elle salée" in envoyer.call_args.args[1]
        planifier.assert_not_called()
        tg.traiter(
            {"callback_query": {"id": "q", "data": "eau:non", "message": {"chat": {"id": 11}}}}
        )
        assert "bas-fond" in envoyer.call_args.args[1]
        tg.traiter(
            {"callback_query": {"id": "q", "data": "basfond:oui", "message": {"chat": {"id": 11}}}}
        )
        assert planifier.call_args.args[3:] == ("non", "oui")
        assert "eau de ton puits est salée, évite" not in envoyer.call_args.args[1]


def test_photo_non_filtree_par_la_culture_surveillee():
    telegram.ETATS.clear()
    telegram.ETATS[12] = {"langue": "fr", "culture": "tomato"}
    with mock.patch.object(telegram, "_photo") as photo:
        telegram.traiter({"message": {"chat": {"id": 12}, "photo": [{"file_id": "f"}]}})
    assert photo.call_args.args[2] is None


def test_photo_tomate_demande_de_verifier_la_mineuse():
    from engine.app.modules.diagnostic import modele

    res = {
        "predictions": [
            {
                "culture": "tomato",
                "etiquette": "healthy",
                "categorie": "sain",
                "libelle": "Tomate saine",
                "confiance": 0.9,
            }
        ],
        "certain": True,
    }
    with (
        mock.patch.object(modele, "diagnostiquer", return_value=res),
        mock.patch.object(telegram, "_telecharger", return_value=b"x"),
        mock.patch.object(telegram, "dire"),
        mock.patch.object(telegram, "envoyer") as envoyer,
    ):
        telegram._photo(14, "f", None)
    dernier = envoyer.call_args.args[1]
    assert "À vérifier aussi" in dernier and "Tuta absoluta" in dernier


def test_reponse_libre_dite_en_wolof():
    telegram.ETATS.clear()
    telegram.ETATS[13] = {"langue": "wo"}
    r = {
        "statut": "ok",
        "texte": "Arrose au pied.",
        "sources": [],
        "mode": "gemini",
        "passages": [],
    }
    from engine.app.modules import parole

    with (
        mock.patch("engine.app.modules.rag.reponse.repondre", return_value=r),
        mock.patch.object(parole, "dire_en_wolof", return_value=b"mp3") as dire_wo,
        mock.patch.object(telegram, "_envoyer_fichier") as fichier,
        mock.patch.object(telegram, "envoyer"),
    ):
        telegram._question(13, "Comment éviter le mildiou ?")
    dire_wo.assert_called_once_with("Arrose au pied.")
    assert fichier.call_args.kwargs["octets"] == b"mp3"


def test_mode_wolof_boutons_numerotes():
    tg = telegram
    tg.ETATS.clear()
    tg.ETATS[14] = {"langue": "wo"}
    with mock.patch.object(tg, "_appel") as appel:
        tg.envoyer(14, "texte", reply_markup=tg.CLAVIER)
    clavier = appel.call_args.kwargs["reply_markup"]
    assert clavier is tg.CLAVIER_WO and clavier["keyboard"][1][0]["text"] == "2. " + tg.B_PHOTO
    # « 2. … » ou « 2 » tout court déclenchent la même action que le bouton texte
    for saisi in ("2. " + tg.B_PHOTO, "2"):
        with mock.patch.object(tg, "envoyer") as envoyer:
            tg.traiter({"message": {"chat": {"id": 14}, "text": saisi}})
        assert "une photo de ta plante" in envoyer.call_args.args[1]
    with mock.patch.object(tg, "envoyer") as envoyer:
        tg.traiter(
            {"message": {"chat": {"id": 14}, "location": {"latitude": 14.7, "longitude": -17.2}}}
        )
    boutons = envoyer.call_args.kwargs["reply_markup"]["inline_keyboard"][0]
    assert [b["text"][:2] for b in boutons] == ["1.", "2.", "3."]


def test_ordre_des_cultures_dit_par_la_voix():
    # la note vocale « choix_culture » énumère les cultures dans cet ordre
    from engine.app.modules.planification.cultures import CULTURES

    assert list(CULTURES) == [
        "tomato",
        "potato",
        "onion",
        "cabbage",
        "pepper",
        "carrot",
        "chili",
        "bitter_eggplant",
    ]


def test_bouton_position_test_donne_une_position_des_niayes():
    tg = telegram
    tg.ETATS.clear()
    tg.ETATS[13] = {"langue": "fr"}
    assert [{"text": tg.B_POSITION_TEST}] in tg.CLAVIER["keyboard"]
    with (
        mock.patch.object(tg, "envoyer") as envoyer,
        mock.patch.object(tg, "_appel_silencieux"),
        mock.patch.object(tg, "_plan") as plan,
    ):
        tg.traiter({"message": {"chat": {"id": 13}, "text": tg.B_POSITION_TEST}})
    assert (tg.ETATS[13]["lat"], tg.ETATS[13]["lon"]) == (14.76, -17.21)
    assert "Position test : Rufisque" in envoyer.call_args.args[1]
    plan.assert_called_once()


def test_periode_meteo_en_francais():
    assert telegram.periode_fr("2026-11-05", "2026-11-12") == "du 5 au 12 novembre"
    assert telegram.periode_fr("2026-10-28", "2026-11-04") == "du 28 octobre au 4 novembre"


def test_phrase_ph_negation():
    from engine.app.routes.telegram import phrase_ph

    assert phrase_ph(6.8) == "ton sol n'est ni acide ni basique"
    assert phrase_ph(6.1) == "ton sol est un peu acide"


def test_ranger_pages_fusionne():
    from engine.app.modules.rag.fiches import ranger_pages

    assert ranger_pages(["90-91", "91", "89", "88"]) == ["88-91"]
    assert ranger_pages(["88-90", "91", "140"]) == ["88-91", "140"]
    assert ranger_pages(["12", "30", "12"]) == ["12", "30"]


def test_date_future_refusee():
    import datetime as dt

    from engine.app.routes import telegram as tg

    demain = dt.date.today() + dt.timedelta(days=1)
    if demain.month != dt.date.today().month:
        return  # fin de mois : « demain » serait lu comme l'an dernier
    tg.ETATS[10] = {"culture": "tomato", "attend_date": True, "lat": 14.76, "lon": -17.21}
    with mock.patch.object(tg, "envoyer") as envoyer, mock.patch.object(tg, "_alertes") as alertes:
        tg.traiter({"message": {"chat": {"id": 10}, "text": f"{demain.day}/{demain.month}"}})
    assert "pas encore arrivée" in envoyer.call_args.args[1] and not alertes.called
    assert tg.ETATS[10]["attend_date"]


def test_changer_de_culture_et_date_plus_tard():
    from engine.app.routes import telegram as tg

    tg.ETATS[11] = {
        "langue": "fr",
        "culture": "tomato",
        "repiquage": None,
        "attend_date": False,
        "date_libre": True,
        "lat": 14.76,
        "lon": -17.21,
    }
    with mock.patch.object(tg, "envoyer"), mock.patch.object(tg, "_alertes") as alertes:
        tg.traiter(
            {"message": {"chat": {"id": 11}, "text": "15/10"}}
        )  # date donnée après « je ne sais pas »
        assert tg.ETATS[11]["repiquage"].month == 10 and alertes.called
    with mock.patch.object(tg, "envoyer") as envoyer, mock.patch.object(tg, "_appel_silencieux"):
        tg.traiter(
            {
                "callback_query": {
                    "id": "q",
                    "data": "changer_culture",
                    "message": {"chat": {"id": 11}},
                }
            }
        )
        assert "Quelle culture" in envoyer.call_args.args[1]
        tg.traiter(
            {
                "callback_query": {
                    "id": "q",
                    "data": "culture:onion",
                    "message": {"chat": {"id": 11}},
                }
            }
        )
    assert tg.ETATS[11]["culture"] == "onion" and "repiquage" not in tg.ETATS[11]


def test_etat_perdu_apres_veille():
    from engine.app.routes import telegram as tg

    tg.ETATS.pop(12, None)
    with mock.patch.object(tg, "envoyer") as envoyer, mock.patch.object(tg, "_appel_silencieux"):
        tg.traiter(
            {"callback_query": {"id": "q", "data": "eau:oui", "message": {"chat": {"id": 12}}}}
        )
    assert "connaître ton champ" in envoyer.call_args.args[1]


def test_erreur_imprevue_message_de_repli():
    from engine.app.routes import telegram as tg

    with (
        mock.patch.object(tg, "traiter", side_effect=TypeError("x")),
        mock.patch.object(tg, "_appel_silencieux") as appel,
    ):
        tg.traiter_sans_planter({"message": {"chat": {"id": 13}, "text": "bonjour"}})
    assert appel.call_args.kwargs["chat_id"] == 13


def test_secret_non_ascii_refuse():
    from fastapi.testclient import TestClient

    from engine.app.main import app

    with (
        mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "t"),
        mock.patch.object(config, "TELEGRAM_WEBHOOK_SECRET", "s"),
    ):
        r = TestClient(app).post(
            "/webhook/telegram",
            json=START,
            headers={"X-Telegram-Bot-Api-Secret-Token": b"\xe9t\xe9"},
        )
    assert r.status_code == 403


def test_date_inconnue_en_wolof():
    from engine.app.routes import telegram as tg

    for i, mot in enumerate(("xamuma", "Xamu ma.", "xamuma ko")):
        tg.ETATS[20 + i] = {"culture": "tomato", "attend_date": True}
        with mock.patch.object(tg, "envoyer"):
            tg.traiter({"message": {"chat": {"id": 20 + i}, "text": mot}})
        assert tg.ETATS[20 + i]["repiquage"] is None and not tg.ETATS[20 + i]["attend_date"], mot
