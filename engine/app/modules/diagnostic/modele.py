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
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parents[4]
DOSSIER = Path(os.environ.get("MODEL_PATH") or RACINE / "modeles" / "diagnostic")
SEUIL_INCERTAIN = float(os.environ.get("DIAGNOSTIC_CONFIDENCE_THRESHOLD") or 0.6)
TAILLE = 224
MOYENNE = np.array([0.485, 0.456, 0.406], dtype=np.float32)
ECART = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Libellés français et catégories, au format de data/label_mapping.csv (branche d'Oscar).
LIBELLES = {
    "healthy": ("sain", "Feuille saine"),
    "alternaria": ("maladie", "Alternariose"),
    "late_blight": ("maladie", "Mildiou"),
    "bacterial_spot": ("maladie", "Tache bactérienne"),
    "leaf_mold": ("maladie", "Cladosporiose"),
    "septoria_leaf_spot": ("maladie", "Septoriose"),
    "target_spot": ("maladie", "Corynesporiose"),
    "leaf_curl": ("maladie", "Enroulement jaune (virus TYLCV)"),
    "mosaic_virus": ("maladie", "Mosaïque (virus)"),
    "mites": ("ravageur", "Acariens"),
}
CULTURES_FR = {"tomato": "tomate", "potato": "pomme de terre", "pepper": "poivron"}


class ModeleAbsent(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _charger():
    import onnxruntime as ort  # import tardif : le moteur démarre même sans modèle

    fichier = DOSSIER / "terramind_diag_v0.onnx"
    if not fichier.exists():
        raise ModeleAbsent(f"modèle introuvable : {fichier}")
    session = ort.InferenceSession(str(fichier), providers=["CPUExecutionProvider"])
    etiquettes = json.loads((DOSSIER / "etiquettes.json").read_text())
    return session, etiquettes


def _preparer(contenu: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(contenu)).convert("RGB")
    l, h = image.size
    echelle = 256 / min(l, h)  # même traitement que la validation : 256 puis centre 224
    image = image.resize((max(TAILLE, round(l * echelle)), max(TAILLE, round(h * echelle))), Image.BILINEAR)
    l, h = image.size
    g, haut = (l - TAILLE) // 2, (h - TAILLE) // 2
    image = image.crop((g, haut, g + TAILLE, haut + TAILLE))
    x = (np.asarray(image, dtype=np.float32) / 255.0 - MOYENNE) / ECART
    return x.transpose(2, 0, 1)[None].astype(np.float32)


def diagnostiquer(contenu: bytes, culture: str | None = None) -> dict:
    session, etiquettes = _charger()
    logits = session.run(None, {session.get_inputs()[0].name: _preparer(contenu)})[0][0]
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
    return {"predictions": predictions, "seuil_incertain": SEUIL_INCERTAIN,
            "fiche": None, "questions_suivi": [],
            "certain": predictions[0]["confiance"] >= SEUIL_INCERTAIN}
