"""Prépare, une fois pour toutes, la réponse à la question wolof de la démonstration.

Pendant la démo, Octopus (voix wolof) tombe souvent en panne. La question de démonstration est connue d'avance
(guide de test, fiche page 4) : « Naka laa mënë moytu mildiyu ci sama tamaate ? » (« Comment puis-je éviter le
mildiou sur ma tomate ? »). Ce script fait maintenant ce que le moteur ferait en direct :
  1. la réponse tirée des fiches (RAG + Gemini, D8), avec ses sources ;
  2. sa traduction en wolof et sa voix (Octopus), avec plusieurs essais si Octopus échoue.
Il écrit content/audio/wo/<clé>.mp3 et content/voix/reponses_preparees.json. Le moteur s'en sert seulement si
la question comprise est bien celle-là (engine/app/modules/reponses_preparees.py) ; sinon, chemin habituel.

Usage (clés GEMINI_* et OCTOPUS_* dans .env) :
    python3 scripts/outils/preparer_reponse_demo.py
Écouter ensuite le MP3 avant la démo (un locuteur doit le valider, comme les autres notes vocales).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from engine.app.modules import parole  # noqa: E402
from engine.app.modules.rag.reponse import repondre  # noqa: E402

CLE = "reponse_preparee_mildiou_tomate"
QUESTION_WO = "Naka laa mënë moytu mildiyu ci sama tamaate ?"
QUESTION_FR = "Comment puis-je éviter le mildiou sur ma tomate ?"
SORTIE_JSON = RACINE / "content" / "voix" / "reponses_preparees.json"
SORTIE_MP3 = RACINE / "content" / "audio" / "wo" / f"{CLE}.mp3"


def avec_essais(fonction, nom: str, essais: int = 5):
    for i in range(1, essais + 1):
        r = fonction()
        if r:
            return r
        print(f"{nom} : essai {i} sans résultat, nouvel essai dans {5 * i} s")
        time.sleep(5 * i)
    raise SystemExit(f"{nom} : échec après {essais} essais")


def main():
    # Réponse rédigée par Gemini (mode « gemini »), comme en direct ; pas un passage de fiche brut.
    r = avec_essais(lambda: (lambda x: x if x["statut"] == "ok" and x["mode"] == "gemini" else None)(repondre(QUESTION_FR)), "réponse des fiches")
    texte_fr = r["texte"].replace("**", "")
    # Traduction et voix pas à pas (comme parole.dire_en_wolof_detail), mais sans écarter la voix quand le contrôle
    # signale un mot à risque : ici, un locuteur écoute le MP3 avant la démo, ce qui est impossible en direct.
    # Tant qu'il ne l'a pas validé (« voix_validee » à false), le moteur n'envoie que le texte préparé.
    texte_wo = avec_essais(lambda: parole.traduire_en_wolof(texte_fr), "traduction wolof (Gemini)")
    pret = parole.preparer(texte_wo)
    mp3 = avec_essais(lambda: _synthese(" ".join(pret.morceaux)), "voix wolof (Octopus)")
    SORTIE_MP3.write_bytes(mp3)
    donnees = {
        CLE: {
            "question_wo": QUESTION_WO,
            "question_fr": QUESTION_FR,
            "texte_fr": texte_fr,
            "texte_wo": texte_wo,
            "sources": r["sources"],
            "audio": SORTIE_MP3.name,
            "points_a_ecouter": pret.problemes,
            "voix_validee": False,
            "prepare_le": time.strftime("%Y-%m-%d"),
        }
    }
    SORTIE_JSON.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Réponse : {texte_fr}\n\nWolof : {texte_wo}\n\nÀ écouter : {pret.problemes}")
    print(f"MP3 : {SORTIE_MP3.relative_to(RACINE)} ({len(mp3) // 1024} Ko)")


def _synthese(texte: str) -> bytes | None:
    try:
        return parole.synthetiser(texte)
    except Exception as e:  # Octopus indisponible : on réessaie
        print(f"Octopus : {type(e).__name__}")
        return None


if __name__ == "__main__":
    main()
