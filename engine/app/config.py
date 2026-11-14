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



# Bot Telegram (D12) : jeton de @BotFather et secret partagé de l'en-tête du webhook.
TELEGRAM_BOT_TOKEN = valeur("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = valeur("TELEGRAM_WEBHOOK_SECRET")

# Modèle de langage du RAG (D8, D9) : Google Gemini.
GEMINI_API_KEY = valeur("GEMINI_API_KEY")

# Écoute des notes vocales en wolof : Octopus ASR (plateforme du PAS Challenge). Jeton Bearer et
# projet sponsorisé de l'équipe (les crédits du challenge y sont rattachés). Sans jeton : désactivé.
OCTOPUS_API_KEY = valeur("OCTOPUS_API_KEY")
OCTOPUS_PROJECT_ID = valeur("OCTOPUS_PROJECT_ID")
OCTOPUS_URL = valeur("OCTOPUS_URL", "https://www.octoopus.dev").rstrip("/")
OCTOPUS_MINUTES_PAR_JOUR = float(valeur("OCTOPUS_MINUTES_PAR_JOUR", "20") or 20)
