"""Bot Telegram (D12) : même logique que l'application, mêmes modules.

Telegram appelle POST /webhook/telegram à chaque message. L'en-tête
X-Telegram-Bot-Api-Secret-Token doit valoir TELEGRAM_WEBHOOK_SECRET (défini à
l'enregistrement du webhook) : sinon, refus.

Ton : un conseiller qui accompagne pas à pas. Chaque message répond d'abord, puis structure
(titres en gras), puis propose la suite (« Ce que tu peux faire ensuite »). Pas d'émoji, texte en HTML Telegram.

Parcours :
- /start ou « Aide » : présentation et clavier ;
- position partagée : enregistrée, puis plan de culture ;
- photo : diagnostic, puis la fiche en 4 temps ;
- « Surveiller ma culture » : choix de la culture, puis date de repiquage (JJ/MM), puis alertes de la semaine ;
- autre texte : question libre, réponse tirée des fiches (D8).

État par conversation gardé en mémoire (position arrondie à 0,01°, culture, date) : il est
perdu au redémarrage du service, ce qui suffit pour la démonstration. Aucun numéro, aucun nom.
"""

from __future__ import annotations

import datetime as dt
import hmac
import json
import logging
import re
import urllib.error
import urllib.request
import uuid
from html import escape as _echapper
from pathlib import Path

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
LIMITE = 4000  # Telegram refuse les messages de plus de 4096 caractères

B_POSITION = "Envoyer la position de mon champ"
B_PHOTO, B_PLAN = "Examiner une feuille", "Que planter ?"
B_ALERTES, B_AIDE = "Surveiller ma culture", "Aide"
CLAVIER = {"keyboard": [[{"text": B_POSITION, "request_location": True}],
                        [{"text": B_PHOTO}, {"text": B_PLAN}],
                        [{"text": B_ALERTES}, {"text": B_AIDE}]],
           "resize_keyboard": True}
AGENT = "un agent agricole (ANCAR, service départemental de l'agriculture)"

ACCUEIL = (
    "<b>Bonjour, je suis TerraMind.</b>\n"
    "Je suis ton assistant pour le maraîchage dans les Niayes. Je t'accompagne pas à pas, à partir de "
    "documents agricoles publiés (ISRA, FAO, DPV) et de la météo réelle de ton champ.\n\n"
    "<b>Ce que je peux faire pour toi</b>\n"
    "1. Te dire quoi planter ce mois-ci, selon le sol de ton champ.\n"
    "2. Surveiller ta culture et te dire si la météo de la semaine favorise une maladie ou un ravageur.\n"
    "3. Examiner la photo d'une feuille malade et t'expliquer quoi faire.\n\n"
    "<b>Par où commencer</b>\n"
    f"Partage la position de ton champ avec le bouton « {B_POSITION} », en bas de l'écran. "
    "Tu peux aussi m'envoyer directement la photo d'une feuille, ou m'écrire ta question.\n\n"
    "<i>Je ne donne jamais de nom de produit ni de dose : pour un traitement, je t'oriente vers "
    f"{AGENT}.</i>"
)
CONSEILS_PHOTO = (
    "1. Une seule feuille, celle qui est malade.\n"
    "2. De près : la feuille doit remplir la photo.\n"
    "3. À la lumière du jour, sans ombre."
)
DEMANDE_POSITION = (
    "Pour cela, j'ai besoin de connaître ton champ.\n\n"
    "<b>Ce que tu peux faire ensuite</b>\n"
    f"Touche le bouton « {B_POSITION} » en bas de l'écran, de préférence quand tu es dans ton champ."
)

CHOIX_LANGUE = ("<b>Bienvenue sur TerraMind.</b>\n"
                "En quelle langue veux-tu que je te parle ? Touche « Wolof » ou « Français ».\n\n"
                "<i>En wolof, je te réponds par des messages vocaux, avec le texte en français en dessous.</i>")
CLAVIER_LANGUE = {"inline_keyboard": [[{"text": "Wolof", "callback_data": "langue:wo"},
                                       {"text": "Français", "callback_data": "langue:fr"}]]}

# Notes vocales en wolof (D10), préparées à l'avance : content/audio/wo/<clé>.ogg, textes dans
# content/voix/messages_wolof.csv. Phrases générales et sensibles : voix humaine ; contenu choisi par
# le modèle (fiche de la maladie reconnue, alerte, culture) : voix de synthèse contrôlée.
AUDIO_WO = Path(__file__).resolve().parents[3] / "content" / "audio" / "wo"
VOIX_DEJA_ENVOYEES: dict[str, str] = {}  # clé → file_id Telegram, pour ne pas renvoyer le fichier

ETATS: dict[int, dict] = {}


def escape(texte: str) -> str:
    """Échappe <, > et & pour le HTML de Telegram (les apostrophes restent lisibles)."""
    return _echapper(texte, quote=False)


def _court(document: str) -> str:
    """Nom court d'une source : avant la première virgule, sans parenthèse laissée ouverte."""
    nom = document.split(",")[0].strip()
    if nom.count("(") > nom.count(")"):
        nom = nom[:nom.rfind("(")].strip()
    return nom


def _appel(methode: str, **donnees) -> dict:
    req = urllib.request.Request(API.format(jeton=config.TELEGRAM_BOT_TOKEN, methode=methode),
                                 data=json.dumps(donnees).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _morceaux(texte: str) -> list[str]:
    """Coupe un long message aux lignes vides, pour rester sous la limite de Telegram."""
    morceaux, courant = [], ""
    for bloc in texte.split("\n\n"):
        if courant and len(courant) + len(bloc) + 2 > LIMITE:
            morceaux.append(courant)
            courant = bloc
        else:
            courant = f"{courant}\n\n{bloc}" if courant else bloc
    return [m[:LIMITE] for m in morceaux + [courant]]


def envoyer(chat: int, texte: str, **extra):
    """Envoie un message en HTML Telegram ; le clavier éventuel accompagne le dernier morceau."""
    morceaux = _morceaux(texte)
    for i, m in enumerate(morceaux):
        options = extra if i == len(morceaux) - 1 else {}
        try:
            _appel("sendMessage", chat_id=chat, text=m, parse_mode="HTML", **options)
        except urllib.error.HTTPError as e:
            # 400 : balisage refusé par Telegram. On renvoie le même texte sans mise en forme.
            journal.warning("envoi Telegram refusé (%s) : nouvel essai en texte simple", e.code)
            brut = re.sub(r"</?[bi]>", "", m).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            try:
                _appel("sendMessage", chat_id=chat, text=brut, **options)
            except Exception as e2:
                journal.warning("envoi Telegram échoué : %s", type(e2).__name__)
        except Exception as e:  # Telegram indisponible : on journalise sans le contenu
            journal.warning("envoi Telegram échoué : %s", type(e).__name__)


def _envoyer_fichier(methode: str, chat: int, champ: str, chemin: Path) -> dict:
    """Envoie un fichier à Telegram (multipart), sans dépendance externe."""
    borne = uuid.uuid4().hex
    corps = (f"--{borne}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat}\r\n"
             f"--{borne}\r\nContent-Disposition: form-data; name=\"{champ}\"; filename=\"{chemin.name}\"\r\n"
             "Content-Type: audio/ogg\r\n\r\n").encode() + chemin.read_bytes() + f"\r\n--{borne}--\r\n".encode()
    req = urllib.request.Request(API.format(jeton=config.TELEGRAM_BOT_TOKEN, methode=methode), data=corps,
                                 headers={"Content-Type": f"multipart/form-data; boundary={borne}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def dire(chat: int, cle: str, toujours: bool = False):
    """En wolof (ou toujours=True), envoie la note vocale de cette clé. Sans fichier audio, ne fait rien :
    le texte suit de toute façon."""
    if not toujours and ETATS.get(chat, {}).get("langue") != "wo":
        return
    chemin = AUDIO_WO / f"{cle}.ogg"
    if not chemin.exists():
        journal.info("note vocale wolof pas encore enregistrée : %s", cle)
        return
    try:
        if cle in VOIX_DEJA_ENVOYEES:
            _appel("sendVoice", chat_id=chat, voice=VOIX_DEJA_ENVOYEES[cle])
        else:
            r = _envoyer_fichier("sendVoice", chat, "voice", chemin)
            VOIX_DEJA_ENVOYEES[cle] = r["result"]["voice"]["file_id"]
    except Exception as e:
        journal.warning("note vocale non envoyée : %s", type(e).__name__)


def _liste(lignes: list[str]) -> str:
    return "\n".join(f"• {escape(l)}" for l in lignes)


def _plan(chat: int):
    e = ETATS[chat]
    envoyer(chat, "Je regarde maintenant le sol de ton champ et la saison. Cela prend environ 30 secondes.")
    try:
        d, _ = planifier(e["lat"], e["lon"], dt.date.today(), "ne_sait_pas", "ne_sait_pas")
    except sol_module.SolIndisponible:
        envoyer(chat, "Je n'arrive pas à lire la carte des sols à cet endroit pour le moment. "
                      "Réessaie dans quelques minutes avec le bouton « Que planter ? ».", reply_markup=CLAVIER)
        return
    s = d["sol"]
    groupes = {"conseillee": [], "possible": [], "deconseillee": []}
    for c in d["cultures"]:
        groupes[c["adaptation"]].append(c)
    dire(chat, "plan_intro")
    for c in groupes["conseillee"] + groupes["possible"]:
        dire(chat, f"culture_{c['culture']}_{c['adaptation']}")
    dire(chat, "eau_salee")

    blocs = ["<b>Ce qu'il faut savoir sur ton sol</b>\n"
             f"D'après la carte des sols iSDAsoil, ton champ contient environ {s['sable_pct']} % de sable "
             f"et son pH est de {s['ph']}."]
    if groupes["conseillee"]:
        blocs.append("<b>Ce que tu peux planter maintenant</b>\n" + "\n".join(
            f"• {escape(c['libelle'])} : {escape(c['periode_semis'])}"
            + "".join(f"\n   <i>{escape(a)}</i>" for a in c["avertissements"]) for c in groupes["conseillee"]))
    if groupes["possible"]:
        blocs.append("<b>Ce que tu peux planter, avec quelques précautions</b>\n" + "\n".join(
            f"• {escape(c['libelle'])} : {escape(c['periode_semis'])}"
            + "".join(f"\n   <i>{escape(a)}</i>" for a in c["avertissements"]) for c in groupes["possible"]))
    if groupes["deconseillee"]:
        blocs.append("<b>Ce qu'il vaut mieux ne pas planter ce mois-ci</b>\n"
                     + escape(", ".join(c["libelle"] for c in groupes["deconseillee"])) + ".")
    blocs.append("<b>Une précaution importante</b>\nSi l'eau de ton puits est salée, évite l'oignon et la carotte.")
    blocs.append("<b>Ce que tu peux faire ensuite</b>\n"
                 f"Si une culture est déjà en place, touche « {B_ALERTES} » : je regarde si la météo de la "
                 "semaine favorise une maladie. Si une feuille a des taches, envoie-moi sa photo.")
    blocs.append("<i>Sources : Guide pratique du maraîchage au Sénégal (ISRA, 1987) ; carte des sols iSDAsoil.</i>")
    envoyer(chat, "\n\n".join(blocs), reply_markup=CLAVIER)


def _alertes(chat: int):
    e = ETATS[chat]
    try:
        d = calculer(e["lat"], e["lon"], e["culture"], dt.date.today(), e.get("repiquage"))
    except meteo.MeteoIndisponible:
        envoyer(chat, "La météo est momentanément indisponible. Réessaie dans quelques minutes.",
                reply_markup=CLAVIER)
        return
    actives = [a["conseil"] for a in d["alertes"] if a["niveau"] != "aucun" and a["conseil"]]
    if actives:
        dire(chat, "alerte_intro")
        for a in d["alertes"]:
            if a["niveau"] != "aucun" and a["conseil"]:
                dire(chat, f"alerte_{a['risque']}")
    else:
        dire(chat, "alerte_rien")
    debut, fin = d["meteo"]["periode"]
    culture = CULTURES[e["culture"]]["libelle"].lower()
    blocs = [f"<b>Ce que la météo annonce pour ta culture ({escape(culture)}) cette semaine</b>\n"
             f"J'ai regardé la météo de ton champ du {escape(str(debut))} au {escape(str(fin))}."]
    if actives:
        blocs.append("<b>Ce qu'il faut surveiller</b>\n" + _liste(actives))
    else:
        blocs.append("<b>Bonne nouvelle : rien d'inquiétant cette semaine</b>\nLa météo de cette semaine ne favorise aucune des maladies "
                     "ni aucun des ravageurs que je surveille pour cette culture.")
    blocs.append("<b>Ce que tu peux faire ensuite</b>\n"
                 f"Reviens me demander la semaine prochaine avec le bouton « {B_ALERTES} ». "
                 "Si tu vois des taches sur une feuille, envoie-moi sa photo.")
    blocs.append("<i>Météo : NASA POWER. Ces règles viennent d'études faites hors du Sénégal : je parle de "
                 "conditions favorables, pas de maladie certaine.</i>")
    envoyer(chat, "\n\n".join(blocs), reply_markup=CLAVIER)


def _photo(chat: int, file_id: str, culture: str | None):
    from ..modules.diagnostic import modele

    dire(chat, "attente_photo")
    envoyer(chat, "Merci, je regarde ta photo. Cela prend quelques secondes.")
    try:
        chemin = _appel("getFile", file_id=file_id)["result"]["file_path"]
        with urllib.request.urlopen(FICHIER.format(jeton=config.TELEGRAM_BOT_TOKEN, chemin=chemin), timeout=30) as r:
            contenu = r.read()
        res = modele.diagnostiquer(contenu, culture)
    except modele.ModeleAbsent:
        envoyer(chat, "L'examen des photos est momentanément indisponible. Réessaie plus tard.",
                reply_markup=CLAVIER)
        return
    except Exception as e:
        journal.info("photo Telegram illisible : %s", type(e).__name__)
        dire(chat, "photo_illisible")
        envoyer(chat, "Je n'arrive pas à lire cette photo. Peux-tu la reprendre, bien nette ?\n\n"
                      + CONSEILS_PHOTO, reply_markup=CLAVIER)
        return
    top = res["predictions"][0]
    if not res["certain"]:
        dire(chat, "photo_incertaine")
        envoyer(chat, "<b>Je ne suis pas sûr de ce que je vois.</b>\n"
                      "Plutôt que de te donner une mauvaise réponse, je préfère que tu reprennes la photo.\n\n"
                      "<b>Comment reprendre la photo</b>\n" + CONSEILS_PHOTO + "\n\n"
                      f"<i>Si la plante va mal, montre-la aussi à {AGENT}.</i>", reply_markup=CLAVIER)
        return
    if top["categorie"] == "sain":
        dire(chat, "photo_saine")
        envoyer(chat, "<b>Bonne nouvelle : cette feuille semble saine.</b>\n"
                      "Je ne vois pas de signe de maladie sur cette photo.\n\n"
                      "<b>Ce que tu peux faire ensuite</b>\nSi d'autres plants ont des taches, envoie-moi leur photo.",
                reply_markup=CLAVIER)
        return
    tete = ("<b>Ce que je vois sur ta feuille</b>\n"
            f"Ta feuille ressemble à : <b>{escape(top['libelle'])}</b> "
            f"(confiance du modèle : {round(top['confiance'] * 100)} %).\n"
            "C'est une première indication, pas un diagnostic sûr.")
    from .v1 import FICHES_ETIQUETTES

    nom_fiche = FICHES_ETIQUETTES.get(top["etiquette"])
    dire(chat, f"fiche_{nom_fiche}" if nom_fiche else "pas_de_fiche")
    dire(chat, "diagnostic_prudence")
    fiche = texte_fiche(top["etiquette"], top.get("culture"))
    suite = ("<b>Ce que tu peux faire ensuite</b>\n"
             f"Pour confirmer, montre ta plante à {AGENT}. "
             "Tu peux aussi m'écrire une question sur ce problème.")
    if not fiche:
        envoyer(chat, f"{tete}\n\nJe n'ai pas encore de fiche sur ce problème.\n\n{suite}", reply_markup=CLAVIER)
        return
    corps, sources = fiche
    envoyer(chat, f"{tete}\n\n{corps}\n\n{suite}\n\n{sources}", reply_markup=CLAVIER)


def texte_fiche(etiquette: str, culture: str | None) -> tuple[str, str] | None:
    """La fiche en 4 parties (ce que c'est, pourquoi, que faire, éviter) en HTML, et la ligne des sources."""
    from .v1 import PARTIES_FICHE, fiche_simple

    fiche = fiche_simple(etiquette, culture)
    if not fiche:
        return None
    blocs, n = [], 0
    for cle, titre in PARTIES_FICHE.items():
        if fiche.get(cle):
            n += 1
            lignes = [l.lstrip("- ").strip() for l in fiche[cle].split("\n") if l.strip()]
            blocs.append(f"<b>{n}. {escape(titre)}</b>\n" + _liste(lignes))
    documents = sorted({_court(s["document"]) for s in fiche["sources"]})
    return "\n\n".join(blocs), "<i>Sources : " + escape(" ; ".join(documents)) + "</i>"


def _question(chat: int, texte: str):
    from ..modules.rag.reponse import repondre

    r = repondre(texte)
    if r["statut"] != "ok":
        dire(chat, "je_ne_sais_pas")
        envoyer(chat, "Je n'ai pas trouvé la réponse dans mes fiches, et je préfère ne pas inventer.\n"
                      f"Pour cette question, le mieux est de demander à {AGENT}.\n\n"
                      "<b>Ce que je sais faire</b>\n"
                      "• Te dire quoi planter, selon ton sol.\n"
                      "• Surveiller ta culture selon la météo.\n"
                      "• Examiner la photo d'une feuille malade.", reply_markup=CLAVIER)
        return
    sources = " ; ".join(_court(s["document"]) + (f", p. {s['page']}" if s["page"][:1].isdigit() else "")
                         for s in r["sources"][:3])
    reponse = escape(r["texte"].replace("**", ""))
    envoyer(chat, f"{reponse}\n\n<i>Sources : {escape(sources)}</i>", reply_markup=CLAVIER)


def traiter(maj: dict):
    if "callback_query" in maj:
        q = maj["callback_query"]
        chat = q["message"]["chat"]["id"]
        _appel_silencieux("answerCallbackQuery", callback_query_id=q["id"])
        donnee = q.get("data", "")
        if donnee in ("langue:wo", "langue:fr"):
            ETATS.setdefault(chat, {})["langue"] = donnee[-2:]
            dire(chat, "accueil")
            envoyer(chat, ACCUEIL, reply_markup=CLAVIER)
            return
        culture = donnee.removeprefix("culture:")
        if culture in CULTURES:
            ETATS.setdefault(chat, {})["culture"] = culture
            ETATS[chat]["attend_date"] = True
            dire(chat, "date_repiquage")
            envoyer(chat, f"C'est noté : {escape(CULTURES[culture]['libelle'].lower())}.\n\n"
                          "<b>Une dernière question pour bien te conseiller</b>\nÀ quelle date l'as-tu repiquée ? "
                          "Écris-la comme ceci : <b>15/10</b> pour le 15 octobre. "
                          "Si tu ne sais plus, écris : <b>je ne sais pas</b>.")
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
        dire(chat, "position_recue")
        envoyer(chat, "Merci, j'ai bien reçu la position de ton champ. Je la garde arrondie à environ 1 km, "
                      "sans ton nom ni ton numéro.")
        _plan(chat)
    elif msg.get("photo"):
        _photo(chat, msg["photo"][-1]["file_id"], etat.get("culture"))
    elif msg.get("voice") or msg.get("audio"):
        dire(chat, "vocal_non_compris")
        envoyer(chat, "Je ne comprends pas encore les messages vocaux. Utilise les boutons en bas de l'écran, "
                      "ou envoie-moi la photo d'une feuille malade.", reply_markup=CLAVIER)
    elif texte.startswith(("/start", "/langue")) or ("langue" not in etat and not etat.get("attend_date")):
        dire(chat, "choix_langue", toujours=True)  # la question est aussi dite en wolof
        envoyer(chat, CHOIX_LANGUE, reply_markup=CLAVIER_LANGUE)
    elif texte == B_AIDE:
        dire(chat, "accueil")
        envoyer(chat, ACCUEIL + "\n\n<i>Pour changer de langue, écris /langue.</i>", reply_markup=CLAVIER)
    elif texte == B_PHOTO:
        dire(chat, "conseils_photo")
        envoyer(chat, "<b>Envoie-moi la photo d'une feuille malade.</b>\n"
                      "Touche le trombone en bas de l'écran, puis l'appareil photo.\n\n"
                      "<b>Comment bien prendre la photo</b>\n" + CONSEILS_PHOTO, reply_markup=CLAVIER)
    elif texte == B_PLAN:
        if "lat" in etat:
            _plan(chat)
        else:
            dire(chat, "demande_position")
            envoyer(chat, "Je peux te dire quoi planter ce mois-ci, selon le sol de ton champ. "
                          + DEMANDE_POSITION, reply_markup=CLAVIER)
    elif texte == B_ALERTES:
        if "lat" not in etat:
            dire(chat, "demande_position")
            envoyer(chat, "Je peux surveiller ta culture avec la météo de ton champ. "
                          + DEMANDE_POSITION, reply_markup=CLAVIER)
        elif "culture" in etat and not etat.get("attend_date"):
            _alertes(chat)
        else:
            boutons = [[{"text": c["libelle"], "callback_data": f"culture:{k}"}] for k, c in CULTURES.items()]
            dire(chat, "choix_culture")
            envoyer(chat, "<b>Quelle culture veux-tu que je surveille ?</b>\nChoisis-la dans la liste.",
                    reply_markup={"inline_keyboard": boutons})
    elif etat.get("attend_date") and re.fullmatch(r"(je )?ne sais (pas|plus)\.?", texte.lower()):
        etat["repiquage"], etat["attend_date"] = None, False
        envoyer(chat, "Pas de souci, je fais sans la date.")
        if "lat" in etat:
            _alertes(chat)
    elif etat.get("attend_date") and (m := re.fullmatch(r"(\d{1,2})[/.\- ](\d{1,2})", texte)):
        aujourdhui = dt.date.today()
        jour, mois = int(m.group(1)), int(m.group(2))
        try:
            date = dt.date(aujourdhui.year - (mois > aujourdhui.month), mois, jour)
        except ValueError:
            envoyer(chat, "Je n'ai pas compris la date. Écris-la comme ceci : <b>15/10</b> pour le 15 octobre.")
            return
        etat["repiquage"], etat["attend_date"] = date, False
        if "lat" in etat:
            _alertes(chat)
    elif texte:
        _question(chat, texte)


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
