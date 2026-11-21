"""Réponses préparées à l'avance pour la question wolof de la démonstration.

Octopus (voix wolof) tombe souvent en panne. La question de démonstration est connue d'avance (guide de test) :
« Naka laa mënë moytu mildiyu ci sama tamaate ? » (« Comment puis-je éviter le mildiou sur ma tomate ? »).
Sa réponse (texte tiré des fiches + voix wolof) a été préparée par scripts/outils/preparer_reponse_demo.py et
rangée dans content/voix/reponses_preparees.json.

Elle n'est utilisée QUE si la question comprise est bien celle-là : les trois idées doivent y être (éviter ou
protéger, mildiou, tomate), dans la transcription wolof d'Octopus ou dans sa traduction française. Sinon, chemin
habituel. La voix préparée n'est envoyée que si un locuteur l'a validée (« voix_validee », règle D10) ; sinon,
seulement le texte. La transcription (Octopus) reste nécessaire : il faut entendre la question pour la reconnaître.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
FICHIER = RACINE / "content" / "voix" / "reponses_preparees.json"

# Les trois idées de la question, en wolof (transcription) et en français (traduction). Racines sans accents.
IDEES = {
    "reponse_preparee_mildiou_tomate": (
        ("moytu", "moyto", "moytou", "eviter", "evite", "prevenir", "proteger", "empecher", "lutter", "bañ", "ban a am"),
        ("mildiyu", "mildiou", "mildiu", "mildew"),
        ("tamaate", "tamate", "tomate", "tomato"),
    ),
}


def _simple(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in sans_accents if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def _reponses() -> dict:
    if not FICHIER.exists():
        return {}
    return json.loads(FICHIER.read_text(encoding="utf-8"))


def trouver(compris: dict) -> dict | None:
    """La réponse préparée si la question comprise ({"wolof", "francais"}) est celle de la démo, sinon None."""
    for cle, idees in IDEES.items():
        reponse = _reponses().get(cle)
        if not reponse:
            continue
        for texte in (compris.get("wolof"), compris.get("francais")):
            t = _simple(texte or "")
            if t and all(any(_simple(mot) in t for mot in idee) for idee in idees):
                return {"cle": cle, **reponse}
    return None


def adresse_voix(reponse: dict) -> str | None:
    """Adresse de la voix préparée (servie sur /audio/wo/), seulement si un locuteur l'a validée."""
    if not reponse.get("voix_validee") or not (RACINE / "content" / "audio" / "wo" / reponse["audio"]).exists():
        return None
    return f"/audio/wo/{reponse['audio']}"
