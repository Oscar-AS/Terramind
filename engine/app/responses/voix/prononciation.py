"""Prononciation de la voix wolof d'Octopus : l'écran garde l'orthographe correcte (CLAD), la voix reçoit
une graphie qu'elle prononce bien.

La voix lit certaines lettres à la française (« tool » dit « toul »). La table content/voix/prononciation_voix.csv
(colonnes ecrit, dit_a_la_voix, raison) donne, mot par mot, la graphie à envoyer à Octopus ; chaque ligne est
choisie par un locuteur après écoute. Utilisé pour les notes préparées (scripts/outils/generer_audios_wolof.py)
et pour les réponses dites en direct (engine/app/modules/parole.py).
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

TABLE = Path(__file__).resolve().parents[4] / "content" / "voix" / "prononciation_voix.csv"


@lru_cache(maxsize=1)
def _table() -> list[tuple[re.Pattern, str]]:
    if not TABLE.exists():
        return []
    with TABLE.open(encoding="utf-8") as f:
        lignes = [l for l in csv.DictReader(f) if l["ecrit"].strip() and l["dit_a_la_voix"].strip()]
    # Les expressions les plus longues d'abord ; mot entier seulement, sans tenir compte des majuscules.
    lignes.sort(key=lambda l: -len(l["ecrit"]))
    return [
        (
            re.compile(rf"(?<!\w){re.escape(l['ecrit'].strip())}(?!\w)", re.IGNORECASE),
            l["dit_a_la_voix"].strip(),
        )
        for l in lignes
    ]


def _meme_casse(modele: str, mot: str) -> str:
    return mot[:1].upper() + mot[1:] if modele[:1].isupper() else mot


def pour_la_voix(texte_wo: str) -> str:
    """Le texte wolof tel qu'il doit être envoyé à la voix d'Octopus."""
    for motif, dit in _table():
        texte_wo = motif.sub(lambda m, dit=dit: _meme_casse(m.group(0), dit), texte_wo)
    return texte_wo
