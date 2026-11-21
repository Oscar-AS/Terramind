"""Remplacer une note vocale enregistrée par la voix d'Octopus, au plus près de la prononciation d'un locuteur.

Plusieurs prises d'Octopus pour la phrase (graphie de content/voix/prononciation_voix.csv appliquée), chacune
retranscrite par Octopus et comparée à la transcription de l'enregistrement du locuteur (référence). La meilleure
prise est écrite dans /tmp/tm-revoix/<clé>.mp3, pour écoute avant de remplacer la note.

Usage : python3 scripts/outils/revoix_octopus.py position_recue content/voix/enregistrements/salam_position_recue.m4a 3
"""

from __future__ import annotations

import csv
import difflib
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from engine.app.modules import ecoute, parole  # noqa: E402

SORTIE = Path("/tmp/tm-revoix")


def simple(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return " ".join("".join(c for c in t if c.isalnum() or c == " ").split())


def main():
    cle, reference, prises = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3] if len(sys.argv) > 3 else 3)
    texte = next(l["texte_wo"] for l in csv.DictReader(open(RACINE / "content/voix/messages_wolof.csv")) if l["cle"] == cle)
    attendu = ecoute.transcrire(reference.read_bytes(), "audio/mp4", 5)
    print(f"Texte : {texte}\nVoix du locuteur, retranscrite : « {attendu} »\nEnvoyé à Octopus : « {parole.pour_la_voix(texte)} »\n")
    SORTIE.mkdir(exist_ok=True)
    meilleure = None
    for i in range(1, prises + 1):
        try:
            audio = parole.synthetiser(texte)
            entendu = ecoute.transcrire(audio, "audio/mpeg", 5)
        except Exception as e:
            print(f"prise {i} : échec ({type(e).__name__})")
            continue
        score = difflib.SequenceMatcher(None, simple(attendu), simple(entendu)).ratio()
        (SORTIE / f"{cle}_prise{i}.mp3").write_bytes(audio)
        print(f"prise {i} : {score:.2f}  « {entendu} »")
        if not meilleure or score > meilleure[0]:
            meilleure = (score, i, audio)
    if meilleure:
        (SORTIE / f"{cle}.mp3").write_bytes(meilleure[2])
        print(f"\nRetenue : prise {meilleure[1]} ({meilleure[0]:.2f}) → {SORTIE / (cle + '.mp3')}")


if __name__ == "__main__":
    main()
