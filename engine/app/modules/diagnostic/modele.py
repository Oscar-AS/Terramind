"""Diagnostic photo (POST /v1/diagnose) avec le modèle v0 exporté en ONNX.

Modèle et étiquettes : modeles/diagnostic/ (hors Git), produits par
ml/training/entrainer_diagnostic.py puis ml/training/exporter_onnx.py.
Le seuil d'incertitude est volontairement prudent : sous le seuil, aucune maladie n'est
annoncée (statut « incertain »).
"""

from __future__ import annotations

import io
import json
import os
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parents[4]
DOSSIER = Path(os.environ.get("MODEL_PATH") or RACINE / "modeles" / "diagnostic")
SEUIL_INCERTAIN = 0.6  # repli si ni variable d'environnement ni calibration
TAILLE = 224
MOYENNE = np.array([0.485, 0.456, 0.406], dtype=np.float32)
ECART = np.array([0.229, 0.224, 0.225], dtype=np.float32)
# Mémoire limitée (Render gratuit, 512 Mo). Une photo JPEG de téléphone (12 à 108 millions de pixels) est
# décodée directement à taille réduite (draft) ; les autres formats (PNG…) sont décodés en entier, donc
# limités à 25 millions de pixels. Au-delà de 120 millions, Pillow refuse avant tout décodage.
Image.MAX_IMAGE_PIXELS = 120_000_000
PIXELS_MAX_NON_JPEG = 25_000_000
COTE_MIN = 64  # en dessous, la photo est agrandie plus de 3 fois : le modèle ne verrait que du flou
_VERROU = threading.Lock()  # un seul chargement du modèle, même si deux photos arrivent en même temps

# Libellés français et catégories, au format de data/label_mapping.csv (branche d'Oscar).
LIBELLES = {
    "healthy": ("sain", "Feuille saine"),
    "alternaria": ("maladie", "Alternariose"),
    "late_blight": ("maladie", "Mildiou"),
    "bacterial_spot": ("maladie", "Tache bactérienne"),
    "leaf_mold": ("maladie", "Cladosporiose"),
    "septoria_leaf_spot": ("maladie", "Septoriose"),
    "target_spot": ("maladie", "Tache cible (corynesporiose)"),
    "leaf_curl": ("maladie", "Enroulement jaune (virus TYLCV)"),
    "mosaic_virus": ("maladie", "Mosaïque (virus)"),
    "mites": ("ravageur", "Acariens"),
    "virosis": ("maladie", "Virose"),
    "bacterial_wilt": ("maladie", "Flétrissement bactérien"),
    "fusarium": ("maladie", "Fusariose"),
    "caterpillars": ("ravageur", "Chenilles"),
    "helicoverpa_armigera": ("ravageur", "Noctuelle de la tomate"),
    "blossom_end_rot": ("abiotique", "Cul noir du fruit (nécrose apicale)"),
    "sunburn": ("abiotique", "Coup de soleil sur le fruit"),
    "healthy_fruit": ("sain", "Fruit sain"),
}
CULTURES_FR = {"tomato": "tomate", "potato": "pomme de terre", "pepper": "poivron", "onion": "oignon"}


class ModeleAbsent(RuntimeError):
    pass


def _charger():
    with _VERROU:
        return _charger_une_fois()


@lru_cache(maxsize=1)
def _charger_une_fois():
    import onnxruntime as ort  # import tardif : le moteur démarre même sans modèle

    fichier = next((DOSSIER / n for n in ("terramind_diag.onnx", "terramind_diag_v0.onnx") if (DOSSIER / n).exists()), None)
    if fichier is None:
        raise ModeleAbsent(f"modèle introuvable dans {DOSSIER}")
    session = ort.InferenceSession(str(fichier), providers=["CPUExecutionProvider"])
    etiquettes = json.loads((DOSSIER / "etiquettes.json").read_text())
    # Calibration (v1) : température choisie sur la validation de terrain, seuil d'incertitude.
    calib = DOSSIER / "calibration.json"
    reglage = json.loads(calib.read_text()) if calib.exists() else {}
    return session, etiquettes, float(reglage.get("temperature", 1.0)), reglage.get("seuil_incertain")


def _preparer(contenu: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(contenu))
    if image.format == "JPEG":
        image.draft("RGB", (512, 512))  # décodage à taille réduite, côté court ≥ 512 (le modèle utilise 256)
    elif image.size[0] * image.size[1] > PIXELS_MAX_NON_JPEG:
        raise ValueError("image trop grande")
    if min(image.size) < COTE_MIN:  # vignette ou image tronquée : on ne devine rien (idée reprise d'Oscar)
        raise ValueError("image trop petite")
    image = image.convert("RGB")
    l, h = image.size
    echelle = 256 / min(l, h)  # même traitement que la validation : 256 puis centre 224
    image = image.resize((max(TAILLE, round(l * echelle)), max(TAILLE, round(h * echelle))), Image.BILINEAR)
    l, h = image.size
    g, haut = (l - TAILLE) // 2, (h - TAILLE) // 2
    image = image.crop((g, haut, g + TAILLE, haut + TAILLE))
    x = (np.asarray(image, dtype=np.float32) / 255.0 - MOYENNE) / ECART
    return x.transpose(2, 0, 1)[None].astype(np.float32)


def diagnostiquer(contenu: bytes, culture: str | None = None) -> dict:
    session, etiquettes, temperature, seuil_calibre = _charger()
    seuil = float(os.environ.get("DIAGNOSTIC_CONFIDENCE_THRESHOLD") or seuil_calibre or SEUIL_INCERTAIN)
    logits = session.run(None, {session.get_inputs()[0].name: _preparer(contenu)})[0][0] / temperature
    if culture:  # culture déclarée : on ne garde que ses classes
        masque = np.array([e["culture"] == culture for e in etiquettes])
        if masque.any():
            logits = np.where(masque, logits, -np.inf)
    p = np.exp(logits - logits.max())
    p = p / p.sum()
    predictions = []
    for i in np.argsort(-p)[:3]:
        e = etiquettes[int(i)]
        categorie, libelle = LIBELLES[e["etiquette"]]
        predictions.append({"culture": e["culture"], "etiquette": e["etiquette"], "categorie": categorie,
                            "libelle": libelle, "confiance": round(float(p[i]), 3)})
    return {"predictions": predictions, "seuil_incertain": seuil,
            "fiche": None, "questions_suivi": [],
            "certain": predictions[0]["confiance"] >= seuil}
