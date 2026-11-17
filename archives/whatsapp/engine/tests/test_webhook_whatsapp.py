"""Tests du webhook WhatsApp (J1). Aucun appel réel à Meta : l'envoi est remplacé par une fonction factice.

Lancer depuis la racine : .venv/bin/python -m unittest discover engine/tests
Ignoré automatiquement si FastAPI n'est pas installé.
"""

import hashlib
import hmac
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from fastapi.testclient import TestClient

    from engine.app import config
    from engine.app.main import app
except ImportError:  # environnement sans FastAPI
    TestClient = None

SECRET, JETON = "secret-de-test", "jeton-de-test"
MESSAGE = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "messages": [
                            {
                                "from": "221700000000",
                                "type": "text",
                                "text": {"body": "Salamalekum"},
                            },
                            {"from": "221700000000", "type": "image", "image": {"id": "x"}},
                        ]
                    }
                }
            ]
        }
    ]
}


@unittest.skipIf(TestClient is None, "FastAPI absent")
class Webhook(unittest.TestCase):
    def setUp(self):
        self.anciens = (config.WHATSAPP_APP_SECRET, config.WHATSAPP_VERIFY_TOKEN)
        config.WHATSAPP_APP_SECRET, config.WHATSAPP_VERIFY_TOKEN = SECRET, JETON
        self.envoyes = []

        async def faux_envoi(destinataire, texte, client):
            self.envoyes.append((destinataire, texte))

        app.state.envoyer_texte = faux_envoi
        self.client = TestClient(app)

    def tearDown(self):
        config.WHATSAPP_APP_SECRET, config.WHATSAPP_VERIFY_TOKEN = self.anciens
        del app.state.envoyer_texte

    def _post(self, corps, signature=None):
        brut = json.dumps(corps).encode()
        sig = signature or "sha256=" + hmac.new(SECRET.encode(), brut, hashlib.sha256).hexdigest()
        return self.client.post(
            "/webhook/whatsapp",
            content=brut,
            headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
        )

    def test_verification_meta(self):
        ok = self.client.get(
            "/webhook/whatsapp",
            params={"hub.mode": "subscribe", "hub.verify_token": JETON, "hub.challenge": "1234"},
        )
        self.assertEqual((ok.status_code, ok.text), (200, "1234"))
        ko = self.client.get(
            "/webhook/whatsapp",
            params={"hub.mode": "subscribe", "hub.verify_token": "faux", "hub.challenge": "1234"},
        )
        self.assertEqual(ko.status_code, 403)

    def test_echo_seulement_si_signature_valide(self):
        r = self._post(MESSAGE)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(self.envoyes), 1)  # le message image est ignoré en J1
        self.assertIn("Salamalekum", self.envoyes[0][1])
        self.assertEqual(self._post(MESSAGE, signature="sha256=00").status_code, 401)
        self.assertEqual(len(self.envoyes), 1)

    def test_refus_sans_secret(self):
        config.WHATSAPP_APP_SECRET = ""
        self.assertEqual(self._post(MESSAGE).status_code, 503)
        self.assertEqual(self.envoyes, [])


if __name__ == "__main__":
    unittest.main()
