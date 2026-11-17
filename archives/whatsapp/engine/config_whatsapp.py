"""Variables WhatsApp, à recoller dans engine/app/config.py pour réactiver le bot (voir README)."""

from engine.app.config import valeur

WHATSAPP_TOKEN = valeur("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = valeur("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_APP_SECRET = valeur("WHATSAPP_APP_SECRET")
WHATSAPP_VERIFY_TOKEN = valeur("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_API_VERSION = valeur("WHATSAPP_API_VERSION") or "v27.0"
