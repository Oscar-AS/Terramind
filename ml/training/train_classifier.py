"""Fine-tuning d'un modèle de vision pré-entraîné (PlantVillage HF ou MobileNetV3) sur terramind_v1.

Respecte la décision D5 (licence permissive Apache-2.0 / BSD, pas d'Ultralytics/YOLOv8 AGPL)
et la décision D13 (base fusionnée terramind_v1 : TOM2024 Burkina Faso + CCMT Ghana).

Deux backbones supportés (--backbone) :
1. `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification` (défaut, via Hugging Face
   `transformers`) : MobileNetV2 déjà pré-entraîné sur 38 classes de maladies foliaires
   (PlantVillage), adapté ensuite aux vraies photos de champ ouest-africaines de terramind_v1.
2. `mobilenet_v3_large` (via `torchvision.models`, pré-entraîné ImageNet-1K).

Stratégie d'entraînement en 2 phases :
- Phase 1 (tête seule, backbone gelé, 2 époques, lr=1e-3)
- Phase 2 (fine-tuning complet avec CosineAnnealingLR, 6 époques, lr=1e-4)
- Pondération inversement proportionnelle à la racine de l'effectif (`1 / sqrt(n_c)`) pour
  protéger les petites classes (ex. mildiou de la tomate à 58 images d'entraînement).
- Redimensionnement systématique en 224x224 px pour neutraliser le biais de résolution
  entre CCMT (400x400) et TOM2024 (tailles variables).

Sorties :
- Poids et métadonnées des classes : `modeles/diagnostic/terramind_v1_model.pt` et `classes.json`
- Rapport complet d'évaluation et calibration du seuil « incertain » : `ml/eval/metrics.json`

Usage (sur Google Colab / Kaggle GPU ou machine avec PyTorch) :
    python ml/training/train_classifier.py --epochs-head 2 --epochs-finetune 6 --leaf-only
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path("data_local/processed/terramind_v1")
SPLITS_CSV = DATA_DIR / "splits.csv"
SUMMARY_CSV = Path("data/splits_terramind_v1.csv")
MODEL_OUT_DIR = Path("modeles/diagnostic")
METRICS_OUT = Path("ml/eval/metrics.json")

HF_DEFAULT_MODEL = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
IMAGE_SIZE = 224
PETITES_CLASSES_SEUIL_IMAGES = 100


def charger_splits(leaf_only: bool = True, cultures: set[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Lit splits.csv et construit la table ordonnée des classes (crop, label)."""
    if not SPLITS_CSV.is_file():
        raise FileNotFoundError(
            f"{SPLITS_CSV} introuvable. Lancer d'abord : python ml/training/split_dataset.py"
        )

    libelles: dict[tuple[str, str], str] = {}
    totaux_classe: dict[tuple[str, str], int] = {}
    if SUMMARY_CSV.is_file():
        with SUMMARY_CSV.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                clef = (r["crop"], r["label"])
                libelles[clef] = r["libelle_fr"]
                totaux_classe[clef] = int(r["total"])

    lignes: list[dict] = []
    with SPLITS_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if leaf_only and row.get("est_feuille") == "non":
                continue
            if cultures and row["crop"] not in cultures:
                continue
            lignes.append(row)

    couples = sorted({(r["crop"], r["label"], r["categorie"]) for r in lignes})
    classes_info = []
    for idx, (crop, label, categorie) in enumerate(couples):
        total_img = totaux_classe.get((crop, label), 100)
        classes_info.append(
            {
                "index": idx,
                "cle": f"{crop}__{label}",
                "culture": crop,
                "etiquette": label,
                "categorie": categorie,
                "libelle": libelles.get((crop, label), label),
                "total_images": total_img,
                "petite_classe": total_img < PETITES_CLASSES_SEUIL_IMAGES,
            }
        )
    return lignes, classes_info


def calibrer_seuil_incertain(y_true: list[int], y_pred: list[int], confs: list[float]) -> dict:
    """Calcule la courbe Précision vs Couverture et choisit le seuil « incertain » optimal."""
    courbe = []
    seuil_retenu = 0.60
    for s_int in range(40, 95, 5):
        seuil = round(s_int / 100.0, 2)
        gardes = [(yt, yp) for yt, yp, c in zip(y_true, y_pred, confs, strict=False) if c >= seuil]
        couverture = len(gardes) / max(1, len(y_true))
        exactitude = (
            sum(1 for yt, yp in gardes if yt == yp) / len(gardes) if gardes else 0.0
        )
        courbe.append(
            {
                "seuil": seuil,
                "exactitude_retenus": round(exactitude, 4),
                "taux_couverture": round(couverture, 4),
                "taux_incertain": round(1.0 - couverture, 4),
            }
        )
        if exactitude >= 0.85 and couverture >= 0.70 and seuil_retenu == 0.60:
            seuil_retenu = seuil

    return {"seuil_recommande": seuil_retenu, "courbe_seuil": courbe}


def entrainer(args: argparse.Namespace) -> int:
    try:
        import torch
        import torch.nn as nn
        from PIL import Image
        from torch.utils.data import DataLoader, Dataset
        from torchvision import transforms
    except ImportError as exc:
        print(
            f"PyTorch / torchvision requis pour l'entraînement ({exc}).\n"
            "Sur Google Colab ou Kaggle, ils sont déjà installés par défaut."
        )
        return 1

    cultures_filtre = (
        {c.strip().lower() for c in args.crops.split(",") if c.strip()} if args.crops else None
    )
    lignes, classes_info = charger_splits(leaf_only=args.leaf_only, cultures=cultures_filtre)
    cle_vers_idx = {(c["culture"], c["etiquette"]): c["index"] for c in classes_info}
    nb_classes = len(classes_info)

    print(f"Classes retenues : {nb_classes} | Images totales : {len(lignes)}")

    tf_train = transforms.Compose(
        [
            transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    tf_eval = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    class TerraMindDataset(Dataset):
        def __init__(self, items: list[dict], transform):
            self.items = items
            self.transform = transform

        def __len__(self) -> int:
            return len(self.items)

        def __getitem__(self, idx: int):
            r = self.items[idx]
            img_path = DATA_DIR / r["file"]
            with Image.open(img_path) as im:
                tenseur = self.transform(im.convert("RGB"))
            cible = cle_vers_idx[(r["crop"], r["label"])]
            return tenseur, cible, r["source"], r["crop"]

    train_items = [r for r in lignes if r["split"] == "train"]
    val_items = [r for r in lignes if r["split"] == "val"]
    test_items = [r for r in lignes if r["split"] == "test"]

    ds_train = TerraMindDataset(train_items, tf_train)
    ds_val = TerraMindDataset(val_items, tf_eval)
    ds_test = TerraMindDataset(test_items, tf_eval)

    dl_train = DataLoader(ds_train, batch_size=args.batch_size, shuffle=True, num_workers=2)
    dl_val = DataLoader(ds_val, batch_size=args.batch_size, shuffle=False, num_workers=2)
    dl_test = DataLoader(ds_test, batch_size=args.batch_size, shuffle=False, num_workers=2)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Appareil d'entraînement : {device} | Backbone : {args.backbone}")

    util_hf = False
    if args.backbone != "mobilenet_v3_large":
        try:
            from transformers import AutoModelForImageClassification

            modele = AutoModelForImageClassification.from_pretrained(
                args.backbone,
                num_labels=nb_classes,
                ignore_mismatched_sizes=True,
            )
            util_hf = True
        except Exception as exc:
            print(f"Repli sur torchvision mobilenet_v3_large ({exc})")

    if not util_hf:
        from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

        modele = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_features = modele.classifier[-1].in_features
        modele.classifier[-1] = nn.Linear(in_features, nb_classes)

    modele.to(device)

    # Pondération par classe : 1 / sqrt(effectif_train)
    compte_train = Counter(cle_vers_idx[(r["crop"], r["label"])] for r in train_items)
    poids = torch.tensor(
        [1.0 / math.sqrt(max(1, compte_train[i])) for i in range(nb_classes)],
        dtype=torch.float32,
        device=device,
    )
    poids = poids / poids.mean()
    critere = nn.CrossEntropyLoss(weight=poids)

    def _logits(sortie):
        return sortie.logits if hasattr(sortie, "logits") else sortie

    def evaluer(chargeur):
        modele.eval()
        y_true, y_pred, confs, sources, crops = [], [], [], [], []
        with torch.no_grad():
            for x, y, src, crp in chargeur:
                x = x.to(device)
                probs = torch.softmax(_logits(modele(x)), dim=-1)
                conf, pred = probs.max(dim=-1)
                y_true.extend(y.tolist())
                y_pred.extend(pred.cpu().tolist())
                confs.extend(conf.cpu().tolist())
                sources.extend(src)
                crops.extend(crp)
        return y_true, y_pred, confs, sources, crops

    # Phase 1 : entraînement de la tête seule
    if args.epochs_head > 0:
        for nom, param in modele.named_parameters():
            param.requires_grad = "classifier" in nom
        opt_head = torch.optim.AdamW(
            [p for p in modele.parameters() if p.requires_grad], lr=1e-3, weight_decay=1e-4
        )
        for ep in range(1, args.epochs_head + 1):
            modele.train()
            perte_tot = 0.0
            for x, y, _, _ in dl_train:
                x, y = x.to(device), y.to(device)
                opt_head.zero_grad()
                perte = critere(_logits(modele(x)), y)
                perte.backward()
                opt_head.step()
                perte_tot += perte.item() * len(y)
            yt, yp, _, _, _ = evaluer(dl_val)
            acc_val = sum(1 for a, b in zip(yt, yp, strict=False) if a == b) / max(1, len(yt))
            print(f"[Phase 1 - Tête] Époque {ep}/{args.epochs_head} | val_acc={acc_val:.4f}")

    # Phase 2 : fine-tuning complet
    for param in modele.parameters():
        param.requires_grad = True
    opt_ft = torch.optim.AdamW(modele.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt_ft, T_max=max(1, args.epochs_finetune))

    meilleur_val = 0.0
    MODEL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    chemin_poids = MODEL_OUT_DIR / "terramind_v1_model.pt"

    for ep in range(1, args.epochs_finetune + 1):
        modele.train()
        for x, y, _, _ in dl_train:
            x, y = x.to(device), y.to(device)
            opt_ft.zero_grad()
            perte = critere(_logits(modele(x)), y)
            perte.backward()
            opt_ft.step()
        sched.step()
        yt, yp, _, _, _ = evaluer(dl_val)
        acc_val = sum(1 for a, b in zip(yt, yp, strict=False) if a == b) / max(1, len(yt))
        print(f"[Phase 2 - FineTune] Époque {ep}/{args.epochs_finetune} | val_acc={acc_val:.4f}")
        if acc_val >= meilleur_val:
            meilleur_val = acc_val
            torch.save(
                {
                    "backbone": args.backbone,
                    "util_hf": util_hf,
                    "nb_classes": nb_classes,
                    "classes": classes_info,
                    "state_dict": modele.state_dict(),
                },
                chemin_poids,
            )

    # Évaluation finale sur val (calibration seuil) et test (métriques publiées)
    yt_val, yp_val, conf_val, _, _ = evaluer(dl_val)
    calibration = calibrer_seuil_incertain(yt_val, yp_val, conf_val)
    seuil_opt = calibration["seuil_recommande"]

    yt_test, yp_test, conf_test, src_test, crp_test = evaluer(dl_test)
    acc_test_global = sum(1 for a, b in zip(yt_test, yp_test, strict=False) if a == b) / max(
        1, len(yt_test)
    )

    # Précision par source (TOM2024 vs CCMT) et par culture
    par_source = defaultdict(lambda: [0, 0])
    par_culture = defaultdict(lambda: [0, 0])
    par_classe = defaultdict(lambda: [0, 0])
    for yt, yp, src, crp in zip(yt_test, yp_test, src_test, crp_test, strict=False):
        ok = int(yt == yp)
        par_source[src][0] += ok
        par_source[src][1] += 1
        par_culture[crp][0] += ok
        par_culture[crp][1] += 1
        par_classe[yt][0] += ok
        par_classe[yt][1] += 1

    gardes_test = [
        (yt, yp) for yt, yp, c in zip(yt_test, yp_test, conf_test, strict=False) if c >= seuil_opt
    ]
    taux_incertain_test = 1.0 - (len(gardes_test) / max(1, len(yt_test)))
    acc_test_hors_incertain = (
        sum(1 for yt, yp in gardes_test if yt == yp) / len(gardes_test) if gardes_test else 0.0
    )

    rapport = {
        "date_evaluation": dt.date.today().isoformat(),
        "modele": args.backbone,
        "base": "terramind_v1 (TOM2024 + CCMT)",
        "nb_classes": nb_classes,
        "leaf_only": args.leaf_only,
        "effectifs": {
            "train": len(train_items),
            "val": len(val_items),
            "test": len(test_items),
        },
        "seuil_incertain": seuil_opt,
        "test_metrics": {
            "exactitude_globale": round(acc_test_global, 4),
            "exactitude_hors_incertain": round(acc_test_hors_incertain, 4),
            "taux_incertain": round(taux_incertain_test, 4),
            "par_source": {
                s: {"exactitude": round(ok / n, 4), "images": n}
                for s, (ok, n) in sorted(par_source.items())
            },
            "par_culture": {
                c: {"exactitude": round(ok / n, 4), "images": n}
                for c, (ok, n) in sorted(par_culture.items())
            },
            "par_classe": {
                classes_info[idx]["cle"]: {
                    "libelle": classes_info[idx]["libelle"],
                    "exactitude": round(ok / n, 4),
                    "images_test": n,
                }
                for idx, (ok, n) in sorted(par_classe.items())
            },
        },
        "calibration_val": calibration,
    }

    METRICS_OUT.parent.mkdir(parents=True, exist_ok=True)
    METRICS_OUT.write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")
    (MODEL_OUT_DIR / "classes.json").write_text(
        json.dumps(classes_info, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Poids enregistrés dans {chemin_poids}")
    print(f"Métriques enregistrées dans {METRICS_OUT}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fine-tuning du modèle de diagnostic TerraMind v1.")
    p.add_argument("--backbone", default=HF_DEFAULT_MODEL)
    p.add_argument("--epochs-head", type=int, default=2)
    p.add_argument("--epochs-finetune", type=int, default=6)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--leaf-only", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument(
        "--crops",
        default="",
        help="Liste optionnelle de cultures séparées par des virgules (ex. tomato,onion,maize)",
    )
    return p


if __name__ == "__main__":
    raise SystemExit(entrainer(build_parser().parse_args()))
