"""Génère les notes vocales wolof du bot avec la voix de synthèse d'Octopus (plateforme du PAS Challenge).

Lit content/voix/messages_wolof.csv et écrit content/audio/wo/<cle>.mp3 (le bot accepte OGG, MP3, M4A).
Par défaut, seules les phrases relues par un locuteur (statut « relu ») sont générées. Une phrase
déjà générée n'est pas refaite, sauf avec --forcer ; une phrase dont le texte wolof a changé depuis la
dernière génération est refaite automatiquement (empreinte gardée dans content/audio/wo/generes.csv).

Coût : environ 0,02 $ par phrase (grille publique d'Octopus), sur le projet sponsorisé de l'équipe.
Jeton : OCTOPUS_API_KEY (.env) ou, à défaut, celui du CLI octopus (~/.octopus/config.json).

    python3 scripts/outils/generer_audios_wolof.py                 # phrases relues seulement
    python3 scripts/outils/generer_audios_wolof.py --brouillons    # aussi les brouillons (tests internes)
    python3 scripts/outils/generer_audios_wolof.py --cle accueil   # une seule phrase
    python3 scripts/outils/generer_audios_wolof.py --essai         # liste sans rien dépenser
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from engine.app import config  # noqa: E402  (charge .env)

CATALOGUE = RACINE / "content" / "voix" / "messages_wolof.csv"
SORTIE = RACINE / "content" / "audio" / "wo"
JOURNAL = SORTIE / "generes.csv"
PRIX_PHRASE = 0.02
AGENT = "TerraMind-outils/0.2"  # le pare-feu d'Octopus refuse l'agent par défaut de Python


def jeton() -> str:
    if config.OCTOPUS_API_KEY:
        return config.OCTOPUS_API_KEY
    cli = Path.home() / ".octopus" / "config.json"
    if cli.exists():
        return (json.loads(cli.read_text()).get("token") or "").strip()
    return ""


def empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode()).hexdigest()[:16]


def synthetiser(texte: str, cle_api: str) -> bytes:
    corps = json.dumps({"text": texte, "language": "wo",
                        "project_id": config.OCTOPUS_PROJECT_ID or "proj-challenge-f0903409d71542feaa95"}).encode()
    entetes = {"Authorization": f"Bearer {cle_api}", "User-Agent": AGENT}
    req = urllib.request.Request(f"{config.OCTOPUS_URL}/api/tts", data=corps,
                                 headers={**entetes, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        url = json.loads(r.read())["url"]
    if url.startswith("/"):
        url = config.OCTOPUS_URL + url
    with urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=120) as r:
        return r.read()


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--brouillons", action="store_true", help="générer aussi les phrases non relues")
    a.add_argument("--cle", action="append", help="seulement cette clé (répétable)")
    a.add_argument("--forcer", action="store_true", help="refaire même si l'audio existe")
    a.add_argument("--essai", action="store_true", help="afficher ce qui serait généré, sans appel")
    args = a.parse_args()

    statuts = {"relu"} | ({"brouillon_gemini"} if args.brouillons else set())
    lignes = list(csv.DictReader(CATALOGUE.open(encoding="utf-8")))
    deja = {}
    if JOURNAL.exists():
        deja = {r["cle"]: r for r in csv.DictReader(JOURNAL.open(encoding="utf-8"))}

    a_faire = []
    for l in lignes:
        if args.cle and l["cle"] not in args.cle:
            continue
        if l["statut"] not in statuts or not l["texte_wo"].strip():
            continue
        existe = any((SORTIE / f"{l['cle']}.{x}").exists() for x in ("ogg", "mp3", "m4a"))
        meme_texte = deja.get(l["cle"], {}).get("empreinte") == empreinte(l["texte_wo"])
        if existe and meme_texte and not args.forcer:
            continue
        a_faire.append(l)

    print(f"{len(a_faire)} phrase(s) à générer, environ {len(a_faire) * PRIX_PHRASE:.2f} $")
    if args.essai or not a_faire:
        for l in a_faire:
            print(f"  {l['cle']} ({l['statut']})")
        return
    cle_api = jeton()
    if not cle_api:
        sys.exit("Aucun jeton Octopus : remplir OCTOPUS_API_KEY dans .env ou lancer `octopus login`.")

    SORTIE.mkdir(parents=True, exist_ok=True)
    for i, l in enumerate(a_faire, 1):
        try:
            audio = synthetiser(l["texte_wo"], cle_api)
        except Exception as e:
            print(f"  [{i}/{len(a_faire)}] {l['cle']} : échec ({type(e).__name__} {getattr(e, 'code', '')})")
            continue
        for x in ("ogg", "m4a"):  # un seul fichier par clé : le bot prend le premier trouvé
            (SORTIE / f"{l['cle']}.{x}").unlink(missing_ok=True)
        (SORTIE / f"{l['cle']}.mp3").write_bytes(audio)
        deja[l["cle"]] = {"cle": l["cle"], "statut_texte": l["statut"], "empreinte": empreinte(l["texte_wo"]),
                          "octets": str(len(audio))}
        print(f"  [{i}/{len(a_faire)}] {l['cle']} : {len(audio) // 1024} Ko")
        with JOURNAL.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["cle", "statut_texte", "empreinte", "octets"], lineterminator="\n")
            w.writeheader()
            w.writerows(sorted(deja.values(), key=lambda r: r["cle"]))


if __name__ == "__main__":
    os.chdir(RACINE)
    main()
