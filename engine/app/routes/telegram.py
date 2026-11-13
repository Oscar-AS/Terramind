"""Bot Telegram (D12) : même logique que l'application, mêmes modules.

Telegram appelle POST /webhook/telegram à chaque message. L'en-tête
X-Telegram-Bot-Api-Secret-Token doit valoir TELEGRAM_WEBHOOK_SECRET (défini à
l'enregistrement du webhook) : sinon, refus.

Parcours :
- /start : présentation et clavier à 4 boutons ;
- position partagée : enregistrée, puis plan de culture ;
- photo : diagnostic ;
- « Alertes » : choix de la culture, puis date de repiquage (JJ/MM), puis alertes de la semaine ;
- autre texte : question libre (réponse honnête tant que les fiches ne sont pas prêtes).

État par conversation gardé en mémoire (position arrondie à 0,01°, culture, date) : il est
perdu au redémarrage du service, ce qui suffit pour la démonstration. Aucun numéro, aucun nom.
"""

from __future__ import annotations

import datetime as dt
import hmac
import json
import logging
import re
import urllib.request

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from .. import config
from ..modules import meteo
from ..modules.planification import sol as sol_module
from ..modules.planification.cultures import CULTURES
from ..modules.planification.plan import planifier
from ..modules.prevention.alerte import calculer

journal = logging.getLogger("terramind.telegram")
router = APIRouter()
API = "https://api.telegram.org/bot{jeton}/{methode}"
FICHIER = "https://api.telegram.org/file/bot{jeton}/{chemin}"

B_POSITION, B_PLAN, B_ALERTES, B_AIDE = "📍 Envoyer ma position", "🌱 Que planter ?", "🔔 Alertes", "❓ Aide"
CLAVIER = {"keyboard": [[{"text": B_POSITION, "request_location": True}], [{"text": B_PLAN}, {"text": B_ALERTES}],
                        [{"text": B_AIDE}]], "resize_keyboard": True}
BADGE = {"conseillee": "✅", "possible": "⚠️", "deconseillee": "⛔"}
AGENT = "Pour être sûr, montre ta plante à un agent agricole (ANCAR, service départemental de l'agriculture)."
ACCUEIL = ("Bienvenue sur TerraMind 🌱\n\n"
           "📷 Envoie la photo d'une feuille malade : je te dis ce que ça peut être.\n"
           "📍 Partage ta position : je te dis quoi planter ce mois-ci, selon ton sol.\n"
           "🔔 Déclare ta culture : je te préviens quand la météo favorise une maladie ou un ravageur.\n\n"
           "Je réponds en français pour l'instant. Mes conseils viennent de documents publiés "
           "(ISRA, PADEN) ; je ne donne jamais de produit ni de dose.")

ETATS: dict[int, dict] = {}


def _appel(methode: str, **donnees) -> dict:
    req = urllib.request.Request(API.format(jeton=config.TELEGRAM_BOT_TOKEN, methode=methode),
                                 data=json.dumps(donnees).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def envoyer(chat: int, texte: str, **extra):
    try:
        _appel("sendMessage", chat_id=chat, text=texte[:4000], **extra)
    except Exception as e:  # Telegram indisponible : on journalise sans le contenu
        journal.warning("envoi Telegram échoué : %s", type(e).__name__)


def _plan(chat: int):
    e = ETATS[chat]
    envoyer(chat, "Je regarde ton sol et la saison… (cela peut prendre une demi-minute)")
    try:
        d, _ = planifier(e["lat"], e["lon"], dt.date.today(), "ne_sait_pas", "ne_sait_pas")
    except sol_module.SolIndisponible:
        envoyer(chat, "Je n'arrive pas à lire le sol à cet endroit. Réessaie plus tard.")
        return
    s = d["sol"]
    lignes = [f"🟫 Ton sol : {s['sable_pct']} % de sable, pH {s['ph']} (carte iSDAsoil).", ""]
    for c in d["cultures"]:
        lignes.append(f"{BADGE[c['adaptation']]} {c['libelle']} : {c['periode_semis']}")
        lignes += [f"   ⚠️ {a}" for a in c["avertissements"]]
    lignes += ["", "Source : Guide pratique du maraîchage au Sénégal (ISRA, 1987).",
               "Si l'eau de ton puits est salée, évite l'oignon et la carotte."]
    envoyer(chat, "\n".join(lignes), reply_markup=CLAVIER)


def _alertes(chat: int):
    e = ETATS[chat]
    try:
        d = calculer(e["lat"], e["lon"], e["culture"], dt.date.today(), e.get("repiquage"))
    except meteo.MeteoIndisponible:
        envoyer(chat, "La météo est momentanément indisponible. Réessaie plus tard.")
        return
    actives = [a["conseil"] for a in d["alertes"] if a["niveau"] != "aucun"]
    debut, fin = d["meteo"]["periode"]
    texte = "\n\n".join(f"🔔 {a}" for a in actives) if actives else "😌 Pas d'alerte cette semaine pour ta culture."
    envoyer(chat, f"{texte}\n\nMétéo du {debut} au {fin} (NASA POWER).", reply_markup=CLAVIER)


def _photo(chat: int, file_id: str, culture: str | None):
    from ..modules.diagnostic import modele

    envoyer(chat, "J'examine ta feuille… 🔎")
    try:
        chemin = _appel("getFile", file_id=file_id)["result"]["file_path"]
        with urllib.request.urlopen(FICHIER.format(jeton=config.TELEGRAM_BOT_TOKEN, chemin=chemin), timeout=30) as r:
            contenu = r.read()
        res = modele.diagnostiquer(contenu, culture)
    except modele.ModeleAbsent:
        envoyer(chat, "Le diagnostic photo est momentanément indisponible.")
        return
    except Exception as e:
        journal.info("photo Telegram illisible : %s", type(e).__name__)
        envoyer(chat, "Je n'arrive pas à lire cette photo. Reprends-la, bien nette.")
        return
    top = res["predictions"][0]
    if not res["certain"]:
        envoyer(chat, "🤔 Je ne suis pas sûr de ce que je vois. Reprends la photo d'une seule feuille, de près, "
                      "à la lumière du jour. " + AGENT)
    elif top["categorie"] == "sain":
        envoyer(chat, "✅ Cette feuille semble saine.")
    else:
        envoyer(chat, f"⚠️ Cela ressemble à : {top['libelle']} ({round(top['confiance'] * 100)} %).\n"
                      f"Ce n'est qu'une première indication, pas un diagnostic sûr. {AGENT}")
        texte = texte_fiche(top["etiquette"], top.get("culture"))
        envoyer(chat, texte or "Je n'ai pas encore de fiche sur ce problème. Montre ta plante à un agent agricole.")


def texte_fiche(etiquette: str, culture: str | None) -> str | None:
    """La fiche en 4 parties (ce que c'est, pourquoi, que faire, éviter), puis ses sources."""
    from .v1 import PARTIES_FICHE, fiche_simple

    fiche = fiche_simple(etiquette, culture)
    if not fiche:
        return None
    emojis = {"ce_que_c_est": "🔎", "pourquoi": "💡", "que_faire": "🩹", "eviter": "🛡️"}
    blocs, n = [], 0
    for cle, titre in PARTIES_FICHE.items():
        if fiche.get(cle):
            n += 1
            lignes = [l.lstrip("- ").strip() for l in fiche[cle].split("\n") if l.strip()]
            blocs.append(f"{emojis[cle]} {n}. {titre}\n" + "\n".join(f"• {l}" for l in lignes))
    documents = sorted({s["document"].split(",")[0] for s in fiche["sources"]})
    blocs.append("📚 Sources : " + " ; ".join(documents))
    return "\n\n".join(blocs)


def traiter(maj: dict):
    if "callback_query" in maj:
        q = maj["callback_query"]
        chat = q["message"]["chat"]["id"]
        _appel_silencieux("answerCallbackQuery", callback_query_id=q["id"])
        culture = q.get("data", "").removeprefix("culture:")
        if culture in CULTURES:
            ETATS.setdefault(chat, {})["culture"] = culture
            ETATS[chat]["attend_date"] = True
            envoyer(chat, f"C'est noté : {CULTURES[culture]['libelle'].lower()}. "
                          "Quand as-tu repiqué ? Écris la date comme ceci : 15/10")
        return
    msg = maj.get("message") or {}
    chat = (msg.get("chat") or {}).get("id")
    if chat is None:
        return
    etat = ETATS.setdefault(chat, {})
    texte = (msg.get("text") or "").strip()

    if "location" in msg:
        etat["lat"] = round(msg["location"]["latitude"], 2)
        etat["lon"] = round(msg["location"]["longitude"], 2)
        _plan(chat)
    elif msg.get("photo"):
        _photo(chat, msg["photo"][-1]["file_id"], etat.get("culture"))
    elif texte.startswith("/start") or texte == B_AIDE:
        envoyer(chat, ACCUEIL, reply_markup=CLAVIER)
    elif texte == B_PLAN:
        if "lat" in etat:
            _plan(chat)
        else:
            envoyer(chat, "Partage d'abord ta position avec le bouton 📍 (depuis ton champ).", reply_markup=CLAVIER)
    elif texte == B_ALERTES:
        if "lat" not in etat:
            envoyer(chat, "Partage d'abord ta position avec le bouton 📍.", reply_markup=CLAVIER)
        elif "culture" in etat and not etat.get("attend_date"):
            _alertes(chat)
        else:
            boutons = [[{"text": c["libelle"], "callback_data": f"culture:{k}"}] for k, c in CULTURES.items()]
            envoyer(chat, "Qu'est-ce que tu as planté ?", reply_markup={"inline_keyboard": boutons})
    elif etat.get("attend_date") and (m := re.fullmatch(r"(\d{1,2})[/.\- ](\d{1,2})", texte)):
        aujourdhui = dt.date.today()
        jour, mois = int(m.group(1)), int(m.group(2))
        try:
            date = dt.date(aujourdhui.year - (mois > aujourdhui.month), mois, jour)
        except ValueError:
            envoyer(chat, "Je n'ai pas compris la date. Écris-la comme ceci : 15/10")
            return
        etat["repiquage"], etat["attend_date"] = date, False
        if "lat" in etat:
            _alertes(chat)
    elif texte:
        from ..modules.rag.reponse import repondre

        r = repondre(texte)
        if r["statut"] != "ok":
            envoyer(chat, "Je n'ai pas la réponse dans mes fiches. " + AGENT, reply_markup=CLAVIER)
        else:
            src = "\n".join(f"• {s['document']}" + (f", p. {s['page']}" if s["page"][:1].isdigit() else "")
                             for s in r["sources"][:3])
            envoyer(chat, f"{r['texte']}\n\nSources :\n{src}", reply_markup=CLAVIER)


def _appel_silencieux(methode: str, **donnees):
    try:
        _appel(methode, **donnees)
    except Exception:
        pass


@router.post("/webhook/telegram")
async def webhook(request: Request, taches: BackgroundTasks,
                  x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    secret = config.TELEGRAM_WEBHOOK_SECRET
    if not config.TELEGRAM_BOT_TOKEN or not secret:
        raise HTTPException(503, "bot Telegram non configuré")
    if not x_telegram_bot_api_secret_token or not hmac.compare_digest(x_telegram_bot_api_secret_token, secret):
        raise HTTPException(403, "secret invalide")
    # Réponse immédiate à Telegram ; le travail (sol, météo, photo) se fait ensuite.
    taches.add_task(traiter, await request.json())
    return {"ok": True}
