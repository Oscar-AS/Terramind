"""Règles météo ajoutées le 14 nov 2026 : DOWNCAST (oignon)."""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.app.modules.prevention import regles  # noqa: E402


def _heures(t_jour, t_nuit, hr_matin):
    veille, jour = dt.date(2026, 11, 1), dt.date(2026, 11, 2)
    h = {}
    for k in range(24):
        h[dt.datetime.combine(veille, dt.time(k))] = (t_jour if 8 <= k < 20 else t_nuit, 80)
        h[dt.datetime.combine(jour, dt.time(k))] = (t_nuit if k < 8 else t_jour, hr_matin if 2 <= k < 6 else 80)
    return h


def test_downcast_nuit_humide_et_fraiche():
    assert regles.jours_downcast(_heures(22, 18, 97)) == [dt.date(2026, 11, 2)]


def test_downcast_refuse_si_journee_chaude_ou_matin_sec():
    assert regles.jours_downcast(_heures(26, 18, 97)) == []
    assert regles.jours_downcast(_heures(22, 18, 93)) == []


def test_downcast_pluie_de_nuit_ecarte():
    h = _heures(22, 18, 97)
    jour = dt.date(2026, 11, 2)
    h = {k: v + ((0.5,) if k.date() == jour and k.hour in (1, 2, 3) else (0.0,)) for k, v in h.items()}
    ecartes = []
    assert regles.jours_downcast(h, ecartes) == [] and ecartes == [jour]  # 1,5 mm de 23 h à 4 h


def test_date_requise_pour_les_ravageurs():
    from unittest import mock
    from engine.app.modules.prevention import alerte
    with mock.patch.object(alerte.meteo, "journalier", return_value={}):
        d = alerte.calculer(14.7, -17.2, "pepper", dt.date(2026, 11, 14), None)
    assert [(a["risque"], a["niveau"]) for a in d["alertes"]] == [("date_requise", "date_requise")]
    assert "quand tu l'as plantée" in d["alertes"][0]["conseil"]
