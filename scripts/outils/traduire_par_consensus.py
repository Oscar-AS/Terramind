"""Traduction français → wolof par concordance de plusieurs systèmes (demande de Salam, 14 nov 2026).

Processus, pour chaque phrase du catalogue (content/voix/messages_wolof.csv) :
1. trois systèmes la traduisent en wolof : Gemini, NLLB-200 de Meta (facebook/nllb-200-distilled-600M, en
   local) et Teranga-Wolof-4B-MT en local (llama.cpp, `llama-server`). Google Traduction était prévu à la place
   de NLLB, abandonné le 14 nov 2026 (carte refusée par Google Cloud) ;
2. chaque version wolof est retraduite en français par un AUTRE système que celui qui l'a écrite ;
3. un juge (Qwen3-4B en local, Gemini avant le 14 nov 2026) compare chaque retraduction à la phrase de départ : même sens, rien d'ajouté ni
   d'enlevé ? ;
4. on mesure la ressemblance des trois versions wolof entre elles (chrF, Popović 2015) ;
5. la phrase est validée (statut « valide_concordance ») seulement si les trois systèmes ont répondu,
   si les trois retraductions gardent le sens et si les versions wolof se ressemblent assez
   (chrF ≥ SEUIL_CHRF pour chaque paire). On garde alors la version la plus proche des deux autres.
   Sinon : statut « a_relire » avec la raison, pour le locuteur.

Aucun système n'est « certifié » pour le wolof : la concordance réduit le nombre de phrases à relire,
elle ne remplace pas un locuteur pour les phrases signalées. Tous les candidats et contrôles sont
gardés dans content/voix/traductions_concordance.csv (transparence, relecture).

Configuration (.env) : GEMINI_API_KEY ; NLLB_MODELE (défaut facebook/nllb-200-distilled-600M, téléchargé une fois) ;
TERANGA_URL (défaut http://127.0.0.1:8090, serveur `llama-server -m Teranga-Wolof-4B-MT-Q4_K_M.gguf`) ;
JUGE_URL (défaut http://127.0.0.1:8091, serveur
`llama-server -m modeles/juge/Qwen3-4B-Instruct-2507-Q4_K_M.gguf --port 8091 -c 4096 -ngl 99`).

Depuis le 14 nov 2026 (quota gratuit Gemini de 500 demandes/jour épuisé, partagé avec le bot) : Gemini ne sert
plus qu'à proposer sa traduction (1 appel par phrase) ; retraductions par NLLB et Teranga, juge local (Qwen3-4B).
Si le quota est épuisé, le script attend sa remise à zéro (8 h UTC) puis continue.

    .venv/bin/python scripts/outils/traduire_par_consensus.py --essai      # quels systèmes répondent
    .venv/bin/python scripts/outils/traduire_par_consensus.py              # tout le catalogue
    .venv/bin/python scripts/outils/traduire_par_consensus.py --cle accueil
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from engine.app import config  # noqa: E402,F401  (charge .env)
from engine.app.modules.parole import CONSIGNE as CONSIGNE_WO, glossaire  # noqa: E402
from engine.app.modules.rag.reponse import gemini as _gemini  # noqa: E402
import time  # noqa: E402


def appel_gemini(consigne: str, texte: str) -> str | None:
    """Gemini avec 4 essais espacés (surcharge ou trop de demandes : erreurs passagères)."""
    for attente in (0, 5, 15, 40):
        time.sleep(attente)
        r = _gemini(consigne, texte, delai=60)
        if r:
            return r
    # Quota épuisé ou panne : on s'arrête plutôt que de marquer des phrases « à relire » à tort.
    raise GeminiIndisponible


class GeminiIndisponible(Exception):
    """Gemini ne répond plus (souvent le quota gratuit journalier : 500 demandes)."""

CATALOGUE = RACINE / "content" / "voix" / "messages_wolof.csv"
DETAIL = RACINE / "content" / "voix" / "traductions_concordance.csv"
SEUIL_CHRF = 50.0  # ressemblance minimale entre deux versions wolof (0-100), à ajuster après le premier passage
SYSTEMES = ("gemini", "nllb", "teranga")
# Qui retraduit la version de qui (jamais le même système). Depuis le 14 nov 2026, seuls les modèles locaux
# retraduisent (quota gratuit Gemini : 500 demandes/jour, partagé avec le bot) ; Teranga est le meilleur en
# wolof → français (FLORES chrF++ 40,6, fiche du modèle), il retraduit Gemini et NLLB.
RETRADUCTEUR = {"gemini": "teranga", "nllb": "teranga", "teranga": "nllb"}
CONSIGNE_FR = "Traduis ce texte wolof en français, fidèlement, sans rien ajouter. Réponds uniquement par la traduction."
CONSIGNE_JUGE = (
    "Tu compares deux phrases françaises : A est le message d'origine, B est une retraduction depuis le wolof. "
    "Réponds en JSON {\"fidele\": true|false, \"raison\": \"...\"}. fidele = true seulement si B a le même sens "
    "que A, sans information ajoutée, enlevée ou changée (un mot différent mais de même sens est accepté)."
)


# --- systèmes -------------------------------------------------------------------------------------
def gemini_vers(texte: str, cible: str) -> str | None:
    if cible == "wo":
        return appel_gemini(CONSIGNE_WO, f"Glossaire :\n{glossaire()}\n\nRéponse à traduire :\n{texte}")
    return appel_gemini(CONSIGNE_FR, texte)


_NLLB = {}


def nllb_vers(texte: str, cible: str) -> str | None:
    """NLLB-200 (Meta, CC BY-NC 4.0, usage non commercial) : codes FLORES fra_Latn et wol_Latn."""
    if not _NLLB:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        nom = os.environ.get("NLLB_MODELE", "facebook/nllb-200-distilled-600M")
        _NLLB["tok"] = AutoTokenizer.from_pretrained(nom)
        _NLLB["mod"] = AutoModelForSeq2SeqLM.from_pretrained(nom).eval()
    tok, mod = _NLLB["tok"], _NLLB["mod"]
    tok.src_lang = "fra_Latn" if cible == "wo" else "wol_Latn"
    entree = tok(texte, return_tensors="pt", truncation=True, max_length=400)
    sortie = mod.generate(**entree, forced_bos_token_id=tok.convert_tokens_to_ids("wol_Latn" if cible == "wo" else "fra_Latn"),
                          max_new_tokens=400, num_beams=4)
    return tok.batch_decode(sortie, skip_special_tokens=True)[0].strip()


def teranga_vers(texte: str, cible: str) -> str | None:
    """Teranga-Wolof-4B-MT servi par `llama-server` ; gabarit ChatML avec la réflexion coupée (<think></think>
    vide), comme à l'entraînement (Modelfile du modèle) ; consigne de la fiche du modèle : « Traduis en wolof : … »."""
    url = os.environ.get("TERANGA_URL", "http://127.0.0.1:8090").rstrip("/")
    consigne = "Traduis en wolof : " if cible == "wo" else "Traduis en français : "
    invite = (f"<|im_start|>user\n{consigne}{texte}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n")
    corps = json.dumps({"prompt": invite, "temperature": 0, "repeat_penalty": 1.05, "n_predict": 400,
                        "stop": ["<|im_end|>", "<|im_start|>"]}).encode()
    req = urllib.request.Request(f"{url}/completion", data=corps, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())["content"].strip()
    except OSError:
        return None


TRADUIRE = {"gemini": gemini_vers, "nllb": nllb_vers, "teranga": teranga_vers}


def traduire(systeme: str, texte: str, cible: str) -> str | None:
    try:
        r = TRADUIRE[systeme](texte, cible)
        return r.strip() if r else None
    except GeminiIndisponible:
        raise  # remonte jusqu'à main(), qui attend la remise à zéro du quota
    except Exception as e:
        print(f"    {systeme} : échec ({type(e).__name__})")
        return None


# --- contrôles ------------------------------------------------------------------------------------
def chrf(a: str, b: str, n_max: int = 6, beta: float = 2.0) -> float:
    """chrF (Popović 2015) sur les caractères, espaces, ponctuation et accents retirés (« dégg » = « degg » : variantes
    d'écriture, pas un désaccord), moyenne des n-grammes 1 à 6, symétrisé."""
    def ngrammes(t, n):
        t = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if not unicodedata.combining(c))
        t = "".join(c for c in t if c.isalnum())  # ni espaces ni ponctuation
        return Counter(t[i:i + n] for i in range(len(t) - n + 1))

    def score(h, r):
        p = rr = 0.0
        k = 0
        for n in range(1, n_max + 1):
            gh, gr = ngrammes(h, n), ngrammes(r, n)
            if not gh or not gr:
                continue
            commun = sum((gh & gr).values())
            p += commun / sum(gh.values())
            rr += commun / sum(gr.values())
            k += 1
        if not k or not (p or rr):
            return 0.0
        p, rr = p / k, rr / k
        return 100 * (1 + beta**2) * p * rr / (beta**2 * p + rr) if (p or rr) else 0.0

    return (score(a, b) + score(b, a)) / 2


def juge_local(consigne: str, texte: str) -> str | None:
    """Juge : Qwen3-4B-Instruct-2507 (Apache 2.0, GGUF Q4_K_M d'Unsloth) servi par `llama-server` sur JUGE_URL.
    Modèle différent des trois traducteurs : il ne se donne pas raison à lui-même."""
    url = os.environ.get("JUGE_URL", "http://127.0.0.1:8091").rstrip("/")
    corps = json.dumps({"messages": [{"role": "system", "content": consigne}, {"role": "user", "content": texte}],
                        "temperature": 0, "max_tokens": 300, "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request(f"{url}/v1/chat/completions", data=corps, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except OSError:
        return None


def juger(origine: str, retraduction: str | None) -> tuple[bool, str]:
    if not retraduction:
        return False, "retraduction impossible"
    r = juge_local(CONSIGNE_JUGE, f"A : {origine}\nB : {retraduction}")
    if r is None:
        raise SystemExit("Le juge local ne répond pas : lancer llama-server sur JUGE_URL (voir l'en-tête du script).")
    try:
        d = json.loads(r.strip().removeprefix("```json").removesuffix("```").strip())
        return bool(d.get("fidele")), str(d.get("raison", ""))
    except Exception:
        return False, "réponse du juge illisible"


def traiter(texte_fr: str) -> dict:
    wo = {s: traduire(s, texte_fr, "wo") for s in SYSTEMES}
    res = {"wo": wo, "retour": {}, "fidele": {}, "raison": {}, "chrf": {}}
    for s, w in wo.items():
        if w:
            retour = traduire(RETRADUCTEUR[s], w, "fr")
            res["retour"][s] = retour
            res["fidele"][s], res["raison"][s] = juger(texte_fr, retour)
    presents = [s for s in SYSTEMES if wo[s]]
    for a, b in itertools.combinations(presents, 2):
        res["chrf"][f"{a}-{b}"] = round(chrf(wo[a], wo[b]), 1)
    problemes = []
    if len(presents) < len(SYSTEMES):
        problemes.append("systèmes absents : " + ", ".join(s for s in SYSTEMES if not wo[s]))
    problemes += [f"{s} : sens changé ({res['raison'][s]})" for s in presents if not res["fidele"].get(s)]
    problemes += [f"versions trop différentes ({p} : {v})" for p, v in res["chrf"].items() if v < SEUIL_CHRF]
    if presents:
        res["choisi"] = max(presents, key=lambda s: sum(v for p, v in res["chrf"].items() if s in p.split("-")))
    res["problemes"] = problemes
    return res


def attendre_quota(cle: str) -> None:
    """Le quota gratuit Gemini repart à minuit heure du Pacifique (8 h UTC en hiver = 8 h à Dakar) ; marge de 10 min."""
    import datetime as dt
    maintenant = dt.datetime.now(dt.timezone.utc)
    reprise = maintenant.replace(hour=8, minute=10, second=0, microsecond=0)
    if reprise <= maintenant:
        reprise += dt.timedelta(days=1)
    print(f"Gemini ne répond plus (quota ?) avant « {cle} » : attente jusqu'à {reprise:%d/%m %H:%M} UTC.", flush=True)
    time.sleep((reprise - maintenant).total_seconds())


def ecrire(lignes: list[dict], champs: list[str], detail: list[dict]) -> None:
    with CATALOGUE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, lineterminator="\n")
        w.writeheader()
        w.writerows(lignes)
    if detail:
        champs_d = list(dict.fromkeys(k for d in detail for k in d))
        with DETAIL.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=champs_d, lineterminator="\n")
            w.writeheader()
            w.writerows(detail)


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--essai", action="store_true", help="vérifier quels systèmes répondent, sans rien écrire")
    a.add_argument("--cle", action="append", help="seulement cette clé (répétable)")
    a.add_argument("--reprendre", action="store_true", help="sauter les phrases déjà passées (après une coupure)")
    args = a.parse_args()

    if args.essai:
        for s in SYSTEMES:
            print(f"{s:8} → {traduire(s, 'Bonjour, comment vas-tu ?', 'wo')}")
        return

    lignes = list(csv.DictReader(CATALOGUE.open(encoding="utf-8")))
    champs = list(lignes[0].keys())
    detail = []
    if args.reprendre and DETAIL.exists():
        detail = list(csv.DictReader(DETAIL.open(encoding="utf-8")))
    for r in lignes:
        if args.cle and r["cle"] not in args.cle:
            continue
        if r["statut"] == "relu":  # relu par un locuteur : on n'y touche plus
            continue
        if args.reprendre and r["statut"] in ("valide_concordance", "a_relire"):
            continue
        res = None
        for _ in range(2):  # au plus une attente de remise à zéro du quota par phrase
            try:
                res = traiter(r["texte_fr"])
                break
            except GeminiIndisponible:
                attendre_quota(r["cle"])
        if res is None:
            print(f"\nGemini ne répond toujours pas : arrêt avant « {r['cle']} ». Relancer avec --reprendre.")
            break
        if res.get("choisi"):
            r["texte_wo"] = res["wo"][res["choisi"]]
        r["statut"] = "valide_concordance" if not res["problemes"] else "a_relire"
        print(f"  {r['cle']:40} {r['statut']:20} {'; '.join(res['problemes'])[:120]}")
        detail.append({"cle": r["cle"], "texte_fr": r["texte_fr"], "statut": r["statut"],
                       "choisi": res.get("choisi", ""), "problemes": " | ".join(res["problemes"]),
                       **{f"wo_{s}": res["wo"].get(s) or "" for s in SYSTEMES},
                       **{f"retour_{s}": res["retour"].get(s) or "" for s in SYSTEMES},
                       **{f"chrf_{p}": v for p, v in res["chrf"].items()}})
        ecrire(lignes, champs, detail)  # après chaque phrase : une coupure ne fait plus tout perdre
    n = Counter(r["statut"] for r in lignes)
    print(f"\n{n.get('valide_concordance', 0)} validées par concordance, {n.get('a_relire', 0)} à relire par un locuteur.")


if __name__ == "__main__":
    main()
