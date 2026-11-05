# Moteur TerraMind sur Hugging Face Spaces (SDK Docker). Spaces attend une application sur le port 7860.
# Les secrets (WHATSAPP_TOKEN, WHATSAPP_APP_SECRET, ...) sont définis dans Settings > Variables and secrets
# de l'espace, jamais dans ce dépôt.
FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /home/user/app

COPY --chown=user engine/requirements.txt engine/requirements.txt
RUN pip install --no-cache-dir --user -r engine/requirements.txt
COPY --chown=user engine/ engine/

EXPOSE 7860
CMD ["uvicorn", "engine.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
