"""Réponse à une question libre (POST /v1/chat), à partir des seules fiches (D8).

1. Recherche des passages pertinents (fiches.py). Sous le score minimal : « je ne sais pas ».
2. Rédaction :
   - avec GEMINI_API_KEY : Gemini rédige une réponse courte **uniquement** à partir des passages,
     sans produit ni dose ; s'il juge que les passages ne répondent pas, il renvoie JE_NE_SAIS_PAS ;
   - sans clé, ou si Gemini échoue : on renvoie le passage le plus pertinent tel quel (extractif).
Rien de personnel n'est envoyé à Gemini : seulement la question et les extraits de fiches.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import threading
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
    "Écris les apostrophes normalement (c'est, l'oignon, d'abord). "
    "Utilise UNIQUEMENT les extraits de fiches fournis : n'ajoute aucune information extérieure. "
    "Ne cite jamais de produit chimique, de pesticide ni de dose ; pour un traitement, renvoie vers un agent agricole. "
    "Si les extraits ne permettent pas de répondre à la question, réponds exactement : JE_NE_SAIS_PAS"
)


class _Plafond:
    """Nombre d'appels à Gemini par jour (GEMINI_APPELS_PAR_JOUR, 500 par défaut) : /v1/chat est ouvert à
    tous, un script en boucle ne doit pas épuiser le quota. Au-delà : réponse extractive, sans Gemini.
    """

    def __init__(self):
        self.jour, self.n, self.verrou = dt.date.today(), 0, threading.Lock()

    def prendre(self) -> bool:
        limite = int(os.environ.get("GEMINI_APPELS_PAR_JOUR", "").strip() or 500)
        with self.verrou:
            if self.jour != dt.date.today():
                self.jour, self.n = dt.date.today(), 0
            if self.n >= limite:
                return False
            self.n += 1
            return True


PLAFOND = _Plafond()


# Gemini oublie parfois les apostrophes (« C est l alternariose », vu le 18 nov 2026).
# En français, une lettre seule (c, d, j, l, m, n, s, t) ou « qu » devant un mot qui commence par une
# voyelle ou un h n'existe pas : c'est une élision dont l'apostrophe manque.
_ELISION = re.compile(
    r"(?<!\d )\b([cdjlmnstCDJLMNST]|[Qq]u|[Jj]usqu|[Ll]orsqu|[Pp]uisqu) (?=[aeiouyhàâäéèêëîïôöûüAEIOUYHÀÂÉÈÊÎÔÛ])"
)


def remettre_apostrophes(texte: str) -> str:
    return _ELISION.sub(r"\1'", texte)


def gemini(consigne: str, texte: str, delai: int = 30) -> str | None:
    """Appel simple à Gemini (consigne système + un message). None sans clé, plafond atteint ou échec."""
    cle = os.environ.get("GEMINI_API_KEY", "").strip()
    if not cle:
        return None
    if not PLAFOND.prendre():
        journal.warning("plafond du jour des appels à Gemini atteint")
        return None
    modele = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"
    corps = {
        "system_instruction": {"parts": [{"text": consigne}]},
        "contents": [{"role": "user", "parts": [{"text": texte}]}],
    }
    req = urllib.request.Request(
        GEMINI.format(modele=modele),
        data=json.dumps(corps).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": cle},
    )
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            d = json.loads(r.read())
        reponse = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"]).strip()
        return remettre_apostrophes(reponse) or None
    except Exception as e:  # quota, réseau, modèle indisponible
        journal.warning("Gemini indisponible (%s)", type(e).__name__)
        return None


SUITE = (
    " Des échanges précédents peuvent être fournis : sers-t'en seulement pour comprendre de quoi parle "
    "la question (par exemple « et pour l'oignon ? » après une question sur le mildiou) ; la réponse "
    "doit toujours venir des extraits de fiches."
)


def _gemini(
    question: str, ps: list[fiches.Passage], historique: list[dict] | None = None
) -> str | None:
    extraits = "\n\n".join(f"[Fiche « {p.titre} », section « {p.section} »]\n{p.texte}" for p in ps)
    avant = ""
    if historique:
        avant = (
            "Échanges précédents :\n"
            + "\n".join(
                f"- Agriculteur : {e['question']}\n  TerraMind : {e['reponse']}" for e in historique
            )
            + "\n\n"
        )
    return gemini(
        CONSIGNE + (SUITE if historique else ""),
        f"Extraits de fiches :\n{extraits}\n\n{avant}Question : {question}",
    )


def _chercher(question: str, historique: list[dict] | None) -> list[tuple[float, fiches.Passage]]:
    """Passages de la question d'abord. Avec des échanges récents, on ajoute ceux du sujet en cours
    (questions récentes + question : « et comment l'éviter ? » après l'alternariose → la partie « éviter »
    de la fiche alternariose). Gemini voit les échanges et choisit ; une question nouvelle garde ses passages.
    """
    propres = [(s, p) for s, p in fiches.chercher(question) if s >= SCORE_MIN]
    if not historique:
        return propres
    vus = {id(p) for _, p in propres}
    sujet = [
        (s, p)
        for s, p in fiches.chercher(" ".join([e["question"] for e in historique] + [question]))
        if s >= SCORE_MIN and id(p) not in vus
    ][:2]
    vus |= {id(p) for _, p in sujet}
    dans_sujet = []
    if sujet:  # dans la fiche du sujet, les parties qui répondent à la question du moment
        dans_sujet = [
            (s, p)
            for s, p in fiches.chercher(question, n=200)
            if p.fiche == sujet[0][1].fiche and s > 0 and id(p) not in vus
        ][:2]
    return propres + sujet + dans_sujet


def repondre(question: str, historique: list[dict] | None = None) -> dict:
    """`historique` : derniers échanges de la conversation (memoire.echanges_recents), facultatif."""
    trouves = _chercher(question, historique)
    if not trouves:
        return {
            "statut": "je_ne_sais_pas",
            "texte": None,
            "passages": [],
            "sources": [],
            "mode": "aucun",
        }
    ps = [p for _, p in trouves]
    # La fiche la plus pertinente apporte aussi sa section « Prévention » : une question sur un
    # symptôme appelle presque toujours « que faire ? ».
    prevention = [
        p
        for p in fiches.passages()
        if p.fiche == ps[0].fiche
        and p.section.lower().startswith(("prévention", "que faire"))
        and p not in ps
    ]
    ps += prevention[:1]
    redige = _gemini(question, ps, historique)
    if redige and "JE_NE_SAIS_PAS" in redige:
        return {
            "statut": "je_ne_sais_pas",
            "texte": None,
            "passages": [],
            "sources": [],
            "mode": "gemini",
        }
    if redige:
        utilises, mode, texte = ps, "gemini", redige
    else:
        p = ps[0]
        utilises, mode = [p], "extractif"
        texte = f"D'après la fiche « {p.titre} » ({p.section.lower()}) :\n{p.texte}"
    return {
        "statut": "ok",
        "texte": texte,
        "mode": mode,
        "sources": fiches.sources_de(utilises),
        "passages": [
            {"fiche": p.fiche, "section": p.section, "extrait": p.texte[:300]} for p in utilises
        ],
    }
