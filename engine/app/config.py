"""Configuration du moteur, lue dans les variables d'environnement (fichier .env en local).

Aucun secret n'est écrit dans le code. Modèle des variables : .env.example à la racine.
"""

import os
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def _charger_env(chemin=RACINE / ".env"):
    """Charge .env sans dépendance externe ; les variables déjà définies (hébergeur) gardent la priorité."""
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if "=" in ligne and not ligne.lstrip().startswith("#"):
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"'))


_charger_env()


def valeur(cle, defaut=""):
    return os.environ.get(cle, defaut).strip()


WHATSAPP_TOKEN = valeur("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = valeur("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_APP_SECRET = valeur("WHATSAPP_APP_SECRET")
WHATSAPP_VERIFY_TOKEN = valeur("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_API_VERSION = valeur("WHATSAPP_API_VERSION") or "v21.0"
