"""Tests des points d'entrée /v1 et des règles, sans réseau (météo et sol remplacés).

Lancer depuis la racine : .venv/bin/python -m unittest discover engine/tests
"""

import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from fastapi.testclient import TestClient
    from engine.app.main import app
except ImportError:
    TestClient = None

from engine.app.modules.planification.plan import evaluer
from engine.app.modules.prevention import regles

COMMUN = {"utilisateur": "test", "canal": "mobile", "langue": "fr"}
SOL = {"ph": 6.6, "sable_pct": 62, "argile_pct": 20, "texture": "Sandy Clay Loam", "source": "test"}


class Regles(unittest.TestCase):
    def test_tomcast_tableau(self):
        self.assertEqual(regles.note_tomcast(0, 20), 0)
        self.assertEqual(regles.note_tomcast(9, 19), 2)   # 18-21 °C : 4 h → 1, 9 h → 2
        self.assertEqual(regles.note_tomcast(23, 27), 4)

    def test_hutton_deux_jours_de_suite(self):
        j = lambda d, tmin, h: {"date": dt.date(2026, 2, d), "tmin": tmin, "h90_frais": h, "dsv": 0}  # noqa: E731
        self.assertEqual(regles.jours_hutton([j(1, 12, 7), j(2, 12, 6)]), [dt.date(2026, 2, 2)])
        self.assertEqual(regles.jours_hutton([j(1, 12, 7), j(2, 9, 6)]), [])     # Tmin < 10
        self.assertEqual(regles.jours_hutton([j(1, 12, 7), j(3, 12, 7)]), [])    # pas consécutifs

    def test_degres_jours(self):
        serie = {dt.date(2026, 1, d): (18.0, 28.0) for d in range(1, 31)}  # moyenne 23 °C
        self.assertAlmostEqual(regles.generations(serie, 8.0, 440), 30 * 15 / 440)


class Plan(unittest.TestCase):
    def test_hors_saison(self):
        self.assertEqual(evaluer("carrot", 8, SOL, "non", "non")["adaptation"], "deconseillee")

    def test_eau_salee_exclut_oignon(self):
        r = evaluer("onion", 11, SOL, "oui", "non")
        self.assertEqual(r["adaptation"], "deconseillee")
        self.assertEqual(evaluer("tomato", 11, SOL, "oui", "non")["adaptation"], "conseillee")

    def test_sol_acide(self):
        self.assertEqual(evaluer("onion", 11, {**SOL, "ph": 5.4}, "non", "non")["adaptation"], "possible")


@unittest.skipIf(TestClient is None, "FastAPI absent")
class Routes(unittest.TestCase):
    def setUp(self):
        self.c = TestClient(app)

    def test_plan(self):
        with mock.patch("engine.app.modules.planification.plan.sol", return_value=SOL):
            r = self.c.post("/v1/plan", json={**COMMUN, "lat": 14.76, "lon": -17.21, "date": "2026-11-13",
                                              "eau_puits_salee": "non", "champ_en_bas_fond": "non"})
        self.assertEqual(r.status_code, 200)
        corps = r.json()
        self.assertEqual(corps["statut"], "ok")
        self.assertFalse(corps["mock"])
        self.assertTrue(corps["sources"])
        self.assertEqual(len(corps["donnees"]["cultures"]), 6)

    def test_alerte_sans_culture(self):
        r = self.c.post("/v1/alert", json={**COMMUN, "lat": 14.76, "lon": -17.21})
        self.assertEqual(r.json()["statut"], "culture_requise")

    def test_alerte_meteo_indisponible(self):
        from engine.app.modules import meteo
        with mock.patch("engine.app.routes.v1.calculer", side_effect=meteo.MeteoIndisponible("x")):
            r = self.c.post("/v1/alert", json={**COMMUN, "lat": 14.76, "lon": -17.21, "culture": "tomato"})
        self.assertEqual(r.status_code, 503)

    def test_chat_hors_sujet(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            r = self.c.post("/v1/chat", json={**COMMUN, "texte": "Quel est le prix du riz à Dakar ?"})
        self.assertEqual(r.json()["statut"], "je_ne_sais_pas")

    def test_chat_fiche_sourcee(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            r = self.c.post("/v1/chat", json={**COMMUN, "texte": "Ma tomate a des taches brunes avec des cercles"})
        corps = r.json()
        self.assertEqual(corps["statut"], "ok")
        self.assertIn("Alternariose", corps["message"]["texte"])
        self.assertTrue(corps["sources"])

    def test_langue_invalide(self):
        r = self.c.post("/v1/chat", json={**COMMUN, "langue": "en", "texte": "x"})
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()


def test_fiche_en_4_parties_pour_chaque_maladie():
    from engine.app.routes.v1 import FICHES_ETIQUETTES, PARTIES_FICHE, fiche_simple
    from engine.app.modules.rag import fiches

    for etiquette in FICHES_ETIQUETTES:
        f = fiche_simple(etiquette)
        assert f, etiquette
        for cle in PARTIES_FICHE:
            assert f[cle], f"{etiquette} : partie « {PARTIES_FICHE[cle]} » absente"
        assert f["sources"], etiquette
    # Pas encore de fiche : rien d'inventé.
    assert fiche_simple("septoria_leaf_spot") is None
    # Aucune fiche ne nomme de produit de traitement (TerraMind ne donne ni produit ni dose).
    interdits = ("mancozèbe", "mancozeb", "cuivre", "deltaméthrine", "abamectine", "endosulfan", "bicarbonate")
    for p in fiches.passages():
        assert not any(m in p.texte.lower() for m in interdits), (p.fiche, p.section)


def test_fiche_filtree_sur_la_culture_de_la_photo():
    from engine.app.routes.v1 import fiche_simple

    oignon = fiche_simple("fusarium", "onion")
    assert "bulbe" in oignon["ce_que_c_est"] and "Sur la tomate" not in oignon["ce_que_c_est"]
    assert "Tomate :" not in oignon["eviter"] and "Oignon :" in oignon["eviter"]
