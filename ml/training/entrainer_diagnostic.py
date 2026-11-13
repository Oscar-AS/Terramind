"""Entraîne un premier modèle de diagnostic photo (référence de base, v0).

Données : PlantVillage (CC BY-SA 3.0) et PlantDoc (CC BY 4.0), déjà dans
data/raw/images/ (scripts/donnees/telecharger_images.py). Cultures couvertes :
tomate, pomme de terre, poivron. Pas d'oignon ni de chou dans ces jeux.

Étiquettes : vocabulaire de data/label_mapping.csv (branche ml/dataset-merge
d'Oscar) pour pouvoir fusionner avec TOM2024 + CCMT ensuite.

Évaluation honnête : PlantVillage est photographié en laboratoire (fond uni),
ce qui gonfle les scores. Le chiffre à retenir est celui du jeu de test
PlantDoc (photos prises au champ), jamais vu à l'entraînement.

Sortie (ignorée par Git) : modeles/diagnostic/terramind_diag_v0.pt (TorchScript)
et etiquettes.json ; métriques dans ml/eval/diagnostic_v0.json.

Usage : .venv/bin/python ml/training/entrainer_diagnostic.py [--epoques 6]
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

RACINE = Path(__file__).resolve().parents[2]
IMAGES = RACINE / "data" / "raw" / "images"
SORTIE = RACINE / "modeles" / "diagnostic"
EVAL = RACINE / "ml" / "eval" / "diagnostic_v0.json"

# (culture, etiquette) au format de data/label_mapping.csv.
PLANTVILLAGE = {
    "Pepper,_bell___Bacterial_spot": ("pepper", "bacterial_spot"),
    "Pepper,_bell___healthy": ("pepper", "healthy"),
    "Potato___Early_blight": ("potato", "alternaria"),
    "Potato___Late_blight": ("potato", "late_blight"),
    "Potato___healthy": ("potato", "healthy"),
    "Tomato___Bacterial_spot": ("tomato", "bacterial_spot"),
    "Tomato___Early_blight": ("tomato", "alternaria"),
    "Tomato___Late_blight": ("tomato", "late_blight"),
    "Tomato___Leaf_Mold": ("tomato", "leaf_mold"),
    "Tomato___Septoria_leaf_spot": ("tomato", "septoria_leaf_spot"),
    "Tomato___Spider_mites Two-spotted_spider_mite": ("tomato", "mites"),
    "Tomato___Target_Spot": ("tomato", "target_spot"),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": ("tomato", "leaf_curl"),
    "Tomato___Tomato_mosaic_virus": ("tomato", "mosaic_virus"),
    "Tomato___healthy": ("tomato", "healthy"),
}
PLANTDOC = {
    "Bell_pepper leaf": ("pepper", "healthy"),
    "Bell_pepper leaf spot": ("pepper", "bacterial_spot"),
    "Potato leaf early blight": ("potato", "alternaria"),
    "Potato leaf late blight": ("potato", "late_blight"),
    "Tomato Early blight leaf": ("tomato", "alternaria"),
    "Tomato Septoria leaf spot": ("tomato", "septoria_leaf_spot"),
    "Tomato leaf": ("tomato", "healthy"),
    "Tomato leaf bacterial spot": ("tomato", "bacterial_spot"),
    "Tomato leaf late blight": ("tomato", "late_blight"),
    "Tomato leaf mosaic virus": ("tomato", "mosaic_virus"),
    "Tomato leaf yellow virus": ("tomato", "leaf_curl"),
    "Tomato mold leaf": ("tomato", "leaf_mold"),
    "Tomato two spotted spider mites leaf": ("tomato", "mites"),
}
EXTENSIONS = {".jpg", ".jpeg", ".png"}
PLAFOND_PAR_CLASSE = 1500  # évite que la virose TYLCV (5 357 images) écrase le reste
TAILLE = 224


def lister(dossier: Path) -> list[Path]:
    return sorted(p for p in dossier.rglob("*") if p.suffix.lower() in EXTENSIONS)


def construire_listes(graine: int):
    alea = random.Random(graine)
    entrainement, validation, terrain = [], [], []
    for dossier, cle in PLANTVILLAGE.items():
        fichiers = lister(IMAGES / "plantvillage" / dossier)
        alea.shuffle(fichiers)
        fichiers = fichiers[:PLAFOND_PAR_CLASSE]
        n_val = max(1, len(fichiers) * 15 // 100)
        validation += [(f, cle) for f in fichiers[:n_val]]
        entrainement += [(f, cle) for f in fichiers[n_val:]]
    for dossier, cle in PLANTDOC.items():
        entrainement += [(f, cle) for f in lister(IMAGES / "plantdoc" / "train" / dossier)]
        terrain += [(f, cle) for f in lister(IMAGES / "plantdoc" / "test" / dossier)]
    return entrainement, validation, terrain


class Photos(Dataset):
    def __init__(self, elements, index, transformation):
        self.elements, self.index, self.transformation = elements, index, transformation

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, i):
        chemin, cle = self.elements[i]
        image = Image.open(chemin).convert("RGB")
        return self.transformation(image), self.index[cle]


def evaluer(modele, chargeur, appareil, n_classes):
    modele.eval()
    bons, total = 0, 0
    par_classe = defaultdict(lambda: [0, 0])
    with torch.no_grad():
        for x, y in chargeur:
            pred = modele(x.to(appareil)).argmax(1).cpu()
            for p, v in zip(pred.tolist(), y.tolist()):
                par_classe[v][1] += 1
                par_classe[v][0] += int(p == v)
            bons += int((pred == y).sum())
            total += len(y)
    return bons / max(total, 1), {k: v[0] / v[1] for k, v in par_classe.items()}


def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--epoques", type=int, default=6)
    arguments.add_argument("--graine", type=int, default=2026)
    args = arguments.parse_args()

    random.seed(args.graine)
    torch.manual_seed(args.graine)
    appareil = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    entrainement, validation, terrain = construire_listes(args.graine)
    cles = sorted({cle for _, cle in entrainement})
    index = {cle: i for i, cle in enumerate(cles)}
    print(f"{len(cles)} classes ; entraînement {len(entrainement)}, "
          f"validation {len(validation)}, terrain {len(terrain)} ; appareil {appareil}")

    normaliser = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    aug = transforms.Compose([
        transforms.RandomResizedCrop(TAILLE, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(0.3, 0.3, 0.3, 0.05),
        transforms.ToTensor(), normaliser,
    ])
    simple = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(TAILLE), transforms.ToTensor(), normaliser,
    ])
    charge = dict(batch_size=48, num_workers=4, persistent_workers=True)
    c_ent = DataLoader(Photos(entrainement, index, aug), shuffle=True, **charge)
    c_val = DataLoader(Photos(validation, index, simple), **charge)
    c_ter = DataLoader(Photos(terrain, index, simple), **charge)

    modele = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    modele.classifier[3] = nn.Linear(modele.classifier[3].in_features, len(cles))
    modele.to(appareil)

    # Poids de classe : les photos de terrain (PlantDoc) sont rares, on compense le déséquilibre.
    comptes = Counter(index[cle] for _, cle in entrainement)
    poids = torch.tensor([len(entrainement) / (len(cles) * comptes[i]) for i in range(len(cles))])
    perte = nn.CrossEntropyLoss(weight=poids.to(appareil), label_smoothing=0.1)
    optimiseur = torch.optim.AdamW(modele.parameters(), lr=1e-3, weight_decay=1e-4)
    planning = torch.optim.lr_scheduler.OneCycleLR(
        optimiseur, max_lr=1e-3, total_steps=args.epoques * len(c_ent))

    meilleur, historique = -1.0, []
    SORTIE.mkdir(parents=True, exist_ok=True)
    for epoque in range(1, args.epoques + 1):
        modele.train()
        debut = time.time()
        for x, y in c_ent:
            optimiseur.zero_grad()
            l = perte(modele(x.to(appareil)), y.to(appareil))
            l.backward()
            optimiseur.step()
            planning.step()
        acc_val, _ = evaluer(modele, c_val, appareil, len(cles))
        acc_ter, _ = evaluer(modele, c_ter, appareil, len(cles))
        historique.append({"epoque": epoque, "validation_labo": acc_val, "test_terrain": acc_ter})
        print(f"époque {epoque} : validation labo {acc_val:.3f}, test terrain {acc_ter:.3f} "
              f"({time.time() - debut:.0f} s)", flush=True)
        # Choix du modèle sur la validation labo : le test terrain reste un test, pas un critère.
        if acc_val > meilleur:
            meilleur = acc_val
            torch.save(modele.state_dict(), SORTIE / "meilleur.pth")

    modele.load_state_dict(torch.load(SORTIE / "meilleur.pth", map_location=appareil))
    acc_val, val_classes = evaluer(modele, c_val, appareil, len(cles))
    acc_ter, ter_classes = evaluer(modele, c_ter, appareil, len(cles))

    modele.to("cpu").eval()
    trace = torch.jit.trace(modele, torch.zeros(1, 3, TAILLE, TAILLE))
    trace.save(str(SORTIE / "terramind_diag_v0.pt"))
    etiquettes = [{"culture": c, "etiquette": e} for c, e in cles]
    (SORTIE / "etiquettes.json").write_text(json.dumps(etiquettes, indent=2))

    EVAL.parent.mkdir(parents=True, exist_ok=True)
    EVAL.write_text(json.dumps({
        "modele": "mobilenet_v3_large (ImageNet) affiné",
        "donnees": {"entrainement": len(entrainement), "validation_labo": len(validation),
                    "test_terrain_plantdoc": len(terrain)},
        "classes": [f"{c}/{e}" for c, e in cles],
        "precision_validation_labo": round(acc_val, 4),
        "precision_test_terrain": round(acc_ter, 4),
        "test_terrain_par_classe": {f"{cles[k][0]}/{cles[k][1]}": round(v, 3)
                                    for k, v in sorted(ter_classes.items())},
        "historique": historique,
        "graine": args.graine,
        "epoques": args.epoques,
    }, indent=2, ensure_ascii=False))
    print(f"FINI : validation labo {acc_val:.3f}, test terrain {acc_ter:.3f}")


if __name__ == "__main__":
    main()
