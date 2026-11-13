"""Que planter ici, et quand (POST /v1/plan).

Règles (proposition de l'équipe à partir du G87, non validée par un agronome) :
- hors de la période de semis du mois courant : « deconseillee » (pas maintenant) ;
- eau du puits salée et culture très sensible au sel : « deconseillee » ;
- pH sous le minimum de la culture : « possible » avec un avertissement ;
- sol lourd (argile ≥ 35 %) pour une culture qui le craint : « possible » avec un avertissement ;
- champ en bas-fond ou salinité inconnue : avertissement pour les cultures très sensibles.
Aucun rendement n'est promis.
"""

from __future__ import annotations

import datetime as dt

from .cultures import CULTURES, SOURCE_PH, SOURCE_SEL
from .sol import sol

ARGILE_LOURD = 35
ORDRE = {"conseillee": 0, "possible": 1, "deconseillee": 2}


def evaluer(culture: str, mois: int, sol_: dict, eau_salee: str, bas_fond: str) -> dict:
    c = CULTURES[culture]
    raisons, avertissements = [], []
    adaptation = "conseillee"

    if mois in c["mois_semis"]:
        raisons.append(f"C'est la bonne période : {c['periode']}.")
        if mois in c.get("hivernage", []):
            avertissements.append("En cette saison, prends une variété d'hivernage.")
    else:
        adaptation = "deconseillee"
        raisons.append(f"Ce n'est pas la période : {c['periode']}.")

    if c["sel"] == "tres_sensible":
        if eau_salee == "oui":
            adaptation = "deconseillee"
            raisons.append("Cette culture supporte très mal le sel, et l'eau de ton puits est salée.")
        elif eau_salee == "ne_sait_pas" or bas_fond == "oui":
            avertissements.append("Cette culture supporte très mal le sel : fais vérifier l'eau de ton puits.")
    elif c["sel"] == "moins_sensible" and eau_salee == "oui":
        avertissements.append("Le sel gêne les jeunes plants : fais vérifier l'eau de ton puits.")

    ph = sol_.get("ph")
    if ph is not None and ph < c["ph_min"]:
        avertissements.append(f"Ton sol est un peu acide (pH {ph}). Demande conseil à un agent agricole.")
        if adaptation == "conseillee":
            adaptation = "possible"
    argile = sol_.get("argile_pct")
    if c["sol_lourd_deconseille"] and argile is not None and argile >= ARGILE_LOURD:
        avertissements.append("Ton sol semble lourd (argileux) ; cette culture préfère un sol léger.")
        if adaptation == "conseillee":
            adaptation = "possible"
    if adaptation != "deconseillee":
        raisons.append(c["saison"])

    return {"culture": culture, "libelle": c["libelle"], "adaptation": adaptation,
            "periode_semis": c["periode"], "cycle_jours": c["cycle_jours"],
            "raisons": raisons, "avertissements": avertissements}


def planifier(lat: float, lon: float, date: dt.date, eau_salee: str, bas_fond: str) -> tuple[dict, list[dict]]:
    sol_ = sol(round(lat, 2), round(lon, 2))
    cultures = [evaluer(c, date.month, sol_, eau_salee, bas_fond) for c in CULTURES]
    cultures.sort(key=lambda x: (ORDRE[x["adaptation"]], x["libelle"]))
    sources = [s for c in CULTURES.values() for s in c["sources"]] + [SOURCE_SEL, SOURCE_PH,
               {"document": "iSDAsoil (iSDA, CC BY 4.0)", "page": "carte 30 m, 0-20 cm"}]
    return {"sol": sol_, "cultures": cultures}, sources
