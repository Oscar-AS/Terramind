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


class SolSecours(unittest.TestCase):
    """Serveur iSDAsoil injoignable : valeurs du point pilote si le champ en est tout proche."""

    def setUp(self):
        from engine.app.modules.planification import sol as s
        self.s = s
        s._sol_en_ligne.cache_clear()
        self.panne = mock.patch.object(s, "_valeur", side_effect=OSError("réseau coupé"))
        self.panne.start()

    def tearDown(self):
        self.panne.stop()
        self.s._sol_en_ligne.cache_clear()

    def test_position_test_rufisque(self):
        r = self.s.sol(14.76, -17.21)
        self.assertEqual((r["ph"], r["sable_pct"], r["texture"]), (6.8, 59, "Sandy Clay Loam"))
        self.assertIn("point pilote de Rufisque", r["source"])
        self.assertIn("injoignable", r["source"])

    def test_loin_des_points_pilotes(self):
        with self.assertRaises(self.s.SolIndisponible):
            self.s.sol(14.69, -17.44)  # Dakar-Plateau, à plus de 5 km de Rufisque

    def test_pas_de_donnee_reste_une_erreur(self):
        with mock.patch.object(self.s, "_valeur", return_value=None):
            with self.assertRaises(self.s.SolIndisponible):
                self.s.sol(14.76, -17.21)  # « pas de donnée » (mer, ville) : pas de secours


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
        self.assertEqual(len(corps["donnees"]["cultures"]), 8)

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
    assert fiche_simple("healthy") is None
    # Aucune fiche ne nomme de produit de traitement (TerraMind ne donne ni produit ni dose).
    interdits = ("mancozèbe", "mancozeb", "cuivre", "deltaméthrine", "abamectine", "endosulfan", "bicarbonate")
    for p in fiches.passages():
        assert not any(m in p.texte.lower() for m in interdits), (p.fiche, p.section)


def test_fiche_filtree_sur_la_culture_de_la_photo():
    from engine.app.routes.v1 import fiche_simple

    oignon = fiche_simple("fusarium", "onion")
    assert "bulbe" in oignon["ce_que_c_est"] and "Sur la tomate" not in oignon["ce_que_c_est"]
    assert "Tomate :" not in oignon["eviter"] and "Oignon :" in oignon["eviter"]


def test_plantation_recente_pas_de_date_requise():
    from engine.app.modules.prevention import alerte

    aujourdhui = dt.date(2026, 11, 16)
    with mock.patch.object(alerte.meteo, "heures", return_value={}), \
            mock.patch.object(alerte.meteo, "horaire", return_value={}), \
            mock.patch.object(alerte.regles, "resume_jours",
                              return_value=[{"date": dt.date(2026, 11, 13), "tmin": 20, "h90_frais": 0, "dsv": 0}]):
        r = alerte.calculer(14.76, -17.21, "tomato", aujourdhui, dt.date(2026, 11, 15))
    niveaux = {a["risque"]: a["niveau"] for a in r["alertes"]}
    assert "date_requise" not in niveaux and niveaux["tuta_absoluta"] == "aucun"


def test_alerte_date_future_refusee():
    if TestClient is None:
        return
    r = TestClient(app).post("/v1/alert", json={**COMMUN, "lat": 14.76, "lon": -17.21, "culture": "tomato",
                                                "date": "2026-11-16", "date_repiquage": "2026-11-20"})
    assert r.status_code == 400


def test_retour_journalise_le_risque():
    if TestClient is None:
        return
    with mock.patch("engine.app.routes.v1.journal") as j:
        r = TestClient(app).post("/v1/feedback", json={**COMMUN, "alerte_id": "a-2026-11-16-late_blight-14.76--17.21",
                                                       "vu": "oui"})
    assert r.status_code == 200 and j.info.call_args.args[1] == "late_blight"


def test_photo_trop_lourde_lue_par_morceaux():
    if TestClient is None:
        return
    from engine.app.routes import v1
    with mock.patch.object(v1, "PHOTO_MAX", 10):
        r = TestClient(app).post("/v1/diagnose", files={"photo": ("p.jpg", b"x" * 50, "image/jpeg")},
                                 data={k: v for k, v in COMMUN.items()})
    assert r.status_code == 413


def test_png_geant_refuse_avant_decodage():
    import io
    from PIL import Image
    from engine.app.modules.diagnostic import modele

    tampon = io.BytesIO()
    Image.new("L", (6000, 5000)).save(tampon, "PNG")  # 30 millions de pixels, quelques Ko compressés
    with self_raises(ValueError):
        modele._preparer(tampon.getvalue())


def test_vignette_trop_petite_refusee():
    import io
    from PIL import Image
    from engine.app.modules.diagnostic import modele

    tampon = io.BytesIO()
    Image.new("RGB", (40, 300), (60, 140, 50)).save(tampon, "JPEG")  # côté court 40 px < 64
    with self_raises(ValueError):
        modele._preparer(tampon.getvalue())
    tampon = io.BytesIO()
    Image.new("RGB", (64, 64), (60, 140, 50)).save(tampon, "JPEG")  # 64 px : accepté
    assert modele._preparer(tampon.getvalue()).shape == (1, 3, 224, 224)


class self_raises:
    def __init__(self, exc):
        self.exc = exc

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        assert t is not None and issubclass(t, self.exc), t
        return True


def _faux_diagnostic(etiquette, culture, categorie="maladie", libelle="Mildiou"):
    return {"predictions": [{"culture": culture, "etiquette": etiquette, "categorie": categorie,
                             "libelle": libelle, "confiance": 0.9}],
            "seuil_incertain": 0.6, "fiche": None, "questions_suivi": [], "certain": True}


def test_question_de_suivi_mineuse_sur_la_tomate():
    if TestClient is None:
        return
    from engine.app.modules.diagnostic import modele
    for etiquette, categorie in (("late_blight", "maladie"), ("healthy", "sain")):
        with mock.patch.object(modele, "diagnostiquer", return_value=_faux_diagnostic(etiquette, "tomato", categorie)):
            r = TestClient(app).post("/v1/diagnose", files={"photo": ("p.jpg", b"x", "image/jpeg")}, data=COMMUN).json()
        q = r["donnees"]["questions_suivi"]
        assert len(q) == 1 and q[0]["fiche"] == "ravageur-mineuse-tomate" and "Tuta absoluta" in q[0]["si_oui"]
        assert any(s["page"] == "29" and "Protection des Végétaux" in s["document"] for s in r["sources"])


def test_pas_de_question_de_suivi_sur_l_oignon_ni_si_incertain():
    if TestClient is None:
        return
    from engine.app.modules.diagnostic import modele
    with mock.patch.object(modele, "diagnostiquer", return_value=_faux_diagnostic("fusarium", "onion")):
        r = TestClient(app).post("/v1/diagnose", files={"photo": ("p.jpg", b"x", "image/jpeg")}, data=COMMUN).json()
    assert r["donnees"]["questions_suivi"] == []
    incertain = {**_faux_diagnostic("late_blight", "tomato"), "certain": False}
    with mock.patch.object(modele, "diagnostiquer", return_value=incertain):
        r = TestClient(app).post("/v1/diagnose", files={"photo": ("p.jpg", b"x", "image/jpeg")}, data=COMMUN).json()
    assert r["statut"] == "incertain" and r["donnees"]["questions_suivi"] == []
