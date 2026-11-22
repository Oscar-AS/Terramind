"""Trouver la graphie qu'Octopus prononce bien pour un mot wolof qu'il déforme.

Pour chaque graphie candidate : Octopus dit une vraie phrase wolof qui contient le mot, puis Octopus retranscrit
l'audio ; on note à quel point la transcription retrouve le mot attendu (0 à 1, meilleur passage). Les MP3 sont
gardés pour l'écoute d'un locuteur, qui a le dernier mot (le score n'est qu'un premier tri). La graphie retenue
va dans content/voix/prononciation_voix.csv (colonnes ecrit, dit_a_la_voix, raison).

Usage (clés OCTOPUS_* dans .env) :
    python3 scripts/outils/essayer_graphies.py pombiteer "Bul jëmbët tamaate ci wetu {}." pombiteer pombitéer ...
"""

from __future__ import annotations

import difflib
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from engine.app.modules import ecoute, parole  # noqa: E402

SORTIE = Path("/tmp/tm-graphies")


def simple(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if c.isalnum() or c == " " and not unicodedata.combining(c))


def score(attendu: str, transcription: str) -> float:
    """Meilleure ressemblance entre le mot attendu et un passage de la transcription (même nombre de mots, ±1)."""
    mots, cible = simple(transcription).split(), simple(attendu)
    meilleur = 0.0
    for n in (1, 2, 3):
        for i in range(len(mots) - n + 1):
            meilleur = max(meilleur, difflib.SequenceMatcher(None, cible, "".join(mots[i:i + n])).ratio())
    return meilleur


def main():
    attendu, phrase, *graphies = sys.argv[1:]
    SORTIE.mkdir(exist_ok=True)
    resultats = []
    for g in graphies:
        texte = phrase.format(g)
        try:
            # On envoie la phrase telle quelle : la graphie testée ne doit pas être réécrite par la table actuelle.
            audio = parole.synthetiser_brut(texte) if hasattr(parole, "synthetiser_brut") else parole.synthetiser(texte)
            transcription = ecoute.transcrire(audio, "audio/mpeg", 8)
        except Exception as e:
            print(f"{g:20} échec : {type(e).__name__} {e}")
            continue
        fichier = SORTIE / f"{attendu}__{g.replace(' ', '_')}.mp3"
        fichier.write_bytes(audio)
        s = score(attendu, transcription)
        resultats.append((s, g, transcription, fichier))
        print(f"{g:20} score {s:.2f}  entendu : « {transcription} »")
    print("\nClassement :")
    for s, g, t, f in sorted(resultats, reverse=True):
        print(f"  {s:.2f}  {g:20} {f}")


if __name__ == "__main__":
    main()
