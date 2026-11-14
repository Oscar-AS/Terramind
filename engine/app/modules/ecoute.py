"""Comprendre une question dite en wolof (note vocale) : transcription puis traduction en français.

1. Transcription : Octopus ASR (plateforme du PAS Challenge), langue wolof. Facturé à la minute
   (0,20 $/min, grille publique d'Octopus) sur le projet sponsorisé de l'équipe : on refuse les
   notes de plus d'une minute et on plafonne le total de minutes par jour (OCTOPUS_MINUTES_PAR_JOUR).
2. Traduction : Gemini traduit la transcription en français, puis la question suit le chemin habituel
   des fiches (RAG, D8). Le texte compris est montré à l'agriculteur pour qu'il puisse vérifier.

Rien n'est conservé : ni l'audio, ni la transcription ; les journaux ne contiennent que des durées.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .. import config

journal = logging.getLogger("terramind.ecoute")
DUREE_MAX = 60  # secondes par note vocale
CONSIGNE_TRADUCTION = (
    "Tu reçois la transcription automatique d'une question posée oralement, en wolof, par un petit "
    "maraîcher du Sénégal. La transcription peut contenir des erreurs, des mots français et des noms de "
    "cultures ou de maladies. Traduis la question en français simple, fidèlement, sans rien ajouter. "
    "Réponds uniquement par la traduction, sur une seule ligne. "
    "Si le texte n'a pas de sens compréhensible, réponds exactement : INCOMPRIS"
)


class EcouteIndisponible(Exception):
    """Octopus non configuré, plafond du jour atteint ou service en panne."""


class NoteTropLongue(Exception):
    pass


class _Compteur:
    """Secondes transcrites aujourd'hui (en mémoire : remis à zéro au redémarrage du serveur)."""

    def __init__(self):
        self.jour, self.secondes, self.verrou = dt.date.today(), 0.0, threading.Lock()

    def reserver(self, secondes: float) -> None:
        with self.verrou:
            if self.jour != dt.date.today():
                self.jour, self.secondes = dt.date.today(), 0.0
            if self.secondes + secondes > config.OCTOPUS_MINUTES_PAR_JOUR * 60:
                raise EcouteIndisponible("plafond du jour atteint")
            self.secondes += secondes

    def corriger(self, reservees: float, reelles: float) -> None:
        with self.verrou:
            self.secondes += reelles - reservees


COMPTEUR = _Compteur()


def disponible() -> bool:
    return bool(config.OCTOPUS_API_KEY and config.OCTOPUS_PROJECT_ID)


def transcrire(audio: bytes, type_mime: str, duree_annoncee: float | None = None) -> str:
    """Texte wolof dit dans la note vocale ("" si rien n'est reconnu)."""
    if not disponible():
        raise EcouteIndisponible("Octopus non configuré")
    if duree_annoncee is not None and duree_annoncee > DUREE_MAX:
        raise NoteTropLongue()
    reservees = float(duree_annoncee or DUREE_MAX)
    COMPTEUR.reserver(reservees)
    borne = "tm-" + uuid.uuid4().hex
    corps = (f"--{borne}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"note\"\r\n"
             f"Content-Type: {type_mime}\r\n\r\n").encode() + audio + f"\r\n--{borne}--\r\n".encode()
    requete = urllib.parse.urlencode({"project_id": config.OCTOPUS_PROJECT_ID, "language": "wo"})
    req = urllib.request.Request(f"{config.OCTOPUS_URL}/api/voice/transcribe?{requete}", data=corps,
                                 headers={"Authorization": f"Bearer {config.OCTOPUS_API_KEY}",
                                          # le pare-feu d'Octopus refuse l'agent par défaut « Python-urllib » (403)
                                          "User-Agent": "TerraMind-moteur/0.2",
                                          "Content-Type": f"multipart/form-data; boundary={borne}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        COMPTEUR.corriger(reservees, 0)
        journal.warning("Octopus a refusé la transcription : HTTP %s", e.code)
        raise EcouteIndisponible(f"HTTP {e.code}") from e
    except Exception as e:
        COMPTEUR.corriger(reservees, 0)
        journal.warning("Octopus injoignable : %s", type(e).__name__)
        raise EcouteIndisponible(type(e).__name__) from e
    duree = float(d.get("duration_seconds") or reservees)
    COMPTEUR.corriger(reservees, duree)
    if duree > DUREE_MAX + 1:
        journal.info("note vocale plus longue qu'annoncé : %.0f s", duree)
    journal.info("note vocale transcrite : %.0f s (aujourd'hui : %.0f s)", duree, COMPTEUR.secondes)
    return (d.get("text") or "").strip()


def traduire(texte_wo: str) -> str | None:
    """Traduction française de la question, ou None si elle n'est pas compréhensible."""
    from .rag.reponse import gemini

    if not texte_wo:
        return None
    fr = gemini(CONSIGNE_TRADUCTION, texte_wo, delai=20)
    if not fr or "INCOMPRIS" in fr:
        return None
    return fr.strip().strip("«»\"").strip()


def comprendre(audio: bytes, type_mime: str, duree_annoncee: float | None = None) -> dict:
    """{"wolof": transcription, "francais": traduction ou None}. Lève EcouteIndisponible ou NoteTropLongue."""
    wo = transcrire(audio, type_mime, duree_annoncee)
    return {"wolof": wo, "francais": traduire(wo)}
