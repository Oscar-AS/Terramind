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
SEUIL_INCERTAIN = 0.6  # repli si ni variable d'environnement ni calibration
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


@lru_cache(maxsize=1)
def _charger():
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
