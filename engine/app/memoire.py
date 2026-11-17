"""Mémoire du bot Telegram : ce que l'agriculteur a déjà dit, gardé même quand Render s'endort.

Render (offre gratuite) efface tout à chaque redémarrage : l'état de chaque conversation (langue,
position du champ arrondie à ~1 km, culture, date de plantation, 3 derniers échanges) est donc rangé
dans Supabase, table `memoire_bot` (docs/memoire-bot.sql), par l'API REST (aucune dépendance en plus).

- Clé : empreinte SHA-256 du numéro de conversation Telegram, salée par TELEGRAM_WEBHOOK_SECRET :
  le numéro lui-même n'est jamais stocké.
- Sans SUPABASE_URL / SUPABASE_KEY, ou si Supabase ne répond pas : rien n'est rangé, le bot garde
  l'état en mémoire vive comme avant (il ne plante jamais à cause de la mémoire).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
import urllib.parse
import urllib.request

from . import config  # noqa: F401  (charge .env)

journal = logging.getLogger("terramind.memoire")
TABLE = "memoire_bot"
DELAI = 5  # secondes : la mémoire ne doit jamais faire attendre l'agriculteur longtemps
# Champs gardés d'une visite à l'autre (les autres sont des drapeaux du moment).
GARDES = (
    "langue",
    "lat",
    "lon",
    "eau_salee",
    "bas_fond",
    "culture",
    "repiquage",
    "attend_date",
    "date_libre",
    "historique",
)


def _reglages() -> tuple[str, str] | None:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    cle = os.environ.get("SUPABASE_KEY", "").strip()
    return (url, cle) if url and cle else None


def active() -> bool:
    return _reglages() is not None


def cle_de(chat: int) -> str:
    sel = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    return hashlib.sha256(f"{sel}:{chat}".encode()).hexdigest()


def vers_json(etat: dict) -> dict:
    sortie = {}
    for k in GARDES:
        if k in etat:
            v = etat[k]
            sortie[k] = {"date": v.isoformat()} if isinstance(v, dt.date) else v
    return sortie


def _depuis_json(donnees: dict) -> dict:
    etat = {}
    for k, v in donnees.items():
        if k in GARDES:
            etat[k] = dt.date.fromisoformat(v["date"]) if isinstance(v, dict) and "date" in v else v
    return etat


def _requete(methode: str, chemin: str, corps: object | None = None, entetes: dict | None = None):
    url, cle = _reglages()
    req = urllib.request.Request(
        f"{url}/rest/v1/{chemin}",
        method=methode,
        data=json.dumps(corps).encode() if corps is not None else None,
        headers={
            "apikey": cle,
            "Authorization": f"Bearer {cle}",
            "Content-Type": "application/json",
            **(entetes or {}),
        },
    )
    with urllib.request.urlopen(req, timeout=DELAI) as r:
        texte = r.read()
    return json.loads(texte) if texte else None


def charger(chat: int) -> dict:
    """L'état gardé pour cette conversation, ou {} (rien de gardé, ou Supabase indisponible)."""
    if not active():
        return {}
    try:
        lignes = _requete("GET", f"{TABLE}?cle=eq.{urllib.parse.quote(cle_de(chat))}&select=etat")
        return _depuis_json(lignes[0]["etat"]) if lignes else {}
    except Exception as e:
        journal.warning("mémoire illisible (%s) : le bot continue sans", type(e).__name__)
        return {}


def enregistrer(chat: int, etat: dict) -> bool:
    """Range l'état (insertion ou mise à jour). False si rien n'a été rangé."""
    if not active():
        return False
    try:
        _requete(
            "POST",
            f"{TABLE}?on_conflict=cle",
            {
                "cle": cle_de(chat),
                "etat": vers_json(etat),
                "maj": dt.datetime.now(dt.timezone.utc).isoformat(),
            },
            {"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
        return True
    except Exception as e:
        journal.warning("mémoire non enregistrée (%s)", type(e).__name__)
        return False


def oublier(chat: int) -> bool:
    """Efface tout ce qui est gardé pour cette conversation (commande /oublier)."""
    if not active():
        return False
    try:
        _requete("DELETE", f"{TABLE}?cle=eq.{urllib.parse.quote(cle_de(chat))}")
        return True
    except Exception as e:
        journal.warning("mémoire non effacée (%s)", type(e).__name__)
        return False


# --- Mémoire de la conversation : les derniers échanges, pour comprendre une question de suite. ---
HISTORIQUE_MAX = 3
HISTORIQUE_DUREE = dt.timedelta(hours=1)  # au-delà, c'est une nouvelle conversation


def echanges_recents(etat: dict, maintenant: dt.datetime | None = None) -> list[dict]:
    maintenant = maintenant or dt.datetime.now(dt.timezone.utc)
    recents = []
    for e in etat.get("historique") or []:
        try:
            if maintenant - dt.datetime.fromisoformat(e["quand"]) <= HISTORIQUE_DUREE:
                recents.append(e)
        except (KeyError, TypeError, ValueError):
            continue
    return recents[-HISTORIQUE_MAX:]


def ajouter_echange(etat: dict, question: str, reponse: str):
    h = echanges_recents(etat)
    h.append(
        {
            "question": question[:500],
            "reponse": reponse[:600],
            "quand": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    )
    etat["historique"] = h[-HISTORIQUE_MAX:]
