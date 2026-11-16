"""Découpage stratifié et reproductible de terramind_v1 en train (80 %), val (10 %) et test (10 %).

Stratification par (crop, label, source) après tri par empreinte SHA-256 :
- garantit que chaque classe (même les plus petites comme tomato/late_blight à 72 images)
  est présente dans train, val et test dans les mêmes proportions ;
- garantit que les deux sources (TOM2024 et CCMT) sont équilibrées dans chaque split ;
- marque les 2 classes de fruits de la tomate (`healthy_fruit`, `blossom_end_rot`) pour
  permettre un entraînement strictement « feuilles » (`--leaf-only`) ou complet.

Entrée : data_local/processed/terramind_v1/manifest.csv
Sorties :
- data_local/processed/terramind_v1/splits.csv (hors Git, 35 448 lignes avec colonne `split`)
- data/splits_terramind_v1.csv (suivi dans Git : effectifs train/val/test par classe)

À lancer depuis la racine :
    .venv\\Scripts\\python.exe ml/training/split_dataset.py
"""

from __future__ import annotations

import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

MANIFEST = Path("data_local/processed/terramind_v1/manifest.csv")
CLASSES_CSV = Path("data_local/processed/terramind_v1/classes.csv")
SPLITS_OUT = Path("data_local/processed/terramind_v1/splits.csv")
SUMMARY_OUT = Path("data/splits_terramind_v1.csv")

SEED = 42
VAL_RATIO = 0.10
TEST_RATIO = 0.10
CLASSES_FRUITS = {("tomato", "healthy_fruit"), ("tomato", "blossom_end_rot")}


def assigner_splits(lignes: list[dict], seed: int = SEED) -> list[dict]:
    """Assigne 'train', 'val' ou 'test' par strate (crop, label, source)."""
    strates: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in sorted(lignes, key=lambda r: r["sha256"]):
        clef = (row["crop"], row["label"], row["source"])
        strates[clef].append(row)

    resultat: list[dict] = []
    for clef in sorted(strates):
        groupe = list(strates[clef])
        rng = random.Random(f"{seed}:{clef[0]}:{clef[1]}:{clef[2]}")
        rng.shuffle(groupe)
        n = len(groupe)
        n_test = max(1, int(round(n * TEST_RATIO)))
        n_val = max(1, int(round(n * VAL_RATIO)))
        for idx, item in enumerate(groupe):
            copie = dict(item)
            if idx < n_test:
                copie["split"] = "test"
            elif idx < n_test + n_val:
                copie["split"] = "val"
            else:
                copie["split"] = "train"
            copie["est_feuille"] = (
                "non" if (copie["crop"], copie["label"]) in CLASSES_FRUITS else "oui"
            )
            resultat.append(copie)

    resultat.sort(key=lambda r: r["file"])
    return resultat


def main() -> int:
    if not MANIFEST.is_file():
        print(f"Manifeste introuvable : {MANIFEST}. Lancer d'abord build_merged_dataset.py.")
        return 1

    with MANIFEST.open(encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))

    libelles: dict[tuple[str, str], str] = {}
    if CLASSES_CSV.is_file():
        with CLASSES_CSV.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                libelles[(r["crop"], r["label"])] = r["libelle_fr"]

    avec_splits = assigner_splits(lignes)

    colonnes_splits = [
        "file",
        "split",
        "crop",
        "label",
        "categorie",
        "est_feuille",
        "source",
        "source_ref",
        "crop_src",
        "label_src",
        "sha256",
        "width",
        "height",
    ]
    with SPLITS_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes_splits, lineterminator="\n")
        writer.writeheader()
        writer.writerows(avec_splits)

    compteurs = Counter((r["crop"], r["label"], r["split"]) for r in avec_splits)
    sources_cnt = Counter((r["crop"], r["label"], r["source"]) for r in avec_splits)
    categories = {(r["crop"], r["label"]): r["categorie"] for r in avec_splits}

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(
            [
                "crop",
                "label",
                "categorie",
                "libelle_fr",
                "est_feuille",
                "train",
                "val",
                "test",
                "total",
                "tom2024",
                "ccmt",
            ]
        )
        for crop, label in sorted(categories):
            n_tr = compteurs[(crop, label, "train")]
            n_va = compteurs[(crop, label, "val")]
            n_te = compteurs[(crop, label, "test")]
            n_tom = sources_cnt[(crop, label, "tom2024")]
            n_ccmt = sources_cnt[(crop, label, "ccmt")]
            est_f = "non" if (crop, label) in CLASSES_FRUITS else "oui"
            w.writerow(
                [
                    crop,
                    label,
                    categories[(crop, label)],
                    libelles.get((crop, label), label),
                    est_f,
                    n_tr,
                    n_va,
                    n_te,
                    n_tr + n_va + n_te,
                    n_tom,
                    n_ccmt,
                ]
            )

    tot_split = Counter(r["split"] for r in avec_splits)
    print(
        f"Découpage terminé ({len(avec_splits)} images) : "
        f"train={tot_split['train']} | val={tot_split['val']} | test={tot_split['test']}"
    )
    print(f"Fichiers écrits : {SPLITS_OUT} et {SUMMARY_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
