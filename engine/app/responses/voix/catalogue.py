"""Phrases wolof relues (content/voix/messages_wolof.csv) et leurs notes vocales (content/audio/wo/).

Utilisé par les réponses /v1 quand l'application demande `langue: "wo"` : la phrase wolof relue par un
locuteur, son texte français, et l'adresse de la note vocale servie par le moteur (/audio/wo/<clé>.mp3).
Seules les phrases au statut « relu » sont proposées (D10 : aucune voix non relue devant un agriculteur).
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parents[4]
CATALOGUE = RACINE / "content" / "voix" / "messages_wolof.csv"
AUDIO_WO = RACINE / "content" / "audio" / "wo"
PREFIXE_AUDIO = "/audio/wo/"


@lru_cache(maxsize=1)
def _phrases() -> dict[str, dict]:
    if not CATALOGUE.exists():
        return {}
    with CATALOGUE.open(encoding="utf-8") as f:
        return {
            l["cle"]: l
            for l in csv.DictReader(f)
            if l["statut"] == "relu" and l["texte_wo"].strip()
        }


def phrase(cle: str) -> dict | None:
    """{cle, texte_wo, texte_fr, audio_url} ; audio_url vaut None si la note vocale n'existe pas."""
    l = _phrases().get(cle)
    if not l:
        return None
    audio = AUDIO_WO / f"{cle}.mp3"
    return {
        "cle": cle,
        "texte_wo": l["texte_wo"],
        "texte_fr": l["texte_fr"],
        "audio_url": PREFIXE_AUDIO + audio.name if audio.exists() else None,
    }


def phrases(*cles: str) -> list[dict]:
    """Les phrases existantes, dans l'ordre, sans les clés absentes du catalogue relu."""
    return [p for p in (phrase(c) for c in cles) if p]
