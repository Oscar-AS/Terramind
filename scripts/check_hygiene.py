"""Contrôles d'hygiène du dépôt : fichiers trop gros, fichiers interdits, dépendances interdites.

Utilisé par la CI (job `hygiene`) et par `make lint`. Python standard uniquement.
Ne contrôle que les fichiers suivis par git.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 1024 * 1024
MAX_SAMPLE_IMAGE_BYTES = 200 * 1024
FORBIDDEN_SUFFIXES = {
    ".pt",
    ".pth",
    ".onnx",
    ".h5",
    ".safetensors",
    ".ckpt",
    ".tif",
    ".tiff",
    ".zip",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
BANNED_DEPENDENCY = re.compile(r"ultralytics|yolov8", re.IGNORECASE)


def tracked_files() -> list[PurePosixPath]:
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    return [PurePosixPath(p) for p in out.decode("utf-8").split("\0") if p]


def is_env_file(path: PurePosixPath) -> bool:
    name = path.name
    return (name == ".env" or name.startswith(".env.")) and name != ".env.example"


def is_dependency_file(path: PurePosixPath) -> bool:
    name = path.name
    return name == "package.json" or (name.startswith("requirements") and name.endswith(".txt"))


def check(path: PurePosixPath) -> list[str]:
    local = Path(path)
    if not local.is_file():
        return []
    errors = []
    size = local.stat().st_size
    suffix = path.suffix.lower()
    top = path.parts[0]

    if size > MAX_FILE_BYTES:
        errors.append(f"{path} : fichier de {size // 1024} Ko, limite 1 Mo. Le garder hors de git.")
    if is_env_file(path):
        errors.append(
            f"{path} : fichier d'environnement interdit (seul .env.example est autorisé)."
        )
    if suffix in FORBIDDEN_SUFFIXES:
        errors.append(
            f"{path} : type de fichier interdit ({suffix}) : modèles, rasters et archives restent hors de git."
        )
    if suffix in IMAGE_SUFFIXES and top in ("research", "data"):
        if path.parts[:2] != ("data", "sample"):
            errors.append(
                f"{path} : image interdite dans {top}/ (photos d'agriculteurs jamais commitées ; "
                "seul data/sample/ accepte de petites images publiques)."
            )
        elif size > MAX_SAMPLE_IMAGE_BYTES:
            errors.append(f"{path} : image de {size // 1024} Ko, limite 200 Ko dans data/sample/.")
    if is_dependency_file(path) and BANNED_DEPENDENCY.search(local.read_text(encoding="utf-8")):
        errors.append(
            f"{path} : dépendance ultralytics / YOLOv8 interdite tant que la licence AGPL n'est pas "
            "tranchée (voir docs/decisions.md, D5)."
        )
    return errors


def main() -> int:
    errors = [error for path in tracked_files() for error in check(path)]
    for error in errors:
        print(f"ERREUR {error}")
    if errors:
        print(f"{len(errors)} problème(s) d'hygiène trouvé(s).")
        return 1
    print("Hygiène du dépôt : OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
