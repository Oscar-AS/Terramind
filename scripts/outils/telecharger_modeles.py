"""Télécharge les modèles wolof utilisés en local dans modeles/ (exclu de Git).

Usage (depuis la racine du dépôt) :
    python3 scripts/outils/telecharger_modeles.py [nom ...]

Le jeton Hugging Face est lu dans .env (HF_TOKEN) et n'est jamais affiché. Les modèles
« sur demande » exigent d'avoir accepté leurs conditions sur leur page Hugging Face avec
le compte du jeton (voir docs/voix-wolof.md § 7 bis).

Choix (4 nov 2026, environ 8,8 Go) : voir MODELES. Non téléchargés volontairement :
- AIHubSN/Kiriku-Wolof-ASR : version plus ancienne de M-Kiriku-ASR (6,2 Go de plus) ;
- galsenai/xTTS-v2-wolof : poids sur Google Drive (plus de 7 Go), à prendre seulement si
  Kiriku-Wolof-TTS et SpeechT5 ne suffisent pas au test d'écoute.
"""

import sys
from pathlib import Path

from huggingface_hub import snapshot_download

RACINE = Path(__file__).resolve().parents[2]
DOSSIER = RACINE / "modeles"

MODELES = {
    "asr": (
        "AIHubSN/M-Kiriku-ASR",
        "Reconnaissance du wolof parlé (Whisper large-v3 ajusté), Apache 2.0, 6,2 Go",
    ),
    "asr-leger": (
        "dofbi/wolof-asr",
        "Reconnaissance légère, MIT, 1 Go (serveur sans carte graphique)",
    ),
    "voix": (
        "AIHubSN/Kiriku-Wolof-TTS",
        "Voix wolof principale à tester, 1 Go, licence non indiquée",
    ),
    "voix-secours": ("bilalfaye/speecht5_tts-wolof-v0.2", "Voix wolof de secours, MIT, 0,6 Go"),
}


def jeton():
    for ligne in (RACINE / ".env").read_text(encoding="utf-8").splitlines():
        if ligne.startswith("HF_TOKEN="):
            valeur = ligne.split("=", 1)[1].strip().strip('"')
            if valeur:
                return valeur
    raise SystemExit("HF_TOKEN absent de .env")


if __name__ == "__main__":
    choix = sys.argv[1:] or list(MODELES)
    t = jeton()
    for nom in choix:
        depot, role = MODELES[nom]
        cible = DOSSIER / depot.replace("/", "__")
        print(f"{nom} : {depot} ({role})")
        snapshot_download(
            depot,
            local_dir=cible,
            token=t,
            allow_patterns=["*.json", "*.txt", "*.model", "*.safetensors", "*.pth", "*.md"],
        )
        print(f"  ok  {cible.relative_to(RACINE)}")
