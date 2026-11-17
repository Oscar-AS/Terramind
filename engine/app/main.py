"""Moteur TerraMind (FastAPI). Lancer en local depuis la racine :

    .venv/bin/uvicorn engine.app.main:app --reload --port 8000

Points d'entrée métier /v1 (docs/api.md) : plan, alertes, diagnostic photo, question, retour.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .responses.voix import catalogue
from .routes import telegram, v1

# Journaux du moteur visibles dans les logs de l'hébergeur (niveau INFO).
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s : %(message)s")

app = FastAPI(title="TerraMind Afrique, moteur", version="0.2.0")
# L'application web (Expo web) appelle le moteur depuis le navigateur : CORS ouvert en lecture/écriture
# simple, sans cookie ni jeton (aucune donnée de session).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(v1.router)
app.include_router(telegram.router)
# Notes vocales wolof relues (content/audio/wo/), écoutées par l'application en mode wolof.
if catalogue.AUDIO_WO.is_dir():
    app.mount("/audio/wo", StaticFiles(directory=catalogue.AUDIO_WO), name="audio_wo")


@app.get("/sante")
def sante():
    return {"statut": "ok", "mock": False}
