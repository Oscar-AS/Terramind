"""Que planter ici, et quand (POST /v1/plan).

Règles (proposition de l'équipe à partir du G87, non validée par un agronome) :
- hors de la période de semis du mois courant : « deconseillee » (pas maintenant) ;
- eau du puits salée et culture très sensible au sel : « deconseillee » ;
- pH sous le minimum de la culture : « possible » avec un avertissement ;
- sol lourd (argile ≥ 35 %) pour une culture qui le craint : « possible » avec un avertissement ;
- champ en bas-fond ou salinité inconnue : avertissement pour les cultures très sensibles au sel ;
- champ en bas-fond pour une culture qui craint les sols trop humides (oignon, pomme de terre, G87 p. 11) :
  « possible » avec un avertissement.
Aucun rendement n'est promis.
"""

from __future__ import annotations

import datetime as dt

from .cultures import CULTURES, SOURCE_BAS_FOND, SOURCE_PH, SOURCE_SEL
from .sol import sol

ARGILE_LOURD = 35
# pH en mots, d'après les classes de réaction du sol de l'USDA (Soil Survey Manual, Handbook 18, chap. 3,
# « Soil reaction ») regroupées en 5 niveaux : ≤ 5,5 « strongly acid » et moins ; 5,6-6,5 « moderately » et
# « slightly acid » ; 6,6-7,3 « neutral » ; 7,4-8,4 « slightly » et « moderately alkaline » ; ≥ 8,5 plus basique.
NIVEAUX_PH = (
    (5.6, "très acide"),
    (6.6, "un peu acide"),
    (7.4, "ni acide ni basique"),
    (8.5, "un peu basique (le contraire d'acide)"),
    (99, "très basique (le contraire d'acide)"),
)


def ph_en_mots(ph: float | None) -> str | None:
    """« un peu acide » pour 6,1 ; None si le pH est inconnu."""
    if ph is None:
        return None
    return next(mots for limite, mots in NIVEAUX_PH if ph < limite)


def nombre_fr(x: float) -> str:
    return f"{x:g}".replace(".", ",")


ORDRE = {"conseillee": 0, "possible": 1, "deconseillee": 2}


def evaluer(culture: str, mois: int, sol_: dict, eau_salee: str, bas_fond: str) -> dict:
    c = CULTURES[culture]
    raisons, avertissements = [], []
    adaptation = "conseillee"

    if mois in c["mois_semis"]:
        raisons.append("C'est la bonne période pour semer ou planter.")
        if mois in c.get("hivernage", []):
            avertissements.append("En cette saison, prends une variété d'hivernage.")
    else:
        adaptation = "deconseillee"
        raisons.append("Ce n'est pas la période pour semer ou planter.")

    if c["sel"] == "tres_sensible":
        if eau_salee == "oui":
            adaptation = "deconseillee"
            raisons.append(
                "Cette culture supporte très mal le sel, et l'eau de ton puits est salée."
            )
        elif eau_salee == "ne_sait_pas" or bas_fond == "oui":
            avertissements.append(
                "Cette culture supporte très mal le sel : fais vérifier l'eau de ton puits."
            )
    elif c["sel"] == "moins_sensible" and eau_salee == "oui":
        avertissements.append("Le sel gêne les jeunes plants : fais vérifier l'eau de ton puits.")

    ph = sol_.get("ph")
    if ph is not None and c["ph_min"] is not None and ph < c["ph_min"]:
        avertissements.append(
            f"Ton sol est trop acide pour cette culture (pH {nombre_fr(ph)} ; elle demande au moins "
            f"{nombre_fr(c['ph_min'])}). Demande conseil à un agent agricole."
        )
        if adaptation == "conseillee":
            adaptation = "possible"
    argile = sol_.get("argile_pct")
    if c["sol_lourd_deconseille"] and argile is not None and argile >= ARGILE_LOURD:
        avertissements.append(
            "Ton sol semble lourd (argileux) ; cette culture préfère un sol léger."
        )
        if adaptation == "conseillee":
            adaptation = "possible"
    if c.get("craint_bas_fond") and bas_fond == "oui":
        avertissements.append(
            "Ton champ est en bas-fond : cette culture craint les sols trop humides. "
            "Choisis une partie bien drainée, ou une autre culture."
        )
        if adaptation == "conseillee":
            adaptation = "possible"
    if adaptation != "deconseillee":
        raisons.append(c["saison"])

    return {
        "culture": culture,
        "libelle": c["libelle"],
        "adaptation": adaptation,
        "periode_semis": c["periode"],
        "cycle_jours": c["cycle_jours"],
        "raisons": raisons,
        "avertissements": avertissements,
    }


def planifier(
    lat: float, lon: float, date: dt.date, eau_salee: str, bas_fond: str
) -> tuple[dict, list[dict]]:
    sol_ = dict(sol(round(lat, 2), round(lon, 2)))  # copie : sol() est mis en cache
    sol_["ph_mots"] = ph_en_mots(sol_.get("ph"))
    cultures = [evaluer(c, date.month, sol_, eau_salee, bas_fond) for c in CULTURES]
    cultures.sort(key=lambda x: (ORDRE[x["adaptation"]], x["libelle"]))
    sources = [s for c in CULTURES.values() for s in c["sources"]] + [
        SOURCE_SEL,
        SOURCE_PH,
        SOURCE_BAS_FOND,
        {"document": "iSDAsoil (iSDA, CC BY 4.0)", "page": "carte 30 m, 0-20 cm"},
    ]
    return {"sol": sol_, "cultures": cultures}, sources
