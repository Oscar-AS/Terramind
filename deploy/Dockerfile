# Moteur TerraMind en conteneur (hébergement : Render, offre gratuite, sans carte bancaire).
# L'hébergeur fournit le port dans la variable PORT ; 8000 par défaut en local.
# Les secrets (WHATSAPP_TOKEN, WHATSAPP_APP_SECRET, ...) sont définis dans les variables d'environnement
# de l'hébergeur, jamais dans ce dépôt.
#   docker build -f deploy/Dockerfile -t terramind-moteur .
#   docker run -p 8000:8000 --env-file .env terramind-moteur
FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /home/user/app

COPY --chown=user engine/requirements.txt engine/requirements.txt
RUN pip install --no-cache-dir --user -r engine/requirements.txt
COPY --chown=user engine/ engine/
# Fiches du RAG (D8).
COPY --chown=user content/fiches/ content/fiches/
# Notes vocales wolof préparées à l'avance (D10) ; le dossier peut être vide au début.
COPY --chown=user content/audio/wo/ content/audio/wo/
# Modèle de diagnostic (ONNX + étiquettes + calibration), produit par ml/training/ ; hors Git.
COPY --chown=user modeles/diagnostic/ modeles/diagnostic/

CMD ["sh", "-c", "uvicorn engine.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
