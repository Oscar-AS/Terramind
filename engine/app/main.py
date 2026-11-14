"""Moteur TerraMind (FastAPI). Lancer en local depuis la racine :

    .venv/bin/uvicorn engine.app.main:app --reload --port 8000

Points d'entrée :
- GET /sante
- POST /v1/plan (et /plan) : module Planification (sol iSDAsoil + cultures maraîchères)
- POST /v1/alert (et /alert) : module Prévention (NASA POWER + Hutton plafonné, TOMCAST, degrés-jours)
- GET/POST /webhook/whatsapp : canal WhatsApp
"""

from fastapi import FastAPI

from .routes import agronomie, whatsapp

app = FastAPI(title="TerraMind Afrique, moteur", version="0.1.0")
app.include_router(whatsapp.router)
app.include_router(agronomie.router)


@app.get("/sante")
def sante():
    return {"statut": "ok", "mock": False}
