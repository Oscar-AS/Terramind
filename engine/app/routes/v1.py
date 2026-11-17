"""Points d'entrée métier /v1 (contrat : docs/api.md, v0.1).

Toutes les réponses suivent l'enveloppe commune. Langue : le wolof écrit et la voix ne sont
pas encore branchés (D9, D10) ; une demande en wolof reçoit donc le texte français, et
l'enveloppe le dit honnêtement (`langue: "fr"`, `audio_url: null`).
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Literal, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..modules import meteo
from ..modules.planification import sol as sol_module
from ..modules.planification.cultures import CULTURES
from ..modules.planification.plan import planifier
from ..modules.prevention.alerte import SOURCE_SEUILS, calculer

journal = logging.getLogger("terramind.v1")
router = APIRouter(prefix="/v1")
VERSION = "0.1"
PHOTO_MAX = 8 * 1024 * 1024
Langue = Literal["fr", "wo"]
Canal = Literal["whatsapp", "telegram", "pwa", "mobile", "dashboard"]
OuiNon = Literal["oui", "non", "ne_sait_pas"]

AGENT = ("Pour être sûr, montre ta plante à un agent agricole (ANCAR, service départemental "
         "de l'agriculture).")


def enveloppe(statut: str, texte: str, donnees: dict, sources: list | None = None, code: int = 200):
    return JSONResponse(status_code=code, content={
        "version": VERSION, "mock": False, "statut": statut, "langue": "fr",
        "message": {"texte": texte, "texte_fr": texte, "audio_url": None, "reponse_type": None},
        "sources": sources or [], "donnees": donnees,
    })


def indisponible(e: Exception):
    journal.warning("dépendance indisponible : %s", e)
    return enveloppe("erreur", "Le service est momentanément indisponible. Réessaie dans quelques minutes.",
                     {}, code=503)


class Commun(BaseModel):
    utilisateur: str = Field(min_length=1, max_length=128)
    canal: Canal
    langue: Langue


class DemandePlan(Commun):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    date: Optional[dt.date] = None
    eau_puits_salee: OuiNon = "ne_sait_pas"
    champ_en_bas_fond: OuiNon = "ne_sait_pas"


class DemandeAlerte(Commun):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    culture: Optional[str] = None
    date_repiquage: Optional[dt.date] = None
    date: Optional[dt.date] = None


class DemandeChat(Commun):
    texte: str = Field(min_length=1, max_length=2000)


class Retour(Commun):
    alerte_id: str = Field(min_length=1, max_length=200)
    vu: OuiNon


@router.post("/plan")
def plan(d: DemandePlan):
    date = d.date or dt.date.today()
    try:
        donnees, sources = planifier(d.lat, d.lon, date, d.eau_puits_salee, d.champ_en_bas_fond)
    except sol_module.SolIndisponible as e:
        return indisponible(e)
    conseillees = [c["libelle"] for c in donnees["cultures"] if c["adaptation"] == "conseillee"]
    texte = (f"Ce mois-ci, tu peux planter : {', '.join(conseillees)}."
             if conseillees else "Aucune culture de la liste n'est conseillée ce mois-ci. " + AGENT)
    journal.info("plan : %s cultures conseillées", len(conseillees))
    return enveloppe("ok", texte, donnees, sources)


@router.post("/alert")
def alerte(d: DemandeAlerte):
    if not d.culture:
        return enveloppe("culture_requise", "Dis-moi d'abord ce que tu as planté.", {})
    if d.culture not in CULTURES:
        return enveloppe("erreur", "Cette culture n'est pas encore prise en charge.", {}, code=400)
    if d.date_repiquage and d.date_repiquage > (d.date or dt.date.today()):
        return enveloppe("erreur", "La date de plantation est dans le futur. Donne le jour où tu as planté.",
                         {}, code=400)
    try:
        donnees = calculer(round(d.lat, 2), round(d.lon, 2), d.culture, d.date or dt.date.today(),
                           d.date_repiquage)
    except meteo.MeteoIndisponible as e:
        return indisponible(e)
    actives = [a["conseil"] for a in donnees["alertes"] if a["niveau"] != "aucun"]
    if not donnees["alertes"]:  # aucune règle météo sourcée pour cette culture
        texte = ("Pour cette culture, je ne surveille pas encore la météo. "
                 "Si tu vois des taches sur ta plante (feuille, fruit, tige), prends-la en photo.")
    else:
        texte = " ".join(actives) if actives else "Pas d'alerte cette semaine pour ta culture."
    return enveloppe("ok", texte, donnees, [SOURCE_SEUILS,
                     {"document": "NASA POWER", "page": "météo au point du champ"}])


@router.post("/diagnose")
async def diagnose(photo: UploadFile = File(...), culture: Optional[str] = Form(None),
                   utilisateur: str = Form(...), canal: Canal = Form(...), langue: Langue = Form(...)):
    from ..modules.diagnostic import modele  # numpy/onnxruntime chargés seulement ici

    contenu = await photo.read(PHOTO_MAX + 1)  # jamais plus que la limite en mémoire
    if len(contenu) > PHOTO_MAX:
        return enveloppe("erreur", "La photo est trop lourde.", {}, code=413)
    try:
        # Calcul du modèle hors de la boucle : le serveur continue de répondre (webhook Telegram…).
        r = await run_in_threadpool(modele.diagnostiquer, contenu, culture)
    except modele.ModeleAbsent as e:
        return indisponible(e)
    except Exception as e:  # image illisible
        journal.info("photo illisible : %s", e)
        return enveloppe("erreur", "Je n'arrive pas à lire cette photo. Reprends-la, bien nette.", {}, code=400)
    certain = r.pop("certain")
    top = r["predictions"][0]
    source = [{"document": "Modèle TerraMind v1 (TOM2024 CC BY 4.0, PlantVillage CC BY-SA 3.0, PlantDoc CC BY 4.0)",
               "page": "ml/eval/diagnostic_v1.md"}]
    if not certain:
        return enveloppe("incertain", "Je ne suis pas sûr de ce que je vois. Reprends la photo d'une seule "
                         "feuille, de près, à la lumière du jour. " + AGENT, r, source)
    r["fiche"] = fiche_simple(top["etiquette"], top.get("culture"))
    if r["fiche"]:
        source += [s for s in r["fiche"].pop("sources") if s not in source]
    r["questions_suivi"] = questions_suivi(culture or top.get("culture"))
    source += [q["source"] for q in r["questions_suivi"] if q["source"] not in source]
    if top["categorie"] == "sain":
        texte = "Cette feuille semble saine."
    else:
        texte = (f"Cela ressemble à : {top['libelle']}. Ce n'est qu'une première indication, "
                 "pas un diagnostic sûr. " + AGENT)
    return enveloppe("ok", texte, r, source)


# Ravageurs que la photo ne sait pas reconnaître (absents du modèle) : une question oui/non tirée de la fiche
# sourcée, posée après chaque diagnostic de la culture, même « saine » (idée reprise d'Oscar, docs/api.md § 2).
DPV = ("Direction de la Protection des Végétaux / PADEN, manuel des ravageurs et maladies des cultures "
       "maraîchères des Niayes (archive Wayback, source `paden` de scripts/donnees/telecharger_sources.py)")
QUESTIONS_SUIVI = {
    "tomato": [{
        "question": "Vois-tu sur les feuilles des taches claires, blanchâtres, où la peau de la feuille reste "
                    "entière ? Ou, sur les fruits, des galeries et de petits trous ?",
        "si_oui": "C'est peut-être la mineuse de la tomate (Tuta absoluta). Sa chenille vit à l'intérieur de "
                  "la feuille : je ne sais pas la reconnaître sur une photo. Montre ta plante à un agent agricole.",
        "fiche": "ravageur-mineuse-tomate",
        "source": {"document": DPV, "page": "29"},
    }],
}


def questions_suivi(culture: Optional[str]) -> list[dict]:
    return [dict(q) for q in QUESTIONS_SUIVI.get(culture or "", [])]


# Étiquette du modèle → fiche de content/fiches/.
FICHES_ETIQUETTES = {
    "alternaria": "maladie-alternariose", "late_blight": "maladie-mildiou", "leaf_mold": "maladie-cladosporiose",
    "bacterial_spot": "maladie-tache-bacterienne", "leaf_curl": "maladie-viroses-tomate",
    "mosaic_virus": "maladie-viroses-tomate", "virosis": "maladie-viroses-tomate",
    "fusarium": "maladie-fusariose", "bacterial_wilt": "maladie-fletrissement-bacterien",
    "helicoverpa_armigera": "ravageur-noctuelle-tomate", "caterpillars": "ravageur-chenilles-oignon",
    "mites": "ravageur-acariose-tomate", "blossom_end_rot": "accident-necrose-apicale",
    "sunburn": "accident-coup-de-soleil", "septoria_leaf_spot": "maladie-septoriose",
    "target_spot": "maladie-tache-cible",
}

# Les 4 questions qu'on se pose quand on est malade, dans l'ordre (sections communes des fiches).
PARTIES_FICHE = {
    "ce_que_c_est": "Ce que c'est",
    "pourquoi": "Pourquoi c'est arrivé",
    "que_faire": "Que faire maintenant",
    "eviter": "Pour que ça ne revienne pas",
}


# Débuts de ligne qui réservent une ligne de fiche à une culture (« Oignon : … », « Sur la tomate : … »).
PREFIXES_CULTURE = {
    "onion": ("oignon :", "sur l'oignon"), "tomato": ("tomate :", "sur la tomate"),
    "potato": ("pomme de terre :", "sur la pomme de terre"), "pepper": ("poivron :", "pour le poivron"),
}


def garder_culture(texte: str, culture: Optional[str]) -> str:
    """Retire les lignes réservées à une autre culture que celle de la photo."""
    if culture not in PREFIXES_CULTURE:
        return texte
    autres = tuple(p for c, ps in PREFIXES_CULTURE.items() if c != culture for p in ps)
    lignes = [l for l in texte.split("\n") if not l.lstrip("- ").lower().startswith(autres)]
    return "\n".join(lignes)


def fiche_simple(etiquette: str, culture: Optional[str] = None) -> Optional[dict]:
    """Fiche d'une étiquette en 4 parties ; chaque partie vaut None si la fiche ne l'a pas."""
    from ..modules.rag import fiches

    nom = FICHES_ETIQUETTES.get(etiquette)
    if not nom:
        return None
    ps = {p.section: p for p in fiches.passages() if p.fiche == nom}
    parties = {cle: ps.get(section) for cle, section in PARTIES_FICHE.items()}
    trouves = [p for p in parties.values() if p]
    if not trouves:
        return None
    resultat = {"fiche": nom, "titre": trouves[0].titre, "sources": fiches.sources_de(trouves)}
    resultat.update({cle: (garder_culture(p.texte, culture).replace("*", "") if p else None) for cle, p in parties.items()})
    return resultat


@router.post("/chat")
def chat(d: DemandeChat):
    # D8 : réponse uniquement à partir des fiches (content/fiches/), rédigée par Gemini si une clé
    # est configurée, sinon passage de fiche renvoyé tel quel.
    from ..modules.rag.reponse import repondre

    r = repondre(d.texte)
    donnees = {"transcription": None, "passages": r["passages"], "mode": r["mode"]}
    if r["statut"] != "ok":
        return enveloppe("je_ne_sais_pas", "Je n'ai pas la réponse dans mes fiches. " + AGENT, donnees)
    return enveloppe("ok", r["texte"], donnees, r["sources"])


@router.post("/feedback")
def feedback(d: Retour):
    # Pas encore de base de données (Supabase non configuré) : le retour est seulement journalisé, sans
    # la position. Identifiant : a-AAAA-MM-JJ-<risque>-<lat>-<lon> (la longitude du Sénégal est négative).
    m = re.fullmatch(r"a-\d{4}-\d{2}-\d{2}-([a-z_]+)-.*", d.alerte_id)
    journal.info("retour : risque=%s vu=%s canal=%s", m.group(1) if m else "?", d.vu, d.canal)
    return enveloppe("ok", "Merci pour ta réponse.", {"enregistre": False})
