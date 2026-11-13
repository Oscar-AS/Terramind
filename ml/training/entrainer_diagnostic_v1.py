"""Modèle de diagnostic v1 : photos de terrain africaines, calibration, choix sur données de terrain.

Différences avec la v0 (ml/eval/diagnostic_v0.md) :
- ajoute TOM2024 (Burkina Faso, photos de terrain, CC BY 4.0) pour la tomate et l'oignon, avec
  les étiquettes de data/label_mapping.csv (branche ml/dataset-merge d'Oscar) ; classes de moins de
  50 images retirées, comme dans la décision D8 d'Oscar ;
- réduit le poids de PlantVillage (photos de laboratoire) : 600 images par classe au plus ;
- augmentations plus fortes (recadrage serré, flou, effacement aléatoire) contre le biais du fond uni ;
- validation « terrain » distincte du test : 20 % de PlantDoc entraînement + 15 % de TOM2024.
  Elle sert à choisir l'époque, la température de calibration et le seuil ; le test n'y sert jamais ;
- calibration par température (Guo et al. 2017) ;
- deux tests de terrain : PlantDoc test (102 photos, comparable à la v0) et 15 % de TOM2024.

Usage : .venv/bin/python ml/training/entrainer_diagnostic_v1.py --arch mobilenet_v3_large
        .venv/bin/python ml/training/entrainer_diagnostic_v1.py --arch convnext_tiny
Sorties (hors Git) : modeles/diagnostic_v1_<arch>/ ; métriques : ml/eval/diagnostic_v1_<arch>.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
from PIL import Image, ImageFilter
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrainer_diagnostic import IMAGES, PLANTDOC, PLANTVILLAGE, RACINE, lister  # noqa: E402

TOM = IMAGES / "tom2024" / "raw-train.parquet"
CULTURES_TOM = {"Tomato", "Onion"}
MIN_IMAGES = 50
PLAFOND_PV = 600
TAILLE = 224
ARCHS = {
    "mobilenet_v3_large": (models.mobilenet_v3_large, models.MobileNet_V3_Large_Weights.IMAGENET1K_V2),
    "convnext_tiny": (models.convnext_tiny, models.ConvNeXt_Tiny_Weights.IMAGENET1K_V1),
}


def part(cle: str, graine: int) -> float:
    """Nombre stable dans [0, 1) tiré du nom : découpage reproductible, indépendant de l'ordre."""
    return int(hashlib.sha256(f"{graine}:{cle}".encode()).hexdigest()[:8], 16) / 2**32


def construire(graine: int):
    alea = random.Random(graine)
    ent, val, test_pd, test_tom = [], [], [], []
    # Images sous forme (source, chargeur, (culture, étiquette)). Chargeur : chemin ou octets.
    for dossier, cle in PLANTVILLAGE.items():
        fichiers = lister(IMAGES / "plantvillage" / dossier)
        alea.shuffle(fichiers)
        ent += [("pv", f, cle) for f in fichiers[:PLAFOND_PV]]
    for dossier, cle in PLANTDOC.items():
        for f in lister(IMAGES / "plantdoc" / "train" / dossier):
            (val if part(str(f.name) + dossier, graine) < 0.2 else ent).append(("pd", f, cle))
        test_pd += [("pd", f, cle) for f in lister(IMAGES / "plantdoc" / "test" / dossier)]

    # data/label_mapping.csv d'Oscar (branche ml/dataset-merge, pas encore fusionnée).
    texte = subprocess.run(["git", "show", "origin/ml/dataset-merge:data/label_mapping.csv"], cwd=RACINE,
                           capture_output=True, text=True, check=True).stdout
    correspondance = {(r["crop_src"], r["label_src"]): (r["crop"], r["label"])
                      for r in csv.DictReader(io.StringIO(texte)) if r["source"] == "tom2024"}
    table = pq.read_table(TOM)
    noms = json.loads(table.schema.metadata[b"huggingface"])["info"]["features"]["label"]["names"]
    lignes = [(r["crop_type"], noms[r["label"]], r["image"]["bytes"])
              for r in table.to_pylist() if r["crop_type"] in CULTURES_TOM]
    comptes = Counter(correspondance[(c, l)] for c, l, _ in lignes)
    vus = set()
    for c, l, octets in lignes:
        cle = correspondance[(c, l)]
        empreinte = hashlib.sha256(octets).hexdigest()
        if comptes[cle] < MIN_IMAGES or empreinte in vus:  # classes trop petites, doublons exacts
            continue
        vus.add(empreinte)
        u = part(empreinte, graine)
        (test_tom if u < 0.15 else val if u < 0.30 else ent).append(("tom", octets, cle))
    return ent, val, test_pd, test_tom


class Photos(Dataset):
    def __init__(self, elements, index, transformation):
        self.elements, self.index, self.transformation = elements, index, transformation

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, i):
        _, charge, cle = self.elements[i]
        image = Image.open(io.BytesIO(charge) if isinstance(charge, bytes) else charge).convert("RGB")
        return self.transformation(image), self.index[cle]


class FlouAleatoire:
    def __call__(self, image):
        return image.filter(ImageFilter.GaussianBlur(random.uniform(0.1, 1.5))) if random.random() < 0.3 else image


def logits_de(modele, chargeur, appareil):
    modele.eval()
    sorties, cibles = [], []
    with torch.no_grad():
        for x, y in chargeur:
            sorties.append(modele(x.to(appareil)).float().cpu())
            cibles.append(y)
    return torch.cat(sorties), torch.cat(cibles)


def temperature(logits, cibles):
    t = torch.ones(1, requires_grad=True)
    opt = torch.optim.LBFGS([t], lr=0.05, max_iter=200)

    def pas():
        opt.zero_grad()
        perte = nn.functional.cross_entropy(logits / t.clamp(min=0.05), cibles)
        perte.backward()
        return perte

    opt.step(pas)
    return float(t.clamp(min=0.05))


def mesures(logits, cibles, t, seuils=(0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    p = torch.softmax(logits / t, 1)
    conf, pred = p.max(1)
    juste = pred == cibles
    tableau = {str(s): {"couverture": round(float((conf >= s).float().mean()), 3),
                        "precision": round(float(juste[conf >= s].float().mean()), 3) if (conf >= s).any() else None}
               for s in seuils}
    return round(float(juste.float().mean()), 4), tableau


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--arch", choices=ARCHS, default="mobilenet_v3_large")
    a.add_argument("--epoques", type=int, default=10)
    a.add_argument("--graine", type=int, default=2026)
    args = a.parse_args()
    random.seed(args.graine)
    torch.manual_seed(args.graine)
    appareil = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    sortie = RACINE / "modeles" / f"diagnostic_v1_{args.arch}"
    sortie.mkdir(parents=True, exist_ok=True)

    ent, val, test_pd, test_tom = construire(args.graine)
    cles = sorted({cle for *_, cle in ent})
    index = {cle: i for i, cle in enumerate(cles)}
    print(f"{args.arch} : {len(cles)} classes ; entraînement {len(ent)}, validation terrain {len(val)}, "
          f"test PlantDoc {len(test_pd)}, test TOM2024 {len(test_tom)}", flush=True)

    norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    aug = transforms.Compose([
        transforms.RandomResizedCrop(TAILLE, scale=(0.35, 1.0)), transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(), transforms.RandomRotation(30), FlouAleatoire(),
        transforms.ColorJitter(0.4, 0.4, 0.4, 0.06), transforms.ToTensor(), norm,
        transforms.RandomErasing(p=0.25),
    ])
    simple = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(TAILLE), transforms.ToTensor(), norm])
    charge = dict(batch_size=48, num_workers=4, persistent_workers=True)
    # Échantillonnage équilibré : chaque classe pèse pareil, quelle que soit sa source.
    comptes = Counter(index[c] for *_, c in ent)
    poids = [1.0 / comptes[index[c]] for *_, c in ent]
    echant = torch.utils.data.WeightedRandomSampler(poids, num_samples=len(ent), replacement=True)
    c_ent = DataLoader(Photos(ent, index, aug), sampler=echant, **charge)
    c_val = DataLoader(Photos(val, index, simple), **charge)
    c_pd = DataLoader(Photos([e for e in test_pd if e[2] in index], index, simple), **charge)
    c_tom = DataLoader(Photos(test_tom, index, simple), **charge)

    fabrique, poids_init = ARCHS[args.arch]
    modele = fabrique(weights=poids_init)
    if args.arch.startswith("mobilenet"):
        modele.classifier[3] = nn.Linear(modele.classifier[3].in_features, len(cles))
    else:
        modele.classifier[2] = nn.Linear(modele.classifier[2].in_features, len(cles))
    modele.to(appareil)
    perte = nn.CrossEntropyLoss(label_smoothing=0.1)
    lr = 1e-3 if args.arch.startswith("mobilenet") else 3e-4
    opt = torch.optim.AdamW(modele.parameters(), lr=lr, weight_decay=0.05)
    plan = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=args.epoques * len(c_ent))

    meilleur, historique = -1.0, []
    for ep in range(1, args.epoques + 1):
        modele.train()
        debut = time.time()
        for x, y in c_ent:
            opt.zero_grad()
            perte(modele(x.to(appareil)), y.to(appareil)).backward()
            opt.step()
            plan.step()
        lv, yv = logits_de(modele, c_val, appareil)
        acc_val = float((lv.argmax(1) == yv).float().mean())
        historique.append({"epoque": ep, "validation_terrain": round(acc_val, 4)})
        print(f"époque {ep} : validation terrain {acc_val:.3f} ({time.time() - debut:.0f} s)", flush=True)
        if acc_val > meilleur:  # choix sur la validation terrain, jamais sur les tests
            meilleur = acc_val
            torch.save(modele.state_dict(), sortie / "meilleur.pth")

    modele.load_state_dict(torch.load(sortie / "meilleur.pth", map_location=appareil))
    lv, yv = logits_de(modele, c_val, appareil)
    t = temperature(lv, yv)
    _, tab_val = mesures(lv, yv, t)
    # Seuil : le plus bas qui donne au moins 85 % de réponses justes sur la validation terrain.
    seuil = next((float(s) for s, m in tab_val.items() if m["precision"] and m["precision"] >= 0.85), 0.9)
    resultats = {}
    for nom, chargeur in (("test_plantdoc", c_pd), ("test_tom2024", c_tom)):
        lt, yt = logits_de(modele, chargeur, appareil)
        acc, tab = mesures(lt, yt, t)
        par_classe = {}
        for i in yt.unique().tolist():
            m = yt == i
            par_classe[f"{cles[i][0]}/{cles[i][1]}"] = round(float((lt[m].argmax(1) == i).float().mean()), 3)
        resultats[nom] = {"images": len(yt), "precision": acc, "seuils": tab, "par_classe": par_classe}
        print(f"{nom} : précision {acc:.3f} ; au seuil {seuil} : {tab[str(seuil)]}", flush=True)

    modele.to("cpu").eval()
    torch.onnx.export(modele, torch.zeros(1, 3, TAILLE, TAILLE), str(sortie / "terramind_diag.onnx"),
                      input_names=["image"], output_names=["logits"], opset_version=17, dynamo=False)
    (sortie / "etiquettes.json").write_text(json.dumps([{"culture": c, "etiquette": e} for c, e in cles], indent=2))
    (sortie / "calibration.json").write_text(json.dumps({"temperature": t, "seuil_incertain": seuil}))
    (RACINE / "ml" / "eval" / f"diagnostic_v1_{args.arch}.json").write_text(json.dumps({
        "architecture": args.arch, "classes": [f"{c}/{e}" for c, e in cles],
        "donnees": {"entrainement": len(ent), "validation_terrain": len(val)},
        "validation_terrain": {"precision": round(meilleur, 4), "seuils": tab_val},
        "temperature": round(t, 3), "seuil_incertain": seuil, **resultats,
        "historique": historique, "graine": args.graine, "epoques": args.epoques,
    }, indent=2, ensure_ascii=False))
    print(f"FINI {args.arch} : température {t:.2f}, seuil {seuil}", flush=True)


if __name__ == "__main__":
    main()
