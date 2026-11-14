"""Script de démonstration rapide des modules Planification (/v1/plan) et Prévention (/v1/alert).

Usage depuis PowerShell à la racine du dépôt :
    .venv\\Scripts\\python.exe scripts/outils/demo_modules_oscar.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.app.routes.agronomie import traiter_requete_alert, traiter_requete_plan


def afficher(titre: str, code: int, reponse: dict) -> None:
    print(f"\n{'=' * 70}")
    print(f" {titre}  (HTTP {code})")
    print(f"{'=' * 70}")
    print(json.dumps(reponse, indent=2, ensure_ascii=False))


def main() -> None:
    # 1. Exemple Planification : Rufisque en novembre (saison fraîche), champ en bas-fond
    code_p, rep_p = traiter_requete_plan(
        {
            "lat": 14.76,
            "lon": -17.21,
            "date": "2026-11-13",
            "eau_puits_salee": "non",
            "champ_en_bas_fond": "oui",
            "utilisateur": "demo_oscar",
            "canal": "pwa",
            "langue": "fr",
        }
    )
    afficher("TEST 1 : POST /v1/plan (Rufisque, 13 nov 2026, bas-fond=oui)", code_p, rep_p)

    # 2. Exemple Prévention : Tivaouane en février sur tomate repiquée en décembre
    code_a, rep_a = traiter_requete_alert(
        {
            "lat": 15.09,
            "lon": -16.65,
            "culture": "tomato",
            "date_repiquage": "2026-12-01",
            "date": "2027-02-10",
            "utilisateur": "demo_oscar",
            "canal": "whatsapp",
            "langue": "wo",
        }
    )
    afficher("TEST 2 : POST /v1/alert (Tivaouane, Tomate, réponse en wolof + FR)", code_a, rep_a)


if __name__ == "__main__":
    main()
