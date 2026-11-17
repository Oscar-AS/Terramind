"""Bot Telegram (D12) : même logique que l'application, mêmes modules.

Telegram appelle POST /webhook/telegram à chaque message. L'en-tête
X-Telegram-Bot-Api-Secret-Token doit valoir TELEGRAM_WEBHOOK_SECRET (défini à
l'enregistrement du webhook) : sinon, refus.

Ton : un conseiller qui accompagne pas à pas. Chaque message répond d'abord, puis structure
(titres en gras), puis propose la suite (« Ce que tu peux faire ensuite »). Pas d'émoji dans les textes ;
en wolof, les boutons portent un numéro que les notes vocales citent. Texte en HTML Telegram.

Parcours :
- /start ou « Aide » : présentation et clavier ;
- position partagée : enregistrée, puis plan de culture ;
- photo : diagnostic, puis la fiche en 4 temps ;
- « La météo de la semaine pour ma culture » : choix de la culture, puis date de mise en place (JJ/MM), puis alertes ;
- autre texte : question libre, réponse tirée des fiches (D8).

État par conversation gardé en mémoire (position arrondie à 0,01°, culture, date) : il est
perdu au redémarrage du service, ce qui suffit pour la démonstration. Aucun numéro, aucun nom.
"""

from __future__ import annotations

import datetime as dt
import hmac
import json
import logging
import os
import re
import traceback
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
from ..modules.planification.plan import nombre_fr, ph_en_mots, planifier
from ..modules.prevention.alerte import calculer

journal = logging.getLogger("terramind.telegram")
router = APIRouter()
API = "https://api.telegram.org/bot{jeton}/{methode}"
FICHIER = "https://api.telegram.org/file/bot{jeton}/{chemin}"
LIMITE = 4000  # Telegram refuse les messages de plus de 4096 caractères

B_POSITION = "Envoyer la position de mon champ"
B_PHOTO = "Voir si ma plante est malade"
B_PLAN = "Que planter dans mon champ ?"
B_ALERTES = "Que dois-je retenir concernant la météo de cette semaine pour mes plantes ?"
B_QUESTION = "J'ai une question à te poser"
# Démonstration (décision de Salam, 15 nov 2026) : la zone de test est pour l'instant les Niayes. Ce bouton envoie
# une position fixe des Niayes (Rufisque, centroïde du département, geoBoundaries ; même zone pilote que l'app),
# pour que le jury essaie sans révéler où il se trouve. À retirer si TerraMind est retenu (base sur tout le
# Sénégal) : mettre BOUTON_POSITION_TEST=0 dans les variables de Render.
B_POSITION_TEST = "Envoyer une position test"
POSITION_TEST = {"nom": "Rufisque", "lat": 14.76, "lon": -17.21}
AVEC_POSITION_TEST = os.environ.get("BOUTON_POSITION_TEST", "1") != "0"
# Un bouton par ligne : le libellé reste lisible en entier sur un petit écran.
CLAVIER = {"keyboard": [[{"text": B_POSITION, "request_location": True}]]
                        + ([[{"text": B_POSITION_TEST}]] if AVEC_POSITION_TEST else []) + [[{"text": B_PHOTO}],
                        [{"text": B_PLAN}], [{"text": B_ALERTES}], [{"text": B_QUESTION}]],
           # is_persistent : Telegram garde les boutons affichés au lieu de les replier derrière une icône
           # (Bot API 6.4) ; un agriculteur peu habitué aux écrans ne trouverait pas l'icône.
           "resize_keyboard": True, "is_persistent": True}
# Anciens libellés (claviers encore affichés sur les téléphones) : traités comme les nouveaux.
# En wolof, beaucoup d'agriculteurs ne lisent pas le français : chaque bouton porte un numéro, que les
# notes vocales citent (« appuie sur le 2 ») ; l'agriculteur peut réécouter la note autant qu'il veut.
NUMEROS = {B_POSITION: 1, B_PHOTO: 2, B_PLAN: 3, B_ALERTES: 4, B_QUESTION: 5, B_POSITION_TEST: 6}
# Rangés dans l'ordre des numéros (1 à 5, puis le bouton test 6), pour que « appuie sur le 2 » corresponde
# aussi à la 2e ligne pour qui ne lit pas.
CLAVIER_WO = {"keyboard": sorted(([dict(b, text=f"{NUMEROS[b['text']]}. {b['text']}") for b in ligne]
                                  for ligne in CLAVIER["keyboard"]), key=lambda l: int(l[0]["text"].split(".")[0])),
              "resize_keyboard": True, "is_persistent": True}
B_AIDE = "/aide"  # l'accueil reste accessible par /aide et par les anciens boutons d'aide
ANCIENS_BOUTONS = {"Examiner une feuille": B_PHOTO, "Ma plante est malade : envoyer une photo": B_PHOTO,
                   "Que planter ?": B_PLAN, "Surveiller ma culture": B_ALERTES,
                   "La météo de la semaine pour ma culture": B_ALERTES,
                   "Aide": B_AIDE, "Comment ça marche ?": B_AIDE}
AGENT = "un agent agricole (ANCAR, service départemental de l'agriculture)"

ACCUEIL = (
    "<b>Bonjour, je suis TerraMind.</b>\n"
    "Je suis ton assistant pour le maraîchage dans les Niayes. Je t'accompagne pas à pas, à partir de "
    "documents agricoles publiés (ISRA, FAO, DPV) et de la météo de la zone de ton champ.\n\n"
    "<b>Ce que je peux faire pour toi</b>\n"
    "1. Te dire quoi planter ce mois-ci, selon le sol de ton champ.\n"
    "2. Surveiller ta culture et te dire si la météo de ces derniers jours favorise une maladie ou un ravageur.\n"
    "3. Regarder la photo de ta plante malade et t'expliquer quoi faire.\n\n"
    "<b>Par où commencer</b>\n"
    f"Partage la position de ton champ avec le bouton « {B_POSITION} », en bas de l'écran. "
    "Tu peux aussi m'envoyer directement une photo de ta plante, ou me poser ta question par écrit "
    "(en français), ou en message vocal en wolof.\n\n"
    "<i>Je ne donne jamais de nom de produit ni de dose : pour un traitement, je t'oriente vers "
    f"{AGENT}.</i>"
)
CONSEILS_PHOTO = (
    "1. Montre ce qui t'inquiète : une feuille, un fruit, une tige ou toute la plante.\n"
    "2. Approche-toi, pour que je voie bien les taches ou les trous.\n"
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

# Notes vocales en wolof (D10), préparées à l'avance : content/audio/wo/<clé>.ogg (ou .mp3, .m4a), textes dans
# content/voix/messages_wolof.csv. Phrases générales et sensibles : voix humaine ; contenu choisi par
# le modèle (fiche de la maladie reconnue, alerte, culture) : voix de synthèse contrôlée.
AUDIO_WO = Path(__file__).resolve().parents[3] / "content" / "audio" / "wo"
VOIX_DEJA_ENVOYEES: dict[str, str] = {}
TYPES_AUDIO = {".ogg": "audio/ogg", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}  # clé → file_id Telegram, pour ne pas renvoyer le fichier

ETATS: dict[int, dict] = {}


def phrase_ph(ph: float) -> str:
    """« ton sol est un peu acide », mais « ton sol n'est ni acide ni basique » (négation obligatoire)."""
    mots = ph_en_mots(ph)
    return f"ton sol n'est {mots}" if mots.startswith("ni ") else f"ton sol est {mots}"


def escape(texte: str) -> str:
    """Échappe <, > et & pour le HTML de Telegram (les apostrophes restent lisibles)."""
    return _echapper(texte, quote=False)


# Noms lisibles par un agriculteur pour les sources dont le nom court serait un nom d'auteur ou un document interne.
NOMS_LISIBLES = {"Beniest J. et al.": "Guide pratique du maraîchage au Sénégal (ISRA / FAO)",
                 "Sylla S.": "Thèse sur la mineuse de la tomate (UCAD / CIRAD)",
                 "Pfeiffer D. G. et al.": "Florida Entomologist (2013)",
                 "Diallo et al. 2015": "African Crop Science Journal (2015)",
                 "Blancard D.": "Ephytia (INRAE)", "Zitter T. A.": "Université Cornell",
                 "Spry C.": "Université du Kentucky", "Jackson G.": "Pacific Pests (fiche 163)",
                 "Panthee D. R.": "International Journal of Vegetable Science"}
SOURCES_INTERNES = ("Seuils météo des maladies et ravageurs",)  # nos notes de travail, pas des sources publiées


def _court(document: str) -> str | None:
    """Nom court d'une source : avant la première virgule, sans parenthèse laissée ouverte."""
    if document.startswith(SOURCES_INTERNES):
        return None
    for auteur, lisible in NOMS_LISIBLES.items():
        if document.startswith(auteur):
            return lisible
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
    if extra.get("reply_markup") is CLAVIER and ETATS.get(chat, {}).get("langue") == "wo":
        extra["reply_markup"] = CLAVIER_WO
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


def _envoyer_fichier(methode: str, chat: int, champ: str, chemin: Path, octets: bytes | None = None) -> dict:
    """Envoie un fichier à Telegram (multipart), sans dépendance externe. `octets` : contenu déjà en mémoire."""
    borne = uuid.uuid4().hex
    contenu = chemin.read_bytes() if octets is None else octets
    corps = (f"--{borne}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat}\r\n"
             f"--{borne}\r\nContent-Disposition: form-data; name=\"{champ}\"; filename=\"{chemin.name}\"\r\n"
             f"Content-Type: {TYPES_AUDIO.get(chemin.suffix, 'audio/ogg')}\r\n\r\n").encode() + contenu + f"\r\n--{borne}--\r\n".encode()
    req = urllib.request.Request(API.format(jeton=config.TELEGRAM_BOT_TOKEN, methode=methode), data=corps,
                                 headers={"Content-Type": f"multipart/form-data; boundary={borne}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def dire(chat: int, cle: str, toujours: bool = False):
    """En wolof (ou toujours=True), envoie la note vocale de cette clé. Sans fichier audio, ne fait rien :
    le texte suit de toute façon."""
    if not toujours and ETATS.get(chat, {}).get("langue") != "wo":
        return
    # Telegram accepte les notes vocales en OGG (Opus), MP3 ou M4A.
    chemin = next((AUDIO_WO / f"{cle}.{ext}" for ext in ("ogg", "mp3", "m4a") if (AUDIO_WO / f"{cle}.{ext}").exists()), None)
    if chemin is None:
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


QUESTIONS_CHAMP = {
    "eau": ("question_eau_salee", "<b>Une question sur ton eau</b>\nL'eau de ton puits est-elle salée ?"),
    "basfond": ("question_bas_fond", "<b>Une question sur ton champ</b>\nTon champ est-il dans un bas-fond, "
                "un endroit bas où l'eau reste longtemps après la pluie ?"),
}
CHAMP_ETAT = {"eau": "eau_salee", "basfond": "bas_fond"}


def _demander_champ(chat: int) -> bool:
    """Pose la prochaine question sur le champ (eau salée, puis bas-fond). False si tout est connu."""
    e = ETATS[chat]
    for cle, (voix, texte) in QUESTIONS_CHAMP.items():
        if CHAMP_ETAT[cle] not in e:
            dire(chat, voix)
            wo = e.get("langue") == "wo"
            envoyer(chat, texte, reply_markup={"inline_keyboard": [[
                {"text": "1. Oui" if wo else "Oui", "callback_data": f"{cle}:oui"},
                {"text": "2. Non" if wo else "Non", "callback_data": f"{cle}:non"},
                {"text": "3. Je ne sais pas" if wo else "Je ne sais pas", "callback_data": f"{cle}:ne_sait_pas"}]]})
            return True
    return False


def _liste(lignes: list[str]) -> str:
    return "\n".join(f"• {escape(l)}" for l in lignes)


def _plan(chat: int):
    e = ETATS[chat]
    if _demander_champ(chat):  # le plan suivra la dernière réponse
        return
    envoyer(chat, "Je regarde maintenant le sol de ton champ et la saison. Cela prend environ 30 secondes.")
    try:
        d, _ = planifier(e["lat"], e["lon"], dt.date.today(), e["eau_salee"], e["bas_fond"])
    except sol_module.SolIndisponible:
        envoyer(chat, "Je n'arrive pas à lire la carte des sols à cet endroit pour le moment. "
                      f"Réessaie dans quelques minutes avec le bouton « {B_PLAN} ».", reply_markup=CLAVIER)
        return
    s = d["sol"]
    groupes = {"conseillee": [], "possible": [], "deconseillee": []}
    for c in d["cultures"]:
        groupes[c["adaptation"]].append(c)
    dire(chat, "plan_intro")
    for c in groupes["conseillee"] + groupes["possible"]:
        dire(chat, f"culture_{c['culture']}_{c['adaptation']}")
    if e["eau_salee"] == "ne_sait_pas":
        dire(chat, "eau_salee")

    blocs = ["<b>Ce qu'il faut savoir sur ton sol</b>\n"
             "D'après la carte des sols iSDAsoil, ton champ "
             + (f"contient environ {round(s['sable_pct'])} % de sable " if s.get("sable_pct") is not None else "")
             + (f"et son pH est de {nombre_fr(s['ph'])} : {phrase_ph(s['ph'])}." if s.get("ph") is not None
                else "(pH inconnu à cet endroit).")]
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
    if e["eau_salee"] == "ne_sait_pas":
        blocs.append("<b>Une précaution importante</b>\nSi l'eau de ton puits est salée, évite l'oignon et la carotte.")
    blocs.append("<b>Ce que tu peux faire ensuite</b>\n"
                 f"Si une culture est déjà en place, touche « {B_ALERTES} » : je regarde si la météo de la "
                 "semaine favorise une maladie. Si tu vois des taches sur ta plante (feuille, fruit, tige), envoie-moi une photo.")
    blocs.append("<i>Sources : Guide pratique du maraîchage au Sénégal (ISRA, 1987) ; carte des sols iSDAsoil.</i>")
    dire(chat, "plan_suite")
    envoyer(chat, "\n\n".join(blocs), reply_markup=CLAVIER)


MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
           "novembre", "décembre")


def periode_fr(debut, fin) -> str:
    """« du 5 au 12 novembre » (ou « du 28 octobre au 4 novembre ») au lieu de « 2026-11-05 au 2026-11-12 »."""
    d, f = (x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10]) for x in (debut, fin))
    if d.month == f.month:
        return f"du {d.day} au {f.day} {MOIS_FR[f.month - 1]}"
    return f"du {d.day} {MOIS_FR[d.month - 1]} au {f.day} {MOIS_FR[f.month - 1]}"


def _alertes(chat: int):
    e = ETATS[chat]
    try:
        d = calculer(e["lat"], e["lon"], e["culture"], dt.date.today(), e.get("repiquage"))
    except meteo.MeteoIndisponible:
        envoyer(chat, "La météo est momentanément indisponible. Réessaie dans quelques minutes.",
                reply_markup=CLAVIER)
        return
    culture = CULTURES[e["culture"]]["libelle"].lower()
    if not d["alertes"]:  # aucune règle météo pour cette culture : ne pas dire « rien d'inquiétant »
        dire(chat, "alerte_pas_de_regle")
        envoyer(chat, f"<b>Pour ta culture ({escape(culture)}), je ne surveille pas encore la météo.</b>\n"
                      "Je n'ai pas de règle sourcée qui relie le temps aux maladies de cette culture.\n\n"
                      "<b>Ce que tu peux faire</b>\nSi tu vois des taches sur ta plante (feuille, fruit, tige), envoie-moi une photo.",
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
    # NASA POWER donne la météo MESURÉE (avec quelques jours de retard), pas une prévision : le titre le dit.
    blocs = [f"<b>Ce que la météo de ces derniers jours dit pour ta culture ({escape(culture)})</b>\n"
             f"J'ai regardé la météo de la zone de ton champ {periode_fr(debut, fin)}."]
    if actives:
        blocs.append("<b>Ce qu'il faut surveiller</b>\n" + _liste(actives))
    else:
        blocs.append("<b>Bonne nouvelle : rien d'inquiétant pour le moment</b>\nLa météo de ces derniers jours ne favorise aucune "
                     "des maladies ni aucun des ravageurs que je surveille pour cette culture.")
    blocs.append("<b>Ce que tu peux faire ensuite</b>\n"
                 f"Reviens me demander la semaine prochaine avec le bouton « {B_ALERTES} ». "
                 "Si tu vois des taches sur ta plante (feuille, fruit, tige), envoie-moi une photo.")
    blocs.append("<i>Météo : NASA POWER. Ces règles viennent d'études faites hors du Sénégal : je parle de "
                 "conditions favorables, pas de maladie certaine.</i>")
    if any(a["niveau"] == "date_requise" for a in d["alertes"]):
        e["date_libre"] = True  # la date pourra être écrite à n'importe quel moment
        blocs.append("<b>Pour surveiller aussi les insectes</b>\nÉcris-moi le jour où tu l'as plantée, "
                     "comme ça : <b>15/10</b> pour le 15 octobre.")
    envoyer(chat, "\n\n".join(blocs), reply_markup=CLAVIER)
    envoyer(chat, "Tu veux surveiller une autre culture ?",
            reply_markup={"inline_keyboard": [[{"text": "Changer de culture", "callback_data": "changer_culture"}]]})


def _choisir_culture(chat: int):
    wo = ETATS.get(chat, {}).get("langue") == "wo"
    boutons = [[{"text": f"{i}. {c['libelle']}" if wo else c["libelle"], "callback_data": f"culture:{k}"}]
               for i, (k, c) in enumerate(CULTURES.items(), 1)]
    dire(chat, "choix_culture")
    envoyer(chat, "<b>Quelle culture veux-tu que je surveille ?</b>\nChoisis-la dans la liste.",
            reply_markup={"inline_keyboard": boutons})


def _sans_position(chat: int):
    """État perdu (redémarrage du serveur après la veille de Render) : on redemande le champ."""
    dire(chat, "demande_position")
    envoyer(chat, DEMANDE_POSITION, reply_markup=CLAVIER)


def _telecharger(file_id: str) -> bytes:
    chemin = _appel("getFile", file_id=file_id)["result"]["file_path"]
    with urllib.request.urlopen(FICHIER.format(jeton=config.TELEGRAM_BOT_TOKEN, chemin=chemin), timeout=30) as r:
        return r.read()


def _vocal(chat: int, note: dict):
    """Question dite en wolof : transcription (Octopus), traduction (Gemini), puis réponse des fiches."""
    from ..modules import ecoute

    ecrire = "Tu peux aussi écrire ta question, ou utiliser les boutons en bas de l'écran."
    if not ecoute.disponible():
        dire(chat, "vocal_indisponible")
        envoyer(chat, f"Je ne peux pas écouter les messages vocaux pour le moment. {ecrire}", reply_markup=CLAVIER)
        return
    if (note.get("duration") or 0) > ecoute.DUREE_MAX:
        dire(chat, "vocal_trop_long")
        envoyer(chat, "Ta note vocale est trop longue pour moi. Pose ta question en moins d'une minute.",
                reply_markup=CLAVIER)
        return
    dire(chat, "vocal_ecoute")
    envoyer(chat, "J'écoute ta note vocale. Cela prend quelques secondes.")
    try:
        compris = ecoute.comprendre(_telecharger(note["file_id"]), note.get("mime_type") or "audio/ogg",
                                    note.get("duration"))
    except ecoute.NoteTropLongue:
        dire(chat, "vocal_trop_long")
        envoyer(chat, "Ta note vocale est trop longue pour moi. Pose ta question en moins d'une minute.",
                reply_markup=CLAVIER)
        return
    except Exception as e:  # Octopus indisponible, plafond du jour atteint, fichier illisible
        journal.info("note vocale non traitée : %s", type(e).__name__)
        dire(chat, "vocal_indisponible")
        envoyer(chat, f"Je ne peux pas écouter les messages vocaux pour le moment. {ecrire}", reply_markup=CLAVIER)
        return
    if not compris["francais"]:
        dire(chat, "vocal_non_compris")
        envoyer(chat, "Je n'ai pas bien compris ta note vocale. Peux-tu la redire plus lentement, dans un "
                      f"endroit calme ? {ecrire}", reply_markup=CLAVIER)
        return
    # L'agriculteur voit ce qui a été compris : s'il y a une erreur, il peut reformuler.
    envoyer(chat, f"<i>J'ai compris ta question ainsi : « {escape(compris['francais'])} »</i>")
    _question(chat, compris["francais"])


def _photo(chat: int, file_id: str, culture: str | None):
    from ..modules.diagnostic import modele

    dire(chat, "attente_photo")
    envoyer(chat, "Merci, je regarde ta photo. Cela prend quelques secondes.")
    try:
        res = modele.diagnostiquer(_telecharger(file_id), culture)
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
        envoyer(chat, "<b>Bonne nouvelle : ce que je vois semble sain.</b>\n"
                      "Je ne vois pas de signe de maladie sur cette photo.\n\n"
                      "<b>Ce que tu peux faire ensuite</b>\nSi d'autres plants ont des taches, envoie-moi leur photo."
                      + _verifier_aussi(top.get("culture")),
                reply_markup=CLAVIER)
        return
    tete = ("<b>Ce que je vois sur ta photo</b>\n"
            f"Cela ressemble à : <b>{escape(top['libelle'])}</b> "
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
        envoyer(chat, f"{tete}\n\nJe n'ai pas encore de fiche sur ce problème.\n\n{suite}"
                      + _verifier_aussi(top.get("culture")), reply_markup=CLAVIER)
        return
    corps, sources = fiche
    envoyer(chat, f"{tete}\n\n{corps}\n\n{suite}{_verifier_aussi(top.get('culture'))}\n\n{sources}",
            reply_markup=CLAVIER)


def _verifier_aussi(culture: str | None) -> str:
    """Ravageurs invisibles pour le modèle (mineuse de la tomate) : la question oui/non de la fiche."""
    from .v1 import questions_suivi

    return "".join(f"\n\n<b>À vérifier aussi</b>\n{escape(q['question'])}\n<i>Si oui : {escape(q['si_oui'])}</i>"
                   for q in questions_suivi(culture))


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
    documents = sorted({c for s in fiche["sources"] if (c := _court(s["document"]))})
    return "\n\n".join(blocs), "<i>Sources : " + escape(" ; ".join(documents)) + "</i>"


def _dire_reponse_wolof(chat: int, texte_fr: str):
    """Réponse libre dite en wolof (traduite puis lue par Octopus) ; le texte français suit toujours."""
    from ..modules import parole

    audio = parole.dire_en_wolof(texte_fr.replace("**", ""))
    if not audio:
        return
    try:
        _envoyer_fichier("sendVoice", chat, "voice", Path("reponse.mp3"), octets=audio)
    except Exception as e:
        journal.warning("réponse vocale non envoyée : %s", type(e).__name__)


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
                      "• Regarder la photo de ta plante malade.", reply_markup=CLAVIER)
        return
    if ETATS.get(chat, {}).get("langue") == "wo":
        _dire_reponse_wolof(chat, r["texte"])
    sources = " ; ".join(_court(s["document"]) + (f", p. {s['page']}" if s["page"][:1].isdigit() else "")
                         for s in [x for x in r["sources"] if _court(x["document"])][:3])
    reponse = escape(r["texte"].replace("**", ""))
    envoyer(chat, f"{reponse}\n\n<i>Sources : {escape(sources)}</i>", reply_markup=CLAVIER)


def traiter(maj: dict):
    if "callback_query" in maj:
        q = maj["callback_query"]
        _appel_silencieux("answerCallbackQuery", callback_query_id=q["id"])
        chat = ((q.get("message") or {}).get("chat") or {}).get("id") or (q.get("from") or {}).get("id")
        if chat is None:
            return
        donnee = q.get("data", "")
        cle, _, reponse = donnee.partition(":")
        if cle in CHAMP_ETAT and reponse in ("oui", "non", "ne_sait_pas"):
            ETATS.setdefault(chat, {})[CHAMP_ETAT[cle]] = reponse
            if "lat" in ETATS[chat]:
                _plan(chat)
            else:
                _sans_position(chat)
            return
        if donnee == "changer_culture":
            _choisir_culture(chat)
            return
        if donnee in ("langue:wo", "langue:fr"):
            ETATS.setdefault(chat, {})["langue"] = donnee[-2:]
            dire(chat, "accueil")
            envoyer(chat, ACCUEIL, reply_markup=CLAVIER)
            return
        culture = donnee.removeprefix("culture:")
        if culture in CULTURES:
            ETATS.setdefault(chat, {})["culture"] = culture
            ETATS[chat]["attend_date"], ETATS[chat]["date_libre"] = True, False
            ETATS[chat].pop("repiquage", None)
            dire(chat, "date_repiquage")
            envoyer(chat, f"C'est noté : {escape(CULTURES[culture]['libelle'].lower())}.\n\n"
                          "<b>Une dernière question pour bien te conseiller</b>\nTu l'as plantée quand ? "
                          "Écris-moi le jour comme ça : <b>15/10</b> pour le 15 octobre. "
                          "Si tu ne t'en souviens plus, écris juste : <b>je ne sais pas</b>.")
        return
    msg = maj.get("message") or {}
    chat = (msg.get("chat") or {}).get("id")
    if chat is None:
        return
    etat = ETATS.setdefault(chat, {})
    texte = (msg.get("text") or "").strip()
    texte = ANCIENS_BOUTONS.get(texte, texte)
    for bouton, numero in NUMEROS.items():  # bouton numéroté (clavier wolof) → même action
        if texte in (f"{numero}. {bouton}", str(numero)):
            texte = bouton

    if "location" in msg:
        etat["lat"] = round(msg["location"]["latitude"], 2)
        etat["lon"] = round(msg["location"]["longitude"], 2)
        dire(chat, "position_recue")
        envoyer(chat, "C'est bon, j'ai bien reçu la position de ton champ.")
        _plan(chat)
    elif texte == B_POSITION_TEST and AVEC_POSITION_TEST and "langue" in etat:
        etat["lat"], etat["lon"] = POSITION_TEST["lat"], POSITION_TEST["lon"]
        dire(chat, "position_recue")
        envoyer(chat, f"Position test : {POSITION_TEST['nom']}, dans la zone pilote des Niayes. "
                      "C'est un bouton de démonstration ; pour ton vrai champ, utilise « " + B_POSITION + " ».")
        _plan(chat)
    elif msg.get("photo"):
        # Pas de filtre par la culture surveillée : la feuille peut venir d'une autre culture.
        _photo(chat, msg["photo"][-1]["file_id"], None)
    elif msg.get("voice") or msg.get("audio"):
        _vocal(chat, msg.get("voice") or msg["audio"])
    elif texte.startswith(("/start", "/langue")) or ("langue" not in etat and not etat.get("attend_date")):
        dire(chat, "choix_langue", toujours=True)  # la question est aussi dite en wolof
        envoyer(chat, CHOIX_LANGUE, reply_markup=CLAVIER_LANGUE)
    elif texte == B_AIDE:
        dire(chat, "accueil")
        envoyer(chat, ACCUEIL + "\n\n<i>Pour changer de langue, écris /langue.</i>", reply_markup=CLAVIER)
    elif texte == B_QUESTION:
        dire(chat, "invite_question")
        envoyer(chat, "Je t'écoute. Pose-moi ta question par écrit (en français), ou envoie-moi un message "
                      "vocal en wolof.", reply_markup=CLAVIER)
    elif texte == B_PHOTO:
        dire(chat, "conseils_photo")
        envoyer(chat, "<b>Envoie-moi une photo de ta plante, là où quelque chose t'inquiète.</b>\n"
                      "Touche le petit bouton rond tout à gauche de la case « Message », juste au-dessus des grands boutons. "
                      "Choisis ensuite « Appareil photo » pour prendre la photo maintenant, ou une photo déjà prise dans ta galerie.\n\n"
                      "<b>Pour une photo bien lisible</b>\n" + CONSEILS_PHOTO, reply_markup=CLAVIER)
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
            _choisir_culture(chat)
    elif etat.get("attend_date") and re.fullmatch(r"((je )?ne sais (pas|plus)|xamu ?ma|xamu ?ma ko)\s*[.!]?", texte.lower()):
        etat["repiquage"], etat["attend_date"] = None, False
        dire(chat, "date_ignoree")
        envoyer(chat, "Pas de souci, je fais sans la date.")
        if "lat" in etat:
            _alertes(chat)
        else:
            _sans_position(chat)
    elif ((etat.get("attend_date") or etat.get("date_libre")) and "culture" in etat
          and (m := re.fullmatch(r"(\d{1,2})[/.\- ](\d{1,2})", texte))):
        aujourdhui = dt.date.today()
        jour, mois = int(m.group(1)), int(m.group(2))
        try:
            date = dt.date(aujourdhui.year - (mois > aujourdhui.month), mois, jour)
        except ValueError:
            dire(chat, "date_incomprise")
            envoyer(chat, "Je n'ai pas compris la date. Écris-la comme ceci : <b>15/10</b> pour le 15 octobre.")
            return
        if date > aujourdhui:
            dire(chat, "date_future")
            envoyer(chat, "Cette date n'est pas encore arrivée. Écris le jour où tu as planté, "
                          "par exemple <b>15/10</b> pour le 15 octobre.")
            return
        etat["repiquage"], etat["attend_date"], etat["date_libre"] = date, False, False
        if "lat" in etat:
            _alertes(chat)
        else:
            _sans_position(chat)
    elif texte:
        _question(chat, texte)


def traiter_sans_planter(maj: dict):
    """Une erreur imprévue ne doit pas laisser l'agriculteur sans réponse."""
    try:
        traiter(maj)
    except Exception as e:
        # Type et ligne seulement : le texte de l'erreur pourrait contenir un message de l'agriculteur.
        ou = traceback.extract_tb(e.__traceback__)[-1]
        journal.error("message non traité : %s (%s:%s)", type(e).__name__, Path(ou.filename).name, ou.lineno)
        q = maj.get("callback_query") or {}
        chat = (((maj.get("message") or q.get("message") or {}).get("chat") or {}).get("id")
                or (q.get("from") or {}).get("id"))
        if chat is not None:
            _appel_silencieux("sendMessage", chat_id=chat, text="Désolé, un problème m'a empêché de répondre. "
                              "Réessaie dans un instant.")
    finally:
        _limiter_etats()


ETATS_MAX = 5000  # agriculteurs gardés en mémoire ; au-delà, on oublie les plus anciens


def _limiter_etats():
    while len(ETATS) > ETATS_MAX:
        ETATS.pop(next(iter(ETATS)))


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
    if not x_telegram_bot_api_secret_token or not hmac.compare_digest(x_telegram_bot_api_secret_token.encode(), secret.encode()):
        raise HTTPException(403, "secret invalide")
    # Réponse immédiate à Telegram ; le travail (sol, météo, photo) se fait ensuite.
    taches.add_task(traiter_sans_planter, await request.json())
    return {"ok": True}
