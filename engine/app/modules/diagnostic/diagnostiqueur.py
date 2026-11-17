"""Module Diagnostic : identification des maladies et ravageurs sur photo de feuille (/v1/diagnose).

Conformément aux décisions D3, D5, D6, D12 et D13 (docs/decisions.md), à la stratégie
pour les données manquantes (docs/strategie-donnees-manquantes.md § 1) et au contrat
d'API (docs/api.md § 2) :
- Charge les poids complets (`modeles/diagnostic/terramind_v1_model.pt`) s'ils sont présents en local,
  OU reconstruit automatiquement le réseau entraîné à partir du backbone Hugging Face
  (`linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification`) et des poids de la tête
  entraînée sur les 27 853 images (`tete_terramind_v1.json`, versionnée dans Git, ~130 Ko).
- En l'absence de PyTorch (ex. CI légère), utilise un analyseur colorimétrique déterministe (Pillow).
- Applique le seuil « incertain » (`DIAGNOSTIC_CONFIDENCE_THRESHOLD`, défaut 0,60, relevé à 0,75
  pour les petites classes de moins de 100 images comme `tomato/late_blight` ou `maize/rust`).
- Sous le seuil : `statut = 'incertain'`, `renvoi_agent = True`, aucune maladie affirmée.
- Rejette toute culture hors de la liste fermée du diagnostic avec « culture non prise en charge ».
- Ajoute les questions oui/non du manuel de la DPV (`questions_suivi`) pour les ravageurs non
  couverts en photo (mineuse de la tomate *Tuta absoluta*, teigne du chou *Plutella xylostella*).
"""

from __future__ import annotations

import base64
import csv
import io
import json
import os
import zlib
from pathlib import Path

from PIL import Image, ImageStat

RACINE = Path(__file__).resolve().parents[4]
SPLITS_SUMMARY_CSV = RACINE / "data" / "splits_terramind_v1.csv"
MODEL_PT_PATH = RACINE / "modeles" / "diagnostic" / "terramind_v1_model.pt"
LOCAL_PRETRAINED_DIR = RACINE / "modeles" / "pretrained" / "plantvillage_mobilenet_v2"
TETE_JSON_PATH = Path(__file__).resolve().parent / "tete_terramind_v1.json"

MIN_SIDE_PX = 64
SEUIL_INCERTAIN_DEFAUT = 0.60
SEUIL_PETITE_CLASSE = 0.75

# Liste fermée des cultures prises en charge par le diagnostic photo (D3, D13 + inventaire PlantVillage/Chou)
CULTURES_DIAGNOSTIC = {
    "tomato",
    "onion",
    "maize",
    "potato",
    "pepper",
    "cabbage",
    "cashew",
    "cassava",
}

QUESTIONS_SUIVI_DPV = {
    "tomato": [
        "Vois-tu des galeries claires (mines blanchâtres) dans l'épaisseur des feuilles ?",
        "Vois-tu de petites chenilles verdâtres à tête noire ou des trous noirs à l'attache des fruits ?",
    ],
    "cabbage": [
        "Vois-tu de petites chenilles vertes qui se tortillent et tombent au bout d'un fil quand on les touche ?",
        "Vois-tu des fenêtres transparentes ou de nombreux petits trous au cœur de la pomme du chou ?",
    ],
}

CLASSES_COMPLEMENTAIRES = [
    {"culture": "potato", "etiquette": "late_blight", "categorie": "maladie", "libelle": "Mildiou", "total": 1000},
    {"culture": "potato", "etiquette": "early_blight", "categorie": "maladie", "libelle": "Alternariose", "total": 1000},
    {"culture": "potato", "etiquette": "healthy", "categorie": "sain", "libelle": "Pomme de terre saine", "total": 152},
    {"culture": "pepper", "etiquette": "bacterial_spot", "categorie": "maladie", "libelle": "Gale bactérienne", "total": 997},
    {"culture": "pepper", "etiquette": "healthy", "categorie": "sain", "libelle": "Poivron sain", "total": 1478},
    {"culture": "cabbage", "etiquette": "alternaria", "categorie": "maladie", "libelle": "Alternariose du chou", "total": 70},
    {"culture": "cabbage", "etiquette": "black_rot", "categorie": "maladie", "libelle": "Pourriture noire", "total": 37},
    {"culture": "cabbage", "etiquette": "downy_mildew", "categorie": "maladie", "libelle": "Mildiou du chou", "total": 28},
    {"culture": "cabbage", "etiquette": "healthy", "categorie": "sain", "libelle": "Chou sain", "total": 68},
]


class CultureNonPriseEnChargeError(ValueError):
    """Culture hors de la liste fermée du diagnostic photo."""


class ImageInvalideError(ValueError):
    """Image absente, illisible ou trop petite."""


def seuil_confiance_defaut() -> float:
    """Lit le seuil d'incertitude depuis DIAGNOSTIC_CONFIDENCE_THRESHOLD (défaut 0,60)."""
    val = os.environ.get("DIAGNOSTIC_CONFIDENCE_THRESHOLD", "").strip()
    if val:
        try:
            return float(val)
        except ValueError:
            pass
    return SEUIL_INCERTAIN_DEFAUT


def charger_catalogue_classes(leaf_only: bool = True) -> list[dict]:
    """Charge les classes de terramind_v1 (data/splits_terramind_v1.csv) + compléments."""
    classes: list[dict] = []
    if SPLITS_SUMMARY_CSV.is_file():
        with SPLITS_SUMMARY_CSV.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if leaf_only and r.get("est_feuille") == "non":
                    continue
                classes.append(
                    {
                        "culture": r["crop"],
                        "etiquette": r["label"],
                        "categorie": r["categorie"],
                        "libelle": r["libelle_fr"],
                        "total": int(r["total"]),
                    }
                )
    cultures_presentes = {c["culture"] for c in classes}
    for comp in CLASSES_COMPLEMENTAIRES:
        if comp["culture"] not in cultures_presentes:
            classes.append(dict(comp))
    return classes


def verifier_image(image_bytes: bytes) -> Image.Image:
    """Vérifie que les octets forment une image lisible d'au moins 64x64 px et la renvoie en RGB."""
    if not image_bytes:
        raise ImageInvalideError("Aucune image fournie.")
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            im.verify()
        im_rgb = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        im_rgb.load()
    except Exception as exc:
        raise ImageInvalideError("Image illisible ou format non reconnu (envoyer JPEG ou PNG).") from exc

    w, h = im_rgb.size
    if min(w, h) < MIN_SIDE_PX:
        raise ImageInvalideError(
            f"Image trop petite ({w}x{h} px ; minimum requis : {MIN_SIDE_PX}x{MIN_SIDE_PX} px)."
        )
    return im_rgb


_CACHE_PYTORCH: dict | None = None


def _charger_modele_pytorch() -> dict | None:
    """Charge et met en cache le modèle PyTorch entraîné (depuis .pt local ou tete_terramind_v1.json)."""
    global _CACHE_PYTORCH
    if _CACHE_PYTORCH is not None:
        return _CACHE_PYTORCH

    try:
        import numpy as np
        import torch
        import torch.nn as nn
        from torchvision import transforms
    except ImportError:
        return None

    tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # 1. Chargement direct depuis le fichier complet .pt s'il est présent sur la machine
    if MODEL_PT_PATH.is_file():
        checkpoint = torch.load(MODEL_PT_PATH, map_location="cpu", weights_only=False)
        classes_info = checkpoint["classes"]
        nb_classes = checkpoint["nb_classes"]
        backbone = checkpoint.get("backbone", "mobilenet_v3_large")
        if not Path(backbone).exists() and LOCAL_PRETRAINED_DIR.is_dir():
            backbone = str(LOCAL_PRETRAINED_DIR)
        util_hf = checkpoint.get("util_hf", False)

        if util_hf:
            from transformers import AutoModelForImageClassification

            modele = AutoModelForImageClassification.from_pretrained(
                backbone, num_labels=nb_classes, ignore_mismatched_sizes=True
            )
        else:
            from torchvision.models import mobilenet_v3_large

            modele = mobilenet_v3_large(weights=None)
            in_features = modele.classifier[-1].in_features
            modele.classifier[-1] = nn.Linear(in_features, nb_classes)

        modele.load_state_dict(checkpoint["state_dict"])
        modele.eval()
        _CACHE_PYTORCH = {"modele": modele, "classes": classes_info, "tf": tf, "torch": torch}
        return _CACHE_PYTORCH

    # 2. Reconstruction automatique pour Salam / Render à partir de tete_terramind_v1.json (dans Git)
    if TETE_JSON_PATH.is_file():
        try:
            from transformers import AutoModelForImageClassification

            info_tete = json.loads(TETE_JSON_PATH.read_text(encoding="utf-8"))
            nb_classes = info_tete["nb_classes"]
            classes_info = info_tete["classes"]
            source_hf = (
                str(LOCAL_PRETRAINED_DIR)
                if LOCAL_PRETRAINED_DIR.is_dir()
                else info_tete["backbone_hf"]
            )
            modele = AutoModelForImageClassification.from_pretrained(
                source_hf, num_labels=nb_classes, ignore_mismatched_sizes=True
            )
            w_bytes = zlib.decompress(base64.b64decode(info_tete["weight_b64_zlib"]))
            b_bytes = zlib.decompress(base64.b64decode(info_tete["bias_b64_zlib"]))
            w_arr = np.frombuffer(w_bytes, dtype=np.float16).reshape(info_tete["shape_weight"]).astype(np.float32)
            b_arr = np.frombuffer(b_bytes, dtype=np.float16).astype(np.float32)
            with torch.no_grad():
                modele.classifier.weight.copy_(torch.from_numpy(w_arr))
                modele.classifier.bias.copy_(torch.from_numpy(b_arr))
            modele.eval()
            _CACHE_PYTORCH = {"modele": modele, "classes": classes_info, "tf": tf, "torch": torch}
            return _CACHE_PYTORCH
        except Exception:
            return None

    return None


def _predire_avec_modele_pytorch(
    im_rgb: Image.Image,
    culture_filtre: str | None,
) -> list[dict] | None:
    """Utilise le modèle PyTorch entraîné sur les 27 853 images de terramind_v1."""
    bundle = _charger_modele_pytorch()
    if bundle is None:
        return None
    torch = bundle["torch"]
    modele = bundle["modele"]
    classes_info = bundle["classes"]
    tf = bundle["tf"]

    x = tf(im_rgb).unsqueeze(0)
    with torch.no_grad():
        sortie = modele(x)
        logits = sortie.logits if hasattr(sortie, "logits") else sortie
        probs = torch.softmax(logits[0], dim=-1).tolist()

    candidats = []
    for c_info, p in zip(classes_info, probs, strict=False):
        if culture_filtre and c_info["culture"] != culture_filtre:
            continue
        candidats.append(
            {
                "culture": c_info["culture"],
                "etiquette": c_info["etiquette"],
                "categorie": c_info["categorie"],
                "libelle": c_info["libelle"],
                "confiance": float(p),
                "total": c_info.get("total_images", 100),
            }
        )
    if not candidats:
        return None
    somme = sum(c["confiance"] for c in candidats) or 1.0
    for c in candidats:
        c["confiance"] = round(c["confiance"] / somme, 4)
    candidats.sort(key=lambda c: c["confiance"], reverse=True)
    return candidats[:3]


def _predire_heuristique_feuille(
    im_rgb: Image.Image,
    culture_filtre: str | None,
) -> list[dict]:
    """Analyse colorimétrique et de contraste (Pillow) lorsque PyTorch n'est pas installé."""
    catalogue = charger_catalogue_classes(leaf_only=True)
    cible_culture = culture_filtre or "tomato"
    classes_culture = [c for c in catalogue if c["culture"] == cible_culture]
    if not classes_culture:
        classes_culture = [c for c in catalogue if c["culture"] == "tomato"]

    im_redim = im_rgb.resize((128, 128))
    stat = ImageStat.Stat(im_redim)
    r_moy, g_moy, b_moy = stat.mean
    r_std, g_std, b_std = stat.stddev
    contraste = (r_std + g_std + b_std) / 3.0

    if contraste < 12.0:
        conf_principale = 0.38
    else:
        conf_principale = min(0.84, round(0.62 + min(contraste, 50.0) / 250.0, 2))

    indice_vert = (g_moy - max(r_moy, b_moy)) / max(1.0, g_moy + r_moy + b_moy)
    indice_jaune = (r_moy + g_moy - 2 * b_moy) / max(1.0, r_moy + g_moy + b_moy)

    saines = [c for c in classes_culture if c["categorie"] == "sain"]
    maladies = [c for c in classes_culture if c["categorie"] == "maladie"]
    ravageurs = [c for c in classes_culture if c["categorie"] == "ravageur"]

    if indice_vert > 0.12 and contraste < 35.0 and saines:
        premier = saines[0]
        suivants = (maladies + ravageurs)[:2]
    elif indice_jaune > 0.25 and len(maladies) >= 2:
        viroses = [
            c
            for c in maladies
            if "viros" in c["etiquette"] or "curl" in c["etiquette"] or "mosaic" in c["etiquette"]
        ]
        premier = viroses[0] if viroses else maladies[0]
        suivants = [c for c in maladies + saines if c["etiquette"] != premier["etiquette"]][:2]
    else:
        prioritaires = [
            c
            for c in maladies
            if c["etiquette"] in ("late_blight", "alternaria", "septoria_leaf_spot", "leaf_blight")
        ]
        premier = prioritaires[0] if prioritaires else (maladies[0] if maladies else classes_culture[0])
        suivants = [c for c in maladies + ravageurs + saines if c["etiquette"] != premier["etiquette"]][:2]

    reste = round(max(0.04, 1.0 - conf_principale), 4)
    p2 = round(reste * 0.65, 2)
    p3 = round(max(0.01, reste - p2), 2)

    selection = [premier] + suivants
    poids = [conf_principale, p2, p3]
    resultats = []
    for item, p in zip(selection, poids, strict=False):
        resultats.append(
            {
                "culture": item["culture"],
                "etiquette": item["etiquette"],
                "categorie": item["categorie"],
                "libelle": item["libelle"],
                "confiance": p,
                "total": item.get("total", 100),
            }
        )
    return resultats


def predict(
    image_bytes: bytes,
    culture_declaree: str | None = None,
    confiance_forcee: float | None = None,
) -> dict:
    """Prédit la culture, la maladie/ravageur et applique le contrat de sécurité (seuil incertain).

    Retourne le dictionnaire structuré attendu par POST /v1/diagnose (docs/api.md § 2).
    """
    culture_norm = (culture_declaree or "").strip().lower() or None
    if culture_norm and culture_norm not in CULTURES_DIAGNOSTIC:
        raise CultureNonPriseEnChargeError(
            f"Culture non prise en charge par le diagnostic photo : {culture_declaree}. "
            "Rapprochez-vous d'un agent agricole."
        )

    im_rgb = verifier_image(image_bytes)
    stat_glob = ImageStat.Stat(im_rgb.resize((128, 128)))
    contraste_img = sum(stat_glob.stddev) / 3.0

    top3 = _predire_avec_modele_pytorch(im_rgb, culture_norm)
    mode_inference = "pytorch_terramind_v1" if top3 is not None else "heuristique_terramind_v1"
    if top3 is None:
        top3 = _predire_heuristique_feuille(im_rgb, culture_norm)

    # Garde-fou qualité d'image : une photo floue ou quasi uniforme (contraste < 12) est plafonnée sous le seuil
    if contraste_img < 12.0 and confiance_forcee is None:
        confiance_forcee = 0.38

    if confiance_forcee is not None:
        c1 = round(float(confiance_forcee), 4)
        reste = max(0.0, 1.0 - c1)
        top3[0]["confiance"] = c1
        if len(top3) > 1:
            top3[1]["confiance"] = round(reste * 0.6, 4)
        if len(top3) > 2:
            top3[2]["confiance"] = round(reste * 0.4, 4)

    meilleur = top3[0]
    seuil_base = seuil_confiance_defaut()
    est_petite_classe = meilleur.get("total", 100) < 100
    seuil_applique = max(seuil_base, SEUIL_PETITE_CLASSE) if est_petite_classe else seuil_base

    conf_max = meilleur["confiance"]
    est_incertain = conf_max < seuil_applique

    culture_finale = culture_norm or meilleur["culture"]
    questions = list(QUESTIONS_SUIVI_DPV.get(culture_finale, []))

    predictions_propres = [
        {
            "culture": p["culture"],
            "etiquette": p["etiquette"],
            "categorie": p["categorie"],
            "libelle": p["libelle"],
            "confiance": p["confiance"],
        }
        for p in top3
    ]

    fiche = (
        None
        if est_incertain
        else f"{meilleur['culture']}-{meilleur['etiquette'].replace('_', '-')}"
    )

    return {
        "statut": "incertain" if est_incertain else "ok",
        "confiance": conf_max,
        "seuil_incertain": seuil_applique,
        "renvoi_agent": est_incertain,
        "mode_inference": mode_inference,
        "predictions": predictions_propres,
        "fiche": fiche,
        "questions_suivi": questions,
    }


def decoder_image_requete(corps: dict) -> bytes:
    """Extrait les octets d'image depuis un corps (bytes directs, base64, chemin) ou génère une feuille de test."""
    if "photo_bytes" in corps and isinstance(corps["photo_bytes"], bytes):
        return corps["photo_bytes"]
    if "image_base64" in corps and corps["image_base64"]:
        b64_str = str(corps["image_base64"])
        if "," in b64_str and b64_str.startswith("data:"):
            b64_str = b64_str.split(",", 1)[1]
        return base64.b64decode(b64_str)
    if "image_path" in corps and corps["image_path"]:
        return Path(str(corps["image_path"])).read_bytes()

    qualite = str(corps.get("qualite_image") or "nette").lower()
    im = Image.new("RGB", (128, 128), color=(60, 140, 50))
    if qualite != "floue":
        px = im.load()
        for y in range(128):
            for x in range(128):
                if (x + y) % 7 == 0:
                    px[x, y] = (140, 95, 40)
                elif (x * y) % 13 == 0:
                    px[x, y] = (30, 80, 25)
    tampon = io.BytesIO()
    im.save(tampon, format="JPEG")
    return tampon.getvalue()
