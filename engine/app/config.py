"""Configuration du moteur, lue dans les variables d'environnement (fichier .env en local).

Aucun secret n'est écrit dans le code. Modèle des variables : .env.example à la racine.
"""

import os
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def _charger_env(chemin=RACINE / ".env"):
    """Charge .env sans dépendance externe. Une valeur remplie dans .env l'emporte sur l'environnement
    du poste (évite d'utiliser par erreur une clé personnelle définie ailleurs) ; l'hébergeur n'a pas de
    fichier .env, ses variables s'appliquent donc telles quelles."""
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            cle, valeur = cle.strip(), valeur.strip().strip('"')
            if valeur:
                os.environ[cle] = valeur
            else:
                os.environ.setdefault(cle, valeur)


_charger_env()


def valeur(cle, defaut=""):
    return os.environ.get(cle, defaut).strip()


WHATSAPP_TOKEN = valeur("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = valeur("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_APP_SECRET = valeur("WHATSAPP_APP_SECRET")
WHATSAPP_VERIFY_TOKEN = valeur("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_API_VERSION = valeur("WHATSAPP_API_VERSION") or "v27.0"

# Bot Telegram (D12) : jeton de @BotFather et secret partagé de l'en-tête du webhook.
TELEGRAM_BOT_TOKEN = valeur("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = valeur("TELEGRAM_WEBHOOK_SECRET")

# Modèle de langage du RAG (D8, D9) : Google Gemini.
GEMINI_API_KEY = valeur("GEMINI_API_KEY")
