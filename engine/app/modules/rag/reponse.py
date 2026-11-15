"""Réponse à une question libre (POST /v1/chat), à partir des seules fiches (D8).

1. Recherche des passages pertinents (fiches.py). Sous le score minimal : « je ne sais pas ».
2. Rédaction :
   - avec GEMINI_API_KEY : Gemini rédige une réponse courte **uniquement** à partir des passages,
     sans produit ni dose ; s'il juge que les passages ne répondent pas, il renvoie JE_NE_SAIS_PAS ;
   - sans clé, ou si Gemini échoue : on renvoie le passage le plus pertinent tel quel (extractif).
Rien de personnel n'est envoyé à Gemini : seulement la question et les extraits de fiches.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request

from ... import config  # noqa: F401  (charge .env avant de lire la clé)
from . import fiches

journal = logging.getLogger("terramind.rag")
SCORE_MIN = 3.5  # voir docs/seuils-et-parametres.md (mesure sur 20 questions)
GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
CONSIGNE = (
    "Tu es TerraMind, assistant pour les petits maraîchers des Niayes (Sénégal), souvent peu lettrés. "
    "Parle comme un conseiller agricole bienveillant qui accompagne l'agriculteur pas à pas : "
    "réponds d'abord directement à la question, puis donne ce qu'il peut faire, dans l'ordre. "
    "Ne répète jamais une action déjà dite : chaque phrase apporte une information nouvelle. "
    "N'annonce pas une liste (« fais ces actions dans l'ordre ») pour une ou deux actions seulement. "
    "Français simple : 3 à 6 phrases courtes, tutoiement, sans jargon. "
    "Texte simple : pas de Markdown (ni astérisques ni titres), pas d'émoji. "
    "Utilise UNIQUEMENT les extraits de fiches fournis : n'ajoute aucune information extérieure. "
    "Ne cite jamais de produit chimique, de pesticide ni de dose ; pour un traitement, renvoie vers un agent agricole. "
    "Si les extraits ne permettent pas de répondre à la question, réponds exactement : JE_NE_SAIS_PAS"
)


def gemini(consigne: str, texte: str, delai: int = 30) -> str | None:
    """Appel simple à Gemini (consigne système + un message). None sans clé ou en cas d'échec."""
    cle = os.environ.get("GEMINI_API_KEY", "").strip()
    if not cle:
        return None
    modele = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"
    corps = {
        "system_instruction": {"parts": [{"text": consigne}]},
        "contents": [{"role": "user", "parts": [{"text": texte}]}],
    }
    req = urllib.request.Request(GEMINI.format(modele=modele), data=json.dumps(corps).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": cle})
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            d = json.loads(r.read())
        reponse = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"]).strip()
        return reponse or None
    except Exception as e:  # quota, réseau, modèle indisponible
        journal.warning("Gemini indisponible (%s)", type(e).__name__)
        return None


def _gemini(question: str, ps: list[fiches.Passage]) -> str | None:
    extraits = "\n\n".join(f"[Fiche « {p.titre} », section « {p.section} »]\n{p.texte}" for p in ps)
    return gemini(CONSIGNE, f"Extraits de fiches :\n{extraits}\n\nQuestion : {question}")


def repondre(question: str) -> dict:
    trouves = [(s, p) for s, p in fiches.chercher(question) if s >= SCORE_MIN]
    if not trouves:
        return {"statut": "je_ne_sais_pas", "texte": None, "passages": [], "sources": [], "mode": "aucun"}
    ps = [p for _, p in trouves]
    # La fiche la plus pertinente apporte aussi sa section « Prévention » : une question sur un
    # symptôme appelle presque toujours « que faire ? ».
    prevention = [p for p in fiches.passages() if p.fiche == ps[0].fiche
                  and p.section.lower().startswith(("prévention", "que faire")) and p not in ps]
    ps += prevention[:1]
    redige = _gemini(question, ps)
    if redige and "JE_NE_SAIS_PAS" in redige:
        return {"statut": "je_ne_sais_pas", "texte": None, "passages": [], "sources": [], "mode": "gemini"}
    if redige:
        utilises, mode, texte = ps, "gemini", redige
    else:
        p = ps[0]
        utilises, mode = [p], "extractif"
        texte = f"D'après la fiche « {p.titre} » ({p.section.lower()}) :\n{p.texte}"
    return {
        "statut": "ok", "texte": texte, "mode": mode, "sources": fiches.sources_de(utilises),
        "passages": [{"fiche": p.fiche, "section": p.section, "extrait": p.texte[:300]} for p in utilises],
    }
