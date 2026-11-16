"""Script de démonstration rapide des 3 modules d'Oscar :
1. Planification (/v1/plan)
2. Prévention (/v1/alert)
3. Diagnostic (/v1/diagnose)

Usage depuis PowerShell à la racine du dépôt :
    .venv\\Scripts\\python.exe -X utf8 scripts/outils/demo_modules_oscar.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.app.routes.agronomie import (
    traiter_requete_alert,
    traiter_requete_diagnose,
    traiter_requete_plan,
)


def afficher(titre: str, code: int, reponse: dict) -> None:
    print(f"\n{'=' * 70}")
    print(f" {titre}  (HTTP {code})")
    print(f"{'=' * 70}")
    print(json.dumps(reponse, indent=2, ensure_ascii=False))


def main() -> None:
    # 1. Planification : Rufisque en novembre (saison fraîche), champ en bas-fond
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
    afficher("MODULE 1 : POST /v1/plan (Rufisque, 13 nov 2026, bas-fond=oui)", code_p, rep_p)

    # 2. Prévention : Tivaouane en février sur tomate repiquée en décembre
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
        },
        autoriser_reseau=False,
    )
    afficher("MODULE 2 : POST /v1/alert (Tivaouane, Tomate, réponse en wolof + FR)", code_a, rep_a)

    # 3A. Diagnostic : Feuille de tomate nette (confiance > seuil + questions DPV)
    code_d1, rep_d1 = traiter_requete_diagnose(
        {
            "culture_declaree": "tomato",
            "qualite_image": "nette",
            "utilisateur": "demo_oscar",
            "canal": "pwa",
            "langue": "fr",
        }
    )
    afficher("MODULE 3A : POST /v1/diagnose (Feuille de tomate nette -> statut ok)", code_d1, rep_d1)

    # 3B. Diagnostic : Image floue (confiance < seuil -> statut incertain + renvoi agent)
    code_d2, rep_d2 = traiter_requete_diagnose(
        {
            "culture_declaree": "tomato",
            "qualite_image": "floue",
            "utilisateur": "demo_oscar",
            "canal": "whatsapp",
            "langue": "wo",
        }
    )
    afficher("MODULE 3B : POST /v1/diagnose (Image floue -> statut incertain)", code_d2, rep_d2)


if __name__ == "__main__":
    main()
