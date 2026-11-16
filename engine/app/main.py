"""Moteur TerraMind (FastAPI). Lancer en local depuis la racine :

    .venv/bin/uvicorn engine.app.main:app --reload --port 8000

Jalon J1 : santé du service et webhook WhatsApp en écho. Les modules métier arrivent au jalon J2.
"""

from fastapi import FastAPI

from .routes import whatsapp

app = FastAPI(title="TerraMind Afrique, moteur", version="0.1.0")
app.include_router(whatsapp.router)


@app.get("/sante")
def sante():
    return {"statut": "ok", "mock": True}
