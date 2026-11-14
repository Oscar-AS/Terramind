"""Routes et gestionnaires pour les modules Planification (/v1/plan) et Prévention (/v1/alert).

Respecte l'enveloppe commune définie dans docs/api.md § 1, 3 et 4.
Les fonctions pures `traiter_requete_plan` et `traiter_requete_alert` fonctionnent même
dans un environnement sans FastAPI, et sont branchées sur le routeur FastAPI dès que disponible.
"""

from __future__ import annotations

from ..modules.planification import HorsZoneError, planifier
from ..modules.prevention import CULTURES_CONNUES, calculer_alertes


def _reponse_erreur(langue: str, texte_fr: str, reponse_type: str = "erreur_requete") -> dict:
    return {
        "version": "0.1",
        "mock": False,
        "statut": "erreur",
        "langue": langue if langue in ("fr", "wo") else "fr",
        "message": {
            "texte": texte_fr,
            "texte_fr": texte_fr,
            "audio_url": None,
            "reponse_type": reponse_type,
        },
        "sources": [],
        "donnees": {},
    }


def _formater_message_plan(resultat: dict, langue: str) -> dict:
    sol_info = resultat["sol"]
    conseillees = [c["libelle"] for c in resultat["cultures"] if c["adaptation"] == "conseillee"]
    possibles = [c["libelle"] for c in resultat["cultures"] if c["adaptation"] == "possible"]

    if conseillees:
        liste_fr = ", ".join(conseillees[:4])
        texte_fr = (
            f"Sol {sol_info['texture']} ({sol_info['sable_pct']} % de sable, pH {sol_info['ph']}) : "
            f"cultures conseillées en ce moment : {liste_fr}."
        )
    elif possibles:
        liste_fr = ", ".join(possibles[:4])
        texte_fr = (
            f"Sol {sol_info['texture']} (pH {sol_info['ph']}) : "
            f"cultures possibles avec précautions : {liste_fr}."
        )
    else:
        texte_fr = (
            f"Sol {sol_info['texture']} (pH {sol_info['ph']}) : "
            "les conditions actuelles sont difficiles ; consulte un agent agricole."
        )

    if langue == "wo":
        texte_wo = (
            f"Suuf si ({sol_info['texture']}, pH {sol_info['ph']}) : "
            f"mbay yi ñu digle fii ak jamono jii mooy : {', '.join((conseillees or possibles)[:3])}."
        )
        return {
            "texte": texte_wo,
            "texte_fr": texte_fr,
            "audio_url": None,
            "reponse_type": "plan_cultures",
        }

    return {
        "texte": texte_fr,
        "texte_fr": texte_fr,
        "audio_url": None,
        "reponse_type": None,
    }


def _formater_message_alert(resultat: dict, langue: str) -> dict:
    if resultat["statut"] == "culture_requise":
        texte_fr = "Précise d'abord la culture de ta parcelle pour calculer les alertes météo."
        texte_wo = "Waxal ban mbay nga jëmbët ci sa tool ngir ñu xool risques météo yi."
        return {
            "texte": texte_wo if langue == "wo" else texte_fr,
            "texte_fr": texte_fr,
            "audio_url": None,
            "reponse_type": "culture_requise",
        }

    actives = [a for a in resultat["alertes"] if a["niveau"] in ("favorable", "surveiller")]
    if actives:
        texte_fr = " ".join(a["conseil"] for a in actives)
    else:
        texte_fr = "Aucune alerte météo particulière cette semaine : maintiens une surveillance régulière."

    if langue == "wo":
        texte_wo = (
            "Maytu sa tool ci jamono jii : xoolal xob yi bu baax. " + texte_fr
            if actives
            else "Amul alerte météo bu mag ci ayu-bés bii : waaye wéyal di xool sa tool."
        )
        return {
            "texte": texte_wo,
            "texte_fr": texte_fr,
            "audio_url": None,
            "reponse_type": "alerte_meteo" if actives else "alerte_ras",
        }

    return {
        "texte": texte_fr,
        "texte_fr": texte_fr,
        "audio_url": None,
        "reponse_type": None,
    }


def traiter_requete_plan(corps: dict) -> tuple[int, dict]:
    """Traite une requête /v1/plan et renvoie (code_http, enveloppe_json)."""
    langue = str(corps.get("langue") or "fr").strip().lower()
    if langue not in ("fr", "wo"):
        return 400, _reponse_erreur("fr", f"Langue non prise en charge : {langue}. Choisir 'fr' ou 'wo'.")

    if "lat" not in corps or "lon" not in corps:
        return 400, _reponse_erreur(langue, "Champs obligatoires manquants : lat et lon.")

    try:
        res = planifier(
            lat=float(corps["lat"]),
            lon=float(corps["lon"]),
            date=corps.get("date"),
            eau_puits_salee=str(corps.get("eau_puits_salee") or "ne_sait_pas"),
            champ_en_bas_fond=str(corps.get("champ_en_bas_fond") or "ne_sait_pas"),
        )
    except HorsZoneError as exc:
        return 200, {
            "version": "0.1",
            "mock": False,
            "statut": "je_ne_sais_pas",
            "langue": langue,
            "message": {
                "texte": str(exc),
                "texte_fr": str(exc),
                "audio_url": None,
                "reponse_type": "hors_zone",
            },
            "sources": [],
            "donnees": {},
        }
    except (ValueError, TypeError) as exc:
        return 400, _reponse_erreur(langue, str(exc))

    return 200, {
        "version": "0.1",
        "mock": False,
        "statut": "ok",
        "langue": langue,
        "message": _formater_message_plan(res, langue),
        "sources": res["sources"],
        "donnees": {
            "sol": res["sol"],
            "cultures": res["cultures"],
        },
    }


def traiter_requete_alert(corps: dict, autoriser_reseau: bool = True) -> tuple[int, dict]:
    """Traite une requête /v1/alert et renvoie (code_http, enveloppe_json)."""
    langue = str(corps.get("langue") or "fr").strip().lower()
    if langue not in ("fr", "wo"):
        return 400, _reponse_erreur("fr", f"Langue non prise en charge : {langue}. Choisir 'fr' ou 'wo'.")

    if "lat" not in corps or "lon" not in corps:
        return 400, _reponse_erreur(langue, "Champs obligatoires manquants : lat et lon.")

    culture = corps.get("culture")
    if culture and str(culture).strip().lower() not in CULTURES_CONNUES:
        texte_fr = f"Culture non prise en charge : {culture}. Oriente-toi vers un agent agricole."
        return 200, {
            "version": "0.1",
            "mock": False,
            "statut": "je_ne_sais_pas",
            "langue": langue,
            "message": {
                "texte": texte_fr,
                "texte_fr": texte_fr,
                "audio_url": None,
                "reponse_type": "culture_non_prise_en_charge",
            },
            "sources": [],
            "donnees": {},
        }

    try:
        res = calculer_alertes(
            lat=float(corps["lat"]),
            lon=float(corps["lon"]),
            culture=culture,
            date_repiquage=corps.get("date_repiquage"),
            date=corps.get("date"),
            autoriser_reseau=autoriser_reseau,
        )
    except HorsZoneError as exc:
        return 200, {
            "version": "0.1",
            "mock": False,
            "statut": "je_ne_sais_pas",
            "langue": langue,
            "message": {
                "texte": str(exc),
                "texte_fr": str(exc),
                "audio_url": None,
                "reponse_type": "hors_zone",
            },
            "sources": [],
            "donnees": {},
        }
    except (ValueError, TypeError) as exc:
        return 400, _reponse_erreur(langue, str(exc))

    return 200, {
        "version": "0.1",
        "mock": False,
        "statut": res["statut"],
        "langue": langue,
        "message": _formater_message_alert(res, langue),
        "sources": res["sources"],
        "donnees": {
            "alertes": res["alertes"],
            "meteo": res["meteo"],
        },
    }


try:
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter()

    @router.post("/v1/plan")
    @router.post("/plan")
    def route_plan(corps: dict):
        code, payload = traiter_requete_plan(corps)
        return JSONResponse(status_code=code, content=payload)

    @router.post("/v1/alert")
    @router.post("/alert")
    def route_alert(corps: dict):
        code, payload = traiter_requete_alert(corps)
        return JSONResponse(status_code=code, content=payload)

except ImportError:
    router = None
