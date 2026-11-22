"""Liste les notes vocales wolof (content/audio/wo/) pour l'application mobile.

Écrit channels/mobile/src/conversation/notes-vocales.ts : clé → extension, avec la même priorité que le bot
Telegram (m4a enregistré par un locuteur, puis ogg, puis mp3). À relancer après l'ajout d'une note vocale :
    python3 scripts/outils/lister_notes_vocales.py
"""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
AUDIO = RACINE / "content" / "audio" / "wo"
SORTIE = RACINE / "channels" / "mobile" / "src" / "conversation" / "notes-vocales.ts"
PRIORITE = ("m4a", "ogg", "mp3")


def main():
    notes: dict[str, str] = {}
    for f in sorted(AUDIO.iterdir()):
        ext = f.suffix[1:]
        if ext in PRIORITE and (f.stem not in notes or PRIORITE.index(ext) < PRIORITE.index(notes[f.stem])):
            notes[f.stem] = ext
    lignes = "\n".join(f"  '{k}': '{v}'," for k, v in sorted(notes.items()))
    SORTIE.write_text(
        "// Notes vocales wolof disponibles (content/audio/wo/), servies par le moteur sur /audio/wo/<clé>.<ext>.\n"
        "// Mêmes fichiers que ceux du bot Telegram (dire() dans engine/app/routes/telegram.py), même priorité : m4a (voix\n"
        "// d'un locuteur), puis ogg, puis mp3. Généré depuis le dossier ; à régénérer si une note est ajoutée :\n"
        "//   python3 scripts/outils/lister_notes_vocales.py\n"
        "export const NOTES_VOCALES: Record<string, 'm4a' | 'ogg' | 'mp3'> = {\n"
        f"{lignes}\n"
        "};\n",
        encoding="utf-8",
    )
    print(f"{len(notes)} notes vocales → {SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
