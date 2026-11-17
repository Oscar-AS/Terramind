"""Mémoire du bot : état gardé après un redémarrage, échanges récents, oubli à la demande (Supabase simulé)."""

import datetime as dt
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.app import memoire  # noqa: E402
from engine.app.routes import telegram as tg  # noqa: E402


class FausseBase:
    """Remplace l'API REST de Supabase : un dictionnaire clé → état."""

    def __init__(self):
        self.lignes, self.panne = {}, False

    def __call__(self, methode, chemin, corps=None, entetes=None):
        if self.panne:
            raise OSError("Supabase injoignable")
        if methode == "POST":
            self.lignes[corps["cle"]] = corps["etat"]
            return None
        cle = chemin.split("cle=eq.")[1].split("&")[0]
        if methode == "DELETE":
            self.lignes.pop(cle, None)
            return None
        return [{"etat": self.lignes[cle]}] if cle in self.lignes else []


def _avec_base():
    base = FausseBase()
    return base, mock.patch.multiple(memoire, _requete=base, _reglages=lambda: ("https://x", "k"))


def test_aller_retour_avec_date():
    base, patch = _avec_base()
    with patch:
        etat = {"langue": "wo", "lat": 14.76, "lon": -17.21, "culture": "tomato",
                "repiquage": dt.date(2026, 10, 20), "attend_date": False, "drapeau_du_moment": 1}
        assert memoire.enregistrer(99, etat)
        assert str(99) not in "".join(base.lignes)  # le numéro de conversation n'est jamais stocké
        relu = memoire.charger(99)
    assert relu["repiquage"] == dt.date(2026, 10, 20) and relu["langue"] == "wo"
    assert "drapeau_du_moment" not in relu


def test_sans_supabase_rien_ne_casse():
    with mock.patch.object(memoire, "_reglages", lambda: None):
        assert memoire.charger(1) == {} and memoire.enregistrer(1, {"langue": "fr"}) is False


def test_panne_supabase_le_bot_continue():
    base, patch = _avec_base()
    base.panne = True
    with patch:
        assert memoire.charger(1) == {} and memoire.enregistrer(1, {"langue": "fr"}) is False


def test_le_bot_se_souvient_apres_un_redemarrage():
    base, patch = _avec_base()
    with patch, mock.patch.object(tg, "envoyer"), mock.patch.object(tg, "dire"), \
            mock.patch.object(tg, "_appel_silencieux"):
        tg.ETATS.clear()
        tg.traiter_sans_planter({"update_id": 1, "callback_query": {
            "id": "q", "data": "langue:wo", "message": {"chat": {"id": 21}}}})
        tg.ETATS.clear()  # Render s'est endormi : la mémoire vive est vide
        with mock.patch.object(tg, "_question") as question:
            tg.traiter_sans_planter({"update_id": 2, "message": {"chat": {"id": 21}, "text": "Bonjour"}})
        question.assert_called_once()  # pas de nouvelle demande de langue : elle a été rechargée
    assert tg.ETATS[21]["langue"] == "wo"


def test_oublier():
    base, patch = _avec_base()
    with patch, mock.patch.object(tg, "envoyer") as envoyer, mock.patch.object(tg, "dire"):
        tg.ETATS.clear()
        memoire.enregistrer(22, {"langue": "fr", "culture": "onion"})
        tg.traiter_sans_planter({"update_id": 3, "message": {"chat": {"id": 22}, "text": "/oublier"}})
        assert base.lignes == {} and 22 not in tg.ETATS
        assert "oublié" in envoyer.call_args.args[1]


def test_echanges_recents_limites_et_perimes():
    etat = {}
    for i in range(5):
        memoire.ajouter_echange(etat, f"question {i}", "réponse")
    assert [e["question"] for e in memoire.echanges_recents(etat)] == ["question 2", "question 3", "question 4"]
    plus_tard = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)
    assert memoire.echanges_recents(etat, plus_tard) == []


def test_question_de_suite_retrouve_le_sujet():
    """« Et pour l'oignon ? » après une question sur le mildiou : les passages du mildiou de l'oignon sont
    trouvés grâce à la question précédente (recherche seule, sans Gemini)."""
    from engine.app.modules.rag import reponse

    historique = [{"question": "Comment reconnaître le mildiou ?", "reponse": "…",
                   "quand": dt.datetime.now(dt.timezone.utc).isoformat()}]
    with mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        seul = reponse._chercher("Et pour l'oignon ?", None)
        suite = reponse._chercher("Et pour l'oignon ?", historique)
    assert any("mildiou" in (p.fiche + p.texte).lower() for _, p in suite)
    assert len(suite) >= len(seul)
