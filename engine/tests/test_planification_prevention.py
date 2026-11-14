"""Tests unitaires et d'intégration des modules Planification et Prévention (Chantier 1)."""

from __future__ import annotations

import datetime as dt

import pytest

from engine.app.modules.planification import HorsZoneError, arrondir_gps, planifier, sol
from engine.app.modules.prevention import calculer_alertes, note_tomcast
from engine.app.routes.agronomie import traiter_requete_alert, traiter_requete_plan

# --- 1. Tests du module Planification (sol + règles sol -> culture) ---


def test_arrondir_gps_confidentialite():
    assert arrondir_gps(14.759312, -17.205489) == (14.76, -17.21)


@pytest.mark.parametrize(
    "lat, lon, dep_attendu, texture_attendue, ph_attendu, sable_attendu",
    [
        (14.76, -17.21, "Rufisque", "Sandy Clay Loam", 6.8, 59),
        (14.75, -16.87, "Thies", "Sandy Loam", 6.3, 72),
        (15.09, -16.65, "Tivaoune", "Sandy Loam", 6.4, 76),
        (15.30, -16.26, "Kebemer", "Sandy Loam", 6.9, 83),
    ],
)
def test_sol_points_pilotes_isdasoil(lat, lon, dep_attendu, texture_attendue, ph_attendu, sable_attendu):
    res = sol(lat, lon)
    assert res["departement_proche"] == dep_attendu
    assert res["texture"] == texture_attendue
    assert res["ph"] == ph_attendu
    assert res["sable_pct"] == sable_attendu
    assert res["source"] == "iSDAsoil 30 m, 0-20 cm"
    assert res["date"] == "2026-11-02"


def test_sol_hors_zone_refuse_sans_inventer():
    # Hors du Sénégal
    with pytest.raises(HorsZoneError):
        sol(48.85, 2.35)
    # Au Sénégal oriental (Tambacounda), trop loin des points pilotes des Niayes
    with pytest.raises(HorsZoneError):
        sol(13.77, -13.67)


def test_planifier_saison_fraiche_et_filtres_sel_bas_fond():
    # Cas 1 : Novembre à Rufisque, eau douce, hors bas-fond -> oignon, tomate et chou conseillés
    res = planifier(14.76, -17.21, date="2026-11-05", eau_puits_salee="non", champ_en_bas_fond="non")
    par_culture = {c["culture"]: c for c in res["cultures"]}
    assert par_culture["onion"]["adaptation"] == "conseillee"
    assert par_culture["tomato"]["adaptation"] == "conseillee"
    assert par_culture["cabbage"]["adaptation"] == "conseillee"

    # Cas 2 : Eau du puits salée -> oignon et carotte passent en déconseillée
    res_sel = planifier(14.76, -17.21, date="2026-11-05", eau_puits_salee="oui", champ_en_bas_fond="non")
    par_culture_sel = {c["culture"]: c for c in res_sel["cultures"]}
    assert par_culture_sel["onion"]["adaptation"] == "deconseillee"
    assert par_culture_sel["carrot"]["adaptation"] == "deconseillee"

    # Cas 3 : Champ en bas-fond -> oignon passe de conseillée à possible avec avertissement drainage
    res_bf = planifier(14.76, -17.21, date="2026-11-05", eau_puits_salee="non", champ_en_bas_fond="oui")
    par_culture_bf = {c["culture"]: c for c in res_bf["cultures"]}
    assert par_culture_bf["onion"]["adaptation"] == "possible"
    assert any("bas-fond" in a for a in par_culture_bf["onion"]["avertissements"])

    # Cas 4 : Plein hivernage (août) -> pomme de terre, oignon et carotte déconseillés
    res_hiv = planifier(15.09, -16.65, date="2026-08-15", eau_puits_salee="non", champ_en_bas_fond="non")
    par_culture_hiv = {c["culture"]: c for c in res_hiv["cultures"]}
    assert par_culture_hiv["potato"]["adaptation"] == "deconseillee"
    assert par_culture_hiv["onion"]["adaptation"] == "deconseillee"
    assert par_culture_hiv["carrot"]["adaptation"] == "deconseillee"


# --- 2. Tests du module Prévention (Hutton plafonné, TOMCAST, degrés-jours) ---


def test_prevention_culture_obligatoire():
    res = calculer_alertes(lat=15.09, lon=-16.65, culture=None, date="2027-02-10", autoriser_reseau=False)
    assert res["statut"] == "culture_requise"
    assert res["alertes"] == []


def test_prevention_hutton_plafonne_et_plafond_wallin():
    base = dt.date(2026, 2, 1)
    # Cas A : 2 jours consécutifs avec Tmin >= 10 °C et 8 h à RH=95 %, T=20 °C (<= 26,6 °C) -> favorable
    releves_favorables = []
    for j in range(7):
        d = base + dt.timedelta(days=j)
        for h in range(24):
            if j in (4, 5) and h < 8:
                releves_favorables.append((d, 20.0, 95.0))
            else:
                releves_favorables.append((d, 22.0, 60.0))

    res_fav = calculer_alertes(
        lat=15.09,
        lon=-16.65,
        culture="tomato",
        date_repiquage="2026-01-01",
        date=base + dt.timedelta(days=6),
        releves_horaires=releves_favorables,
        autoriser_reseau=False,
    )
    mildiou_fav = next(a for a in res_fav["alertes"] if a["risque"] == "late_blight")
    assert mildiou_fav["niveau"] == "favorable"
    assert mildiou_fav["detail"]["jours_conditions_remplies"] == 2

    # Cas B : mêmes heures humides mais à T = 28,0 °C (> plafond 26,6 °C de Wallin) -> aucun risque mildiou
    releves_chauds = []
    for j in range(7):
        d = base + dt.timedelta(days=j)
        for h in range(24):
            if j in (4, 5) and h < 8:
                releves_chauds.append((d, 28.0, 95.0))
            else:
                releves_chauds.append((d, 24.0, 60.0))

    res_chaud = calculer_alertes(
        lat=15.09,
        lon=-16.65,
        culture="tomato",
        date_repiquage="2026-01-01",
        date=base + dt.timedelta(days=6),
        releves_horaires=releves_chauds,
        autoriser_reseau=False,
    )
    mildiou_chaud = next(a for a in res_chaud["alertes"] if a["risque"] == "late_blight")
    assert mildiou_chaud["niveau"] == "aucun"
    assert mildiou_chaud["detail"]["jours_conditions_remplies"] == 0


def test_note_tomcast():
    assert note_tomcast(0, 22.0) == 0
    assert note_tomcast(4, 22.5) == 1
    assert note_tomcast(8, 22.5) == 2
    assert note_tomcast(15, 22.5) == 3
    assert note_tomcast(22, 22.5) == 4


def test_enveloppes_v1_plan_et_alert_conformes_contrat_api():
    # Test /v1/plan en wolof (vérifie D10 : texte_fr toujours présent)
    code_plan, body_plan = traiter_requete_plan(
        {
            "lat": 14.76,
            "lon": -17.21,
            "date": "2026-11-05",
            "eau_puits_salee": "non",
            "champ_en_bas_fond": "oui",
            "utilisateur": "sha256_test",
            "canal": "whatsapp",
            "langue": "wo",
        }
    )
    assert code_plan == 200
    assert body_plan["mock"] is False
    assert body_plan["statut"] == "ok"
    assert body_plan["message"]["texte_fr"]
    assert body_plan["sources"]
    assert body_plan["donnees"]["sol"]["texture"] == "Sandy Clay Loam"

    # Test /v1/alert sur l'exemple exact de docs/api.md § 4
    code_alert, body_alert = traiter_requete_alert(
        {
            "lat": 15.09,
            "lon": -16.65,
            "culture": "tomato",
            "date_repiquage": "2026-12-01",
            "date": "2027-02-10",
            "utilisateur": "sha256_test",
            "canal": "whatsapp",
            "langue": "wo",
        },
        autoriser_reseau=False,
    )
    assert code_alert == 200
    assert body_alert["mock"] is False
    assert body_alert["statut"] == "ok"
    assert body_alert["sources"]
    risques = {a["risque"]: a for a in body_alert["donnees"]["alertes"]}
    assert risques["late_blight"]["niveau"] == "favorable"
    assert risques["tuta_absoluta"]["niveau"] == "surveiller"
    assert risques["tuta_absoluta"]["detail"]["generations_depuis_repiquage"] >= 2.5
