"""Vérifie le contenu agronomique : gabarits FR/wolof, audios wolof, règles sol -> culture, fiches.

Utilisé par la CI (job `content`) et par `make check-content`. Python standard uniquement.
À lancer depuis la racine du dépôt. Formats attendus :

- content/templates/fr.json et wo.json : objet {identifiant: gabarit}. Un gabarit est une chaîne
  ou un objet. Un gabarit qui parle de météo ou de sol (champ `theme` valant meteo, climat ou sol,
  ou identifiant contenant l'un de ces mots) doit être un objet avec `source` et `date` non vides.
- content/audio/wo/<identifiant>.<ext> : un audio par gabarit wolof, 150 Ko maximum.
- content/regles_sol_culture.csv : en-têtes obligatoires, `source` renseignée sur chaque ligne.
- content/fiches/*.md : en-tête entre deux lignes `---` (lignes `cle: valeur`) avec `source`,
  `date` et `validee_par`. Une fiche qui contient un dosage doit déclarer `dosage_source`.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

CONTENT = Path("content")
TEMPLATES = {"fr": CONTENT / "templates" / "fr.json", "wo": CONTENT / "templates" / "wo.json"}
AUDIO_DIR = CONTENT / "audio" / "wo"
RULES_CSV = CONTENT / "regles_sol_culture.csv"
FICHES_DIR = CONTENT / "fiches"

MAX_AUDIO_BYTES = 150 * 1024
RULES_HEADERS = [
    "culture",
    "texture_sol",
    "ph_min",
    "ph_max",
    "besoin_eau",
    "saison_semis",
    "source",
    "validee_par",
]
FICHE_REQUIRED = ["source", "date", "validee_par"]
SOURCED_THEMES = {"meteo", "météo", "climat", "sol", "sols"}
DOSAGE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:mg|g|kg|ml|cl|l)\s*/\s*(?:l|ha)\b|%\s*de\s+produit",
    re.IGNORECASE,
)

errors: list[str] = []
warnings: list[str] = []


def files_in(directory: Path, pattern: str = "*") -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob(pattern) if p.is_file() and p.name != ".gitkeep")


def empty_fields(value: object, where: str) -> list[str]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return [where]
    if isinstance(value, dict):
        if not value:
            return [where]
        return [e for k, v in value.items() for e in empty_fields(v, f"{where}.{k}")]
    if isinstance(value, list):
        if not value:
            return [where]
        return [e for i, v in enumerate(value) for e in empty_fields(v, f"{where}[{i}]")]
    return []


def needs_source(key: str, template: object) -> bool:
    if isinstance(template, dict) and str(template.get("theme", "")).lower() in SOURCED_THEMES:
        return True
    return any(token in SOURCED_THEMES for token in re.split(r"[^a-zé]+", key.lower()))


def load_template_file(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path} : JSON invalide ({exc}).")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path} : doit être un objet {{identifiant: gabarit}}.")
        return None
    for key, template in data.items():
        for field in empty_fields(template, key):
            errors.append(f"{path} : valeur vide pour « {field} ».")
        if needs_source(key, template):
            if not isinstance(template, dict) or empty_fields(
                {k: template.get(k) for k in ("source", "date")}, key
            ):
                errors.append(
                    f"{path} : le gabarit « {key} » parle de météo ou de sol : "
                    "champs `source` et `date` obligatoires."
                )
    return data


def check_templates() -> dict | None:
    present = {lang: path for lang, path in TEMPLATES.items() if path.is_file()}
    if not present:
        return None
    for lang, path in TEMPLATES.items():
        if lang not in present:
            errors.append(f"{path} manquant : fr.json et wo.json vont ensemble.")
    loaded = {lang: load_template_file(path) for lang, path in present.items()}
    fr, wo = loaded.get("fr"), loaded.get("wo")
    if fr is not None and wo is not None:
        for key in sorted(fr.keys() - wo.keys()):
            errors.append(f"Gabarit « {key} » présent en français mais absent en wolof.")
        for key in sorted(wo.keys() - fr.keys()):
            errors.append(f"Gabarit « {key} » présent en wolof mais absent en français.")
    return wo


def check_audio(wo: dict | None) -> bool:
    audios = files_in(AUDIO_DIR)
    for audio in audios:
        size = audio.stat().st_size
        if size > MAX_AUDIO_BYTES:
            errors.append(f"{audio} : {size // 1024} Ko, limite 150 Ko par audio.")
    if wo is not None:
        stems = {audio.stem for audio in audios}
        for key in sorted(wo.keys() - stems):
            warnings.append(f"Gabarit wolof « {key} » sans audio dans {AUDIO_DIR}/.")
    return bool(audios)


def check_rules() -> bool:
    if not RULES_CSV.is_file():
        return False
    with RULES_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [h for h in RULES_HEADERS if h not in (reader.fieldnames or [])]
        if missing:
            errors.append(f"{RULES_CSV} : en-têtes manquants : {', '.join(missing)}.")
        for line, row in enumerate(reader, start=2):
            if not (row.get("source") or "").strip():
                errors.append(f"{RULES_CSV}, ligne {line} : `source` vide.")
    return True


def split_front_matter(text: str) -> tuple[dict[str, str] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            meta = {}
            for entry in lines[1:end]:
                key, sep, value = entry.partition(":")
                if sep:
                    meta[key.strip()] = value.strip().strip("\"'")
            return meta, "\n".join(lines[end + 1 :])
    return None, text


def check_fiches() -> bool:
    fiches = files_in(FICHES_DIR, "*.md")
    for fiche in fiches:
        meta, body = split_front_matter(fiche.read_text(encoding="utf-8"))
        if meta is None:
            errors.append(f"{fiche} : en-tête manquant (bloc entre deux lignes ---).")
            meta = {}
        for key in FICHE_REQUIRED:
            if not meta.get(key):
                errors.append(f"{fiche} : champ d'en-tête `{key}` manquant ou vide.")
        dosage = DOSAGE.search(body)
        if dosage and not meta.get("dosage_source"):
            errors.append(
                f"{fiche} : dosage détecté (« {dosage.group(0)} ») sans `dosage_source` "
                "dans l'en-tête. Les fiches ne donnent pas de dosage sans source."
            )
    return bool(fiches)


def main() -> int:
    wo = check_templates()
    checked = [any(p.is_file() for p in TEMPLATES.values())]
    checked += [check_audio(wo), check_rules(), check_fiches()]
    if not any(checked):
        print("Contenu : rien à vérifier.")
        return 0
    for warning in warnings:
        print(f"AVERTISSEMENT {warning}")
    for error in errors:
        print(f"ERREUR {error}")
    if errors:
        print(f"{len(errors)} problème(s) de contenu trouvé(s).")
        return 1
    print("Contenu : OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
