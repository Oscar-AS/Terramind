"""Fine-tuning d'un modèle de vision pré-entraîné (PlantVillage HF ou MobileNetV3) sur terramind_v1.

Fonctionne directement sur ton PC (CPU 8 cœurs en ~2-3 minutes grâce à l'extraction
vectorielle 1280-D en une passe + entraînement de la tête sur 50 époques) OU sur GPU CUDA.

Respecte la décision D5 (licence permissive Apache-2.0 / BSD, pas d'Ultralytics/YOLOv8 AGPL)
et la décision D13 (base fusionnée terramind_v1 : TOM2024 Burkina Faso + CCMT Ghana).

Backbone par défaut :
- `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification` (Hugging Face `transformers`) :
  MobileNetV2 déjà pré-entraîné sur 38 classes de maladies foliaires (PlantVillage), adapté
  ensuite aux vraies photos de champ ouest-africaines de terramind_v1.

Sorties générées directement dans ton dossier local :
- `modeles/diagnostic/terramind_v1_model.pt` et `modeles/diagnostic/classes.json`
- `ml/eval/metrics.json` (exactitude globale, hors incertain, par source, par culture, par classe)

Usage sur ton PC :
    .venv\\Scripts\\python.exe -X utf8 ml/training/train_classifier.py
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path("data_local/processed/terramind_v1")
SPLITS_CSV = DATA_DIR / "splits.csv"
SUMMARY_CSV = Path("data/splits_terramind_v1.csv")
MODEL_OUT_DIR = Path("modeles/diagnostic")
METRICS_OUT = Path("ml/eval/metrics.json")

LOCAL_PRETRAINED_DIR = Path("modeles/pretrained/plantvillage_mobilenet_v2")
HF_DEFAULT_MODEL = (
    str(LOCAL_PRETRAINED_DIR)
    if LOCAL_PRETRAINED_DIR.is_dir()
    else "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
)
IMAGE_SIZE = 224
PETITES_CLASSES_SEUIL_IMAGES = 100


def charger_splits(
    leaf_only: bool = True, cultures: set[str] | None = None
) -> tuple[list[dict], list[dict]]:
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


def sous_echantillonner_par_classe(
    items: list[dict], max_par_classe: int, seed: int = 42
) -> list[dict]:
    """Garde au plus `max_par_classe` images par (crop, label) de façon équilibrée entre sources."""
    if max_par_classe <= 0:
        return items
    par_classe: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in items:
        par_classe[(r["crop"], r["label"])].append(r)

    retenus: list[dict] = []
    for clef in sorted(par_classe):
        groupe = sorted(par_classe[clef], key=lambda x: x["sha256"])
        rng = random.Random(f"{seed}:{clef[0]}:{clef[1]}")
        rng.shuffle(groupe)
        retenus.extend(groupe[:max_par_classe])
    return retenus


def calibrer_seuil_incertain(y_true: list[int], y_pred: list[int], confs: list[float]) -> dict:
    """Calcule la courbe Précision vs Couverture et choisit le seuil « incertain » optimal."""
    courbe = []
    seuil_retenu = 0.60
    for s_int in range(40, 95, 5):
        seuil = round(s_int / 100.0, 2)
        gardes = [
            (yt, yp) for yt, yp, c in zip(y_true, y_pred, confs, strict=False) if c >= seuil
        ]
        couverture = len(gardes) / max(1, len(y_true))
        exactitude = sum(1 for yt, yp in gardes if yt == yp) / len(gardes) if gardes else 0.0
        courbe.append(
            {
                "seuil": seuil,
                "exactitude_retenus": round(exactitude, 4),
                "taux_couverture": round(couverture, 4),
                "taux_incertain": round(1.0 - couverture, 4),
            }
        )
        if exactitude >= 0.80 and couverture >= 0.65 and seuil_retenu == 0.60:
            seuil_retenu = seuil

    return {"seuil_recommande": seuil_retenu, "courbe_seuil": courbe}


def entrainer(args: argparse.Namespace) -> int:
    try:
        import torch
        import torch.nn as nn
        from PIL import Image
        from torch.utils.data import DataLoader, Dataset, TensorDataset
        from torchvision import transforms
    except ImportError as exc:
        print(
            f"PyTorch / torchvision requis pour l'entraînement ({exc}).\n"
            "Installer avec : .venv\\Scripts\\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
        )
        return 1

    nb_threads = max(4, os.cpu_count() or 4)
    torch.set_num_threads(nb_threads)

    cultures_filtre = (
        {c.strip().lower() for c in args.crops.split(",") if c.strip()} if args.crops else None
    )
    lignes, classes_info = charger_splits(leaf_only=args.leaf_only, cultures=cultures_filtre)
    cle_vers_idx = {(c["culture"], c["etiquette"]): c["index"] for c in classes_info}
    nb_classes = len(classes_info)

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    mode_rapide_cpu = (not use_cuda) and args.fast_cpu

    train_items = [r for r in lignes if r["split"] == "train"]
    val_items = [r for r in lignes if r["split"] == "val"]
    test_items = [r for r in lignes if r["split"] == "test"]

    if mode_rapide_cpu:
        train_items = sous_echantillonner_par_classe(train_items, args.max_train_per_class)
        val_items = sous_echantillonner_par_classe(val_items, args.max_eval_per_class)
        test_items = sous_echantillonner_par_classe(test_items, args.max_eval_per_class)

    print(
        f"Appareil : {device} ({nb_threads} threads) | Classes : {nb_classes} | "
        f"train={len(train_items)}, val={len(val_items)}, test={len(test_items)}",
        flush=True,
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

    dl_train = DataLoader(
        TerraMindDataset(train_items, tf_eval), batch_size=args.batch_size, shuffle=False
    )
    dl_val = DataLoader(TerraMindDataset(val_items, tf_eval), batch_size=args.batch_size, shuffle=False)
    dl_test = DataLoader(TerraMindDataset(test_items, tf_eval), batch_size=args.batch_size, shuffle=False)

    print(f"Chargement du modèle pré-entraîné : {args.backbone} ...", flush=True)
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
            print(f"Repli sur torchvision mobilenet_v3_large ({exc})", flush=True)

    if not util_hf:
        from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

        modele = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        in_features = modele.classifier[-1].in_features
        modele.classifier[-1] = nn.Linear(in_features, nb_classes)

    modele.to(device)

    compte_train = Counter(cle_vers_idx[(r["crop"], r["label"])] for r in train_items)
    poids = torch.tensor(
        [1.0 / math.sqrt(max(1, compte_train[i])) for i in range(nb_classes)],
        dtype=torch.float32,
        device=device,
    )
    poids = poids / poids.mean()
    critere = nn.CrossEntropyLoss(weight=poids)

    def extraire_embeddings(chargeur, nom_split: str):
        """Passe unique dans le backbone gelé pour extraire les vecteurs 1280-D (ultra-rapide sur CPU)."""
        modele.eval()
        feats_list, y_list, src_list, crp_list = [], [], [], []
        t0 = time.time()
        nb_lots = len(chargeur)
        with torch.inference_mode():
            for i, (x, y, src, crp) in enumerate(chargeur, start=1):
                x = x.to(device)
                if util_hf and hasattr(modele, "mobilenet_v2"):
                    out = modele.mobilenet_v2(x)
                    vec = out.pooler_output
                else:
                    vec = modele.avgpool(modele.features(x)).flatten(1)
                feats_list.append(vec.cpu())
                y_list.extend(y.tolist())
                src_list.extend(src)
                crp_list.extend(crp)
                if i % 10 == 0 or i == nb_lots:
                    print(
                        f"  [Extraction {nom_split}] lot {i}/{nb_lots} ({time.time() - t0:.0f}s)",
                        flush=True,
                    )
        return torch.cat(feats_list, dim=0), torch.tensor(y_list, dtype=torch.long), src_list, crp_list

    print("Extraction des représentations visuelles (1 passe unique par image)...", flush=True)
    cache_emb_path = DATA_DIR / f"embeddings_cache_{len(train_items)}_{len(val_items)}_{len(test_items)}.pt"
    if cache_emb_path.is_file():
        print(f"Chargement des représentations depuis le cache : {cache_emb_path}", flush=True)
        cache_data = torch.load(cache_emb_path, map_location="cpu", weights_only=False)
        x_tr_emb, y_tr_emb = cache_data["x_tr"], cache_data["y_tr"]
        x_va_emb, y_va_emb = cache_data["x_va"], cache_data["y_va"]
        x_te_emb, y_te_emb = cache_data["x_te"], cache_data["y_te"]
        src_test, crp_test = cache_data["src_test"], cache_data["crp_test"]
    else:
        x_tr_emb, y_tr_emb, _, _ = extraire_embeddings(dl_train, "train")
        x_va_emb, y_va_emb, _, _ = extraire_embeddings(dl_val, "val")
        x_te_emb, y_te_emb, src_test, crp_test = extraire_embeddings(dl_test, "test")
        torch.save(
            {
                "x_tr": x_tr_emb,
                "y_tr": y_tr_emb,
                "x_va": x_va_emb,
                "y_va": y_va_emb,
                "x_te": x_te_emb,
                "y_te": y_te_emb,
                "src_test": src_test,
                "crp_test": crp_test,
            },
            cache_emb_path,
        )
        print(f"Représentations mises en cache dans : {cache_emb_path}", flush=True)

    tete = modele.classifier if util_hf else modele.classifier
    for p in tete.parameters():
        p.requires_grad = True

    opt = torch.optim.AdamW(tete.parameters(), lr=3e-3, weight_decay=1e-3)
    nb_epoques_tete = 50
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=nb_epoques_tete)
    dl_emb = DataLoader(TensorDataset(x_tr_emb, y_tr_emb), batch_size=128, shuffle=True)

    MODEL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    chemin_poids = MODEL_OUT_DIR / "terramind_v1_model.pt"
    meilleur_val = 0.0
    meilleur_etat = None

    print(f"Entraînement du classifieur ({nb_epoques_tete} époques sur vecteurs extraits)...", flush=True)
    for ep in range(1, nb_epoques_tete + 1):
        tete.train()
        for bx, by in dl_emb:
            bx, by = bx.to(device), by.to(device)
            opt.zero_grad()
            perte = critere(tete(bx), by)
            perte.backward()
            opt.step()
        sched.step()

        if ep % 10 == 0 or ep == nb_epoques_tete:
            tete.eval()
            with torch.inference_mode():
                logits_va = tete(x_va_emb.to(device))
                preds_va = logits_va.argmax(dim=-1).cpu()
                acc_va = (preds_va == y_va_emb).float().mean().item()
            print(f"  [Époque {ep}/{nb_epoques_tete}] val_acc={acc_va:.4f}", flush=True)
            if acc_va >= meilleur_val:
                meilleur_val = acc_va
                meilleur_etat = {k: v.cpu().clone() for k, v in modele.state_dict().items()}

    if meilleur_etat is not None:
        modele.load_state_dict(meilleur_etat)

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

    # Évaluation finale sur val et test
    tete.eval()
    with torch.inference_mode():
        probs_val = torch.softmax(tete(x_va_emb.to(device)), dim=-1).cpu()
        conf_val, yp_val_t = probs_val.max(dim=-1)
        yt_val = y_va_emb.tolist()
        yp_val = yp_val_t.tolist()

        probs_test = torch.softmax(tete(x_te_emb.to(device)), dim=-1).cpu()
        conf_test_t, yp_test_t = probs_test.max(dim=-1)
        yt_test = y_te_emb.tolist()
        yp_test = yp_test_t.tolist()
        conf_test = conf_test_t.tolist()

    calibration = calibrer_seuil_incertain(yt_val, yp_val, conf_val.tolist())
    seuil_opt = calibration["seuil_recommande"]

    acc_test_global = sum(1 for a, b in zip(yt_test, yp_test, strict=False) if a == b) / max(
        1, len(yt_test)
    )

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
        "effectifs_evalues": {
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
    print(f"\nTerminé ! Poids enregistrés dans : {chemin_poids}", flush=True)
    print(f"Métriques enregistrées dans : {METRICS_OUT}", flush=True)
    print(
        f"Exactitude test : {acc_test_global:.2%} | "
        f"Exactitude hors incertain (seuil {seuil_opt}) : {acc_test_hors_incertain:.2%}",
        flush=True,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fine-tuning du modèle de diagnostic TerraMind v1.")
    p.add_argument("--backbone", default=HF_DEFAULT_MODEL)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--leaf-only", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--fast-cpu", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--max-train-per-class", type=int, default=80)
    p.add_argument("--max-eval-per-class", type=int, default=25)
    p.add_argument(
        "--crops",
        default="",
        help="Liste optionnelle de cultures séparées par des virgules (ex. tomato,onion,maize)",
    )
    return p


if __name__ == "__main__":
    raise SystemExit(entrainer(build_parser().parse_args()))
