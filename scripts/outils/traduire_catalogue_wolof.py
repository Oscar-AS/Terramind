"""Brouillons de traduction wolof du catalogue vocal (content/voix/messages_wolof.csv), par Gemini (D9).

Ne remplit que les lignes sans texte wolof ; statut « brouillon_gemini ». Un locuteur doit relire
chaque ligne (statut « relu », colonne relu_par) avant qu'elle soit enregistrée ou synthétisée.
Le lexique sourcé (content/voix/lexique_wolof.csv) est imposé à Gemini pour les mots du métier.
Seuls les textes français du catalogue sont envoyés à Gemini (aucune donnée personnelle).

    .venv/bin/python scripts/outils/traduire_catalogue_wolof.py
"""

import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from engine.app import config  # noqa: E402,F401  (charge .env)

CATALOGUE = RACINE / "content" / "voix" / "messages_wolof.csv"
LEXIQUE = RACINE / "content" / "voix" / "lexique_wolof.csv"
GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
CONSIGNE = (
    "Tu traduis en wolof du Sénégal (alphabet latin officiel, orthographe du CLAD) des messages qu'un assistant "
    "agricole dira à voix haute à des maraîchers des Niayes, souvent non lettrés. Wolof parlé de tous les jours, "
    "simple et chaleureux, tutoiement. Phrases courtes. Aucun chiffre ni symbole : nombres en toutes lettres. "
    "Garde le sens exact, n'ajoute ni n'enlève aucune information, et ne cite aucun produit chimique. "
    "Pour les mots du glossaire, utilise obligatoirement la forme wolof donnée. Pour un nom de maladie sans "
    "équivalent wolof courant, garde le nom français. Réponds uniquement en JSON : "
    '{"traductions": [{"cle": "...", "texte_wo": "..."}]}'
)


def glossaire() -> str:
    lignes = []
    with LEXIQUE.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["type"] == "mot" and r["a_dire_en_wolof"].strip():
                lignes.append(f"{r['ecrit']} = {r['a_dire_en_wolof'].strip()}")
    return "\n".join(lignes)


def gemini(lot: list[dict]) -> dict[str, str]:
    cle = os.environ.get("GEMINI_API_KEY", "").strip()
    modele = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"
    demande = f"Glossaire :\n{glossaire()}\n\nMessages à traduire :\n" + json.dumps(
        [{"cle": r["cle"], "texte_fr": r["texte_fr"]} for r in lot], ensure_ascii=False
    )
    corps = {
        "system_instruction": {"parts": [{"text": CONSIGNE}]},
        "contents": [{"role": "user", "parts": [{"text": demande}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    req = urllib.request.Request(
        GEMINI.format(modele=modele),
        data=json.dumps(corps).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": cle},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    texte = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
    return {t["cle"]: t["texte_wo"].strip() for t in json.loads(texte)["traductions"]}


def main():
    with CATALOGUE.open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
        champs = list(lignes[0].keys())
    a_faire = [r for r in lignes if not r["texte_wo"].strip()]
    print(f"{len(a_faire)} messages à traduire")
    for i in range(0, len(a_faire), 15):
        lot = a_faire[i : i + 15]
        trad = gemini(lot)
        for r in lot:
            if trad.get(r["cle"]):
                r["texte_wo"], r["statut"] = trad[r["cle"]], "brouillon_gemini"
        print(
            f"  lot {i // 15 + 1} : {sum(1 for r in lot if r['statut'] == 'brouillon_gemini')}/{len(lot)}"
        )
    with CATALOGUE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, lineterminator="\n")
        w.writeheader()
        w.writerows(lignes)


if __name__ == "__main__":
    main()
