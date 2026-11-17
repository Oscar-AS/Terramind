"""Webhook WhatsApp Cloud API (jalon J1 : bot en écho).

- GET  /webhook/whatsapp : vérification de l'adresse par Meta (hub.verify_token, hub.challenge).
- POST /webhook/whatsapp : messages entrants. La signature X-Hub-Signature-256 (HMAC SHA-256 du corps avec
  le secret de l'app) est vérifiée AVANT toute lecture ; sans secret configuré, on refuse (503) plutôt que
  d'accepter des requêtes non authentifiées.

En J1, un message texte reçoit un écho marqué comme réponse de démonstration (mock). Aucun numéro ni contenu
n'est enregistré à ce stade. Les vrais modules (planification, prévention, diagnostic) remplaceront l'écho.
"""

import hashlib
import hmac
import json
import logging

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from .. import config

journal = logging.getLogger("terramind.whatsapp")
router = APIRouter()

MESSAGE_ECHO = (
    "TerraMind (démonstration) : j'ai bien reçu « {texte} ». Les vrais conseils arrivent bientôt."
)


@router.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def verifier(request: Request):
    p = request.query_params
    if (
        p.get("hub.mode") == "subscribe"
        and config.WHATSAPP_VERIFY_TOKEN
        and hmac.compare_digest(p.get("hub.verify_token", ""), config.WHATSAPP_VERIFY_TOKEN)
    ):
        return p.get("hub.challenge", "")
    raise HTTPException(status_code=403, detail="jeton de vérification invalide")


def signature_valide(corps: bytes, entete: str, secret: str) -> bool:
    if not secret or not entete.startswith("sha256="):
        return False
    attendu = hmac.new(secret.encode(), corps, hashlib.sha256).hexdigest()
    return hmac.compare_digest(entete[len("sha256=") :], attendu)


def messages_texte(donnees: dict):
    """Extrait (expéditeur, texte) des messages texte d'une notification WhatsApp."""
    for entree in donnees.get("entry", []):
        for changement in entree.get("changes", []):
            for m in changement.get("value", {}).get("messages", []):
                if m.get("type") == "text":
                    yield m.get("from", ""), m.get("text", {}).get("body", "")


async def envoyer_texte(destinataire: str, texte: str, client: httpx.AsyncClient):
    url = (
        f"https://graph.facebook.com/{config.WHATSAPP_API_VERSION}/"
        f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    r = await client.post(
        url,
        headers={"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": destinataire,
            "type": "text",
            "text": {"body": texte[:4096]},
        },
    )
    if r.status_code >= 400:
        # Code et message d'erreur de Meta seulement : jamais le numéro ni le texte.
        try:
            erreur = r.json().get("error", {})
        except ValueError:
            erreur = {}
        journal.warning(
            "échec d'envoi WhatsApp : HTTP %s, code %s, %s",
            r.status_code,
            erreur.get("code"),
            erreur.get("message", "")[:200],
        )
    else:
        journal.info("réponse WhatsApp envoyée (HTTP %s)", r.status_code)


@router.post("/webhook/whatsapp")
async def recevoir(request: Request):
    if not config.WHATSAPP_APP_SECRET:
        raise HTTPException(status_code=503, detail="secret de l'app non configuré")
    corps = await request.body()
    if not signature_valide(
        corps, request.headers.get("X-Hub-Signature-256", ""), config.WHATSAPP_APP_SECRET
    ):
        raise HTTPException(status_code=401, detail="signature invalide")
    donnees = json.loads(corps or b"{}")
    envoyeur = getattr(request.app.state, "envoyer_texte", envoyer_texte)
    messages = list(messages_texte(donnees))
    champs = [c.get("field") for e in donnees.get("entry", []) for c in e.get("changes", [])]
    journal.info("notification reçue : champs %s, %d message(s) texte", champs, len(messages))
    for e in donnees.get("entry", []):
        for c in e.get("changes", []):
            for st in c.get("value", {}).get("statuses", []):
                # Statut de nos réponses (sent, delivered, read, failed) et codes d'erreur Meta seulement.
                erreurs = [(x.get("code"), x.get("title", "")[:120]) for x in st.get("errors", [])]
                journal.info("statut de réponse : %s %s", st.get("status"), erreurs or "")
    async with httpx.AsyncClient(timeout=15) as client:
        for expediteur, texte in messages:
            await envoyeur(expediteur, MESSAGE_ECHO.format(texte=texte[:200]), client)
    return {"statut": "recu", "mock": True}
