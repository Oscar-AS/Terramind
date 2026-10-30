"""Construit la base fusionnée TerraMind (TOM2024 raw + CCMT Raw Data) depuis les copies locales.

Étapes (décisions D7 et D8 de docs/decisions.md) :
1. étiquettes uniformisées avec data/label_mapping.csv ;
2. exclusion des images illisibles, non JPEG ou dont le petit côté fait moins de MIN_SIDE px ;
3. doublons exacts (SHA-256) : une seule copie si même classe, toutes exclues si classes différentes ;
4. retrait des classes de moins de MIN_IMAGES images ;
5. copie des images (octets d'origine, sans réencodage) et écriture des manifestes.

À lancer depuis la racine du dépôt : python ml/training/build_merged_dataset.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from datasets import Image as HFImage
from datasets import load_from_disk
from PIL import Image

TOM_DIR = Path("data_local/raw/tom2024_raw")
CCMT_DIR = Path("data_local/raw/ccmt_raw/CCMT Dataset")
MAPPING = Path("data/label_mapping.csv")
OUT = Path("data_local/processed/terramind_v1")
EXCLUSIONS_TRACKED = Path("data/exclusions/terramind_v1.csv")
MIN_SIDE = 64
MIN_IMAGES = 100


@dataclass
class Record:
    source: str
    ref: str
    crop_src: str
    label_src: str
    load: Callable[[], bytes]
    sha256: str = ""
    width: int = 0
    height: int = 0
    crop: str = ""
    label: str = ""
    reason: str = ""
    file: str = ""


def tom2024_records() -> list[Record]:
    ds = load_from_disk(str(TOM_DIR))
    names = ds.features["label"].names
    raw = ds.cast_column("image", HFImage(decode=False))
    crops, labels = ds["crop_type"], ds["label"]
    return [
        Record(
            "tom2024",
            f"row{i:05d}",
            crops[i],
            names[labels[i]],
            lambda i=i: raw[i]["image"]["bytes"],
        )
        for i in range(ds.num_rows)
    ]


def ccmt_records() -> list[Record]:
    records = []
    for path in sorted(CCMT_DIR.rglob("*.jpg")):
        crop, label = path.relative_to(CCMT_DIR).parts[:2]
        ref = "/".join(path.relative_to(CCMT_DIR).parts)
        records.append(Record("ccmt", ref, crop, label, path.read_bytes))
    return records


def inspect(record: Record) -> None:
    data = record.load()
    record.sha256 = hashlib.sha256(data).hexdigest()
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            record.width, record.height = image.size
            image_format = image.format
    except Exception:
        record.reason = "illisible"
        return
    if image_format != "JPEG":
        record.reason = "format_non_jpeg"
    elif min(record.width, record.height) < MIN_SIDE:
        record.reason = f"petit_cote_moins_de_{MIN_SIDE}px"


def mark_duplicates(records: list[Record]) -> None:
    groups = defaultdict(list)
    for record in records:
        if not record.reason:
            groups[record.sha256].append(record)
    for group in groups.values():
        if len(group) < 2:
            continue
        if len({(r.crop, r.label) for r in group}) > 1:
            for record in group:
                record.reason = "doublon_etiquettes_differentes"
        else:
            for record in group[1:]:
                record.reason = "doublon_meme_classe"


def main() -> int:
    if OUT.exists():
        print(f"{OUT} existe déjà : le supprimer ou le renommer avant de reconstruire.")
        return 1
    with MAPPING.open(encoding="utf-8") as handle:
        mapping = {(m["source"], m["crop_src"], m["label_src"]): m for m in csv.DictReader(handle)}

    records = tom2024_records() + ccmt_records()
    records.sort(key=lambda r: (r.source, r.ref))
    for record in records:
        target = mapping.get((record.source, record.crop_src, record.label_src))
        if target is None:
            print(
                f"Étiquette absente de {MAPPING} : {record.source} {record.crop_src}/{record.label_src}"
            )
            return 1
        record.crop, record.label = target["crop"], target["label"]
        inspect(record)
    mark_duplicates(records)

    counts = Counter((r.crop, r.label) for r in records if not r.reason)
    for record in records:
        if not record.reason and counts[(record.crop, record.label)] < MIN_IMAGES:
            record.reason = f"classe_moins_de_{MIN_IMAGES}_images"
    kept = [r for r in records if not r.reason]

    for record in kept:
        record.file = (
            f"images/{record.crop}/{record.label}/{record.source}_{record.sha256[:16]}.jpg"
        )
        target = OUT / record.file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(record.load())

    labels = {(m["crop"], m["label"]): m for m in mapping.values()}
    with (OUT / "manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "file",
                "crop",
                "label",
                "categorie",
                "source",
                "source_ref",
                "crop_src",
                "label_src",
                "sha256",
                "width",
                "height",
            ]
        )
        for r in kept:
            writer.writerow(
                [
                    r.file,
                    r.crop,
                    r.label,
                    labels[(r.crop, r.label)]["categorie"],
                    r.source,
                    r.ref,
                    r.crop_src,
                    r.label_src,
                    r.sha256,
                    r.width,
                    r.height,
                ]
            )

    per_source = Counter((r.crop, r.label, r.source) for r in kept)
    with (OUT / "classes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["crop", "label", "categorie", "libelle_fr", "images", "tom2024", "ccmt"])
        for crop, label in sorted(Counter((r.crop, r.label) for r in kept)):
            info = labels[(crop, label)]
            tom, ccmt = per_source[(crop, label, "tom2024")], per_source[(crop, label, "ccmt")]
            writer.writerow(
                [crop, label, info["categorie"], info["libelle_fr"], tom + ccmt, tom, ccmt]
            )

    excluded = [r for r in records if r.reason]
    for path in (OUT / "exclusions.csv", EXCLUSIONS_TRACKED):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["source", "source_ref", "crop_src", "label_src", "raison"])
            writer.writerows([r.source, r.ref, r.crop_src, r.label_src, r.reason] for r in excluded)

    print(f"images lues : {len(records)} | conservées : {len(kept)} | exclues : {len(excluded)}")
    for reason, n in Counter(r.reason for r in excluded).most_common():
        print(f"  exclues, {reason} : {n}")
    print(f"classes : {len(counts) - sum(1 for n in counts.values() if n < MIN_IMAGES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
