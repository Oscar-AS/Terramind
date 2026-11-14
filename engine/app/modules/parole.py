"""Faire dire au bot, en wolof et à voix haute, une réponse rédigée en français (réponses libres du RAG).

Les phrases fixes du bot sont des audios préparés à l'avance (content/audio/wo/). Les réponses aux
questions libres, elles, changent à chaque fois : on les traduit en wolof avec Gemini (lexique sourcé
imposé, comme pour le catalogue, D9), puis la voix de synthèse d'Octopus les lit (D10).
Ces traductions ne sont pas relues par un locuteur : le texte français reste toujours envoyé dessous.

Coût : environ 0,02 $ par réponse dite (grille d'Octopus) ; plafond OCTOPUS_REPONSES_VOCALES_PAR_JOUR.
Rien n'est conservé : ni le texte wolof, ni l'audio.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import threading
import urllib.request
from functools import lru_cache
from pathlib import Path

from .. import config

journal = logging.getLogger("terramind.parole")
LEXIQUE = Path(__file__).resolve().parents[3] / "content" / "voix" / "lexique_wolof.csv"
AGENT = "TerraMind-moteur/0.2"  # le pare-feu d'Octopus refuse l'agent par défaut de Python
CONSIGNE = (
    "Tu traduis en wolof du Sénégal (alphabet latin officiel, orthographe du CLAD) la réponse qu'un assistant "
    "agricole va dire à voix haute à un maraîcher des Niayes, souvent non lettré. Wolof parlé de tous les jours, "
    "simple et chaleureux, tutoiement. Phrases courtes. Aucun chiffre ni symbole : nombres en toutes lettres. "
    "Garde le sens exact, n'ajoute ni n'enlève aucune information, et ne cite aucun produit chimique. "
    "Pour les mots du glossaire, utilise obligatoirement la forme wolof donnée. Pour un nom de maladie sans "
    "équivalent wolof courant, garde le nom français. Réponds uniquement par le texte wolof."
)


class _Compteur:
    def __init__(self):
        self.jour, self.n, self.verrou = dt.date.today(), 0, threading.Lock()

    def prendre(self) -> bool:
        with self.verrou:
            if self.jour != dt.date.today():
                self.jour, self.n = dt.date.today(), 0
            if self.n >= config.OCTOPUS_REPONSES_VOCALES_PAR_JOUR:
                return False
            self.n += 1
            return True


COMPTEUR = _Compteur()


@lru_cache(maxsize=1)
def glossaire() -> str:
    if not LEXIQUE.exists():
        return ""
    with LEXIQUE.open(encoding="utf-8") as f:
        return "\n".join(f"{r['ecrit']} = {r['a_dire_en_wolof'].strip()}" for r in csv.DictReader(f)
                         if r["type"] == "mot" and r["a_dire_en_wolof"].strip())


def traduire_en_wolof(texte_fr: str) -> str | None:
    from .rag.reponse import gemini

    wo = gemini(CONSIGNE, f"Glossaire :\n{glossaire()}\n\nRéponse à traduire :\n{texte_fr}", delai=30)
    return wo.strip() if wo else None


def synthetiser(texte_wo: str) -> bytes:
    """Voix wolof d'Octopus (MP3)."""
    entetes = {"Authorization": f"Bearer {config.OCTOPUS_API_KEY}", "User-Agent": AGENT}
    corps = json.dumps({"text": texte_wo, "language": "wo", "project_id": config.OCTOPUS_PROJECT_ID}).encode()
    req = urllib.request.Request(f"{config.OCTOPUS_URL}/api/tts", data=corps,
                                 headers={**entetes, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        url = json.loads(r.read())["url"]
    if url.startswith("/"):
        url = config.OCTOPUS_URL + url
    with urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=60) as r:
        return r.read()


def dire_en_wolof(texte_fr: str) -> bytes | None:
    """Audio wolof de la réponse, ou None (Octopus non configuré, plafond atteint, échec)."""
    if not (config.OCTOPUS_API_KEY and config.OCTOPUS_PROJECT_ID) or not texte_fr.strip():
        return None
    if not COMPTEUR.prendre():
        journal.info("plafond du jour des réponses vocales atteint")
        return None
    try:
        wo = traduire_en_wolof(texte_fr)
        return synthetiser(wo) if wo else None
    except Exception as e:
        journal.warning("réponse vocale wolof impossible : %s", type(e).__name__)
        return None
