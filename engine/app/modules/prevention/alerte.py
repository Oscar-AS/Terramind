"""Alertes de la semaine pour une culture déclarée (POST /v1/alert)."""

from __future__ import annotations

import datetime as dt

from .. import meteo
from . import regles

SOURCE_SEUILS = {"document": "Seuils météo des maladies et ravageurs (docs/sources/seuils-meteo-maladies-ravageurs.md)",
                 "page": "§ 1 à 5"}
CONSEILS = {
    ("late_blight", "favorable"): "Le temps de ces derniers jours est favorable au mildiou. "
                                  "Regarde le dessous des feuilles : taches brunes avec un duvet blanc.",
    ("alternaria", "favorable"): "Le temps de ces derniers jours est favorable à l'alternariose. "
                                 "Regarde les vieilles feuilles : taches brunes avec des cercles.",
    ("tuta_absoluta", "surveiller"): "Une nouvelle génération de mineuse est probable. "
                                     "Regarde s'il y a des galeries claires dans les feuilles.",
    ("plutella_xylostella", "surveiller"): "Une nouvelle génération de teigne du chou est probable. "
                                           "Regarde tes choux de près, surtout le dessous des feuilles.",
}
MALADIES = {"late_blight": ("tomato", "potato"), "alternaria": ("tomato", "potato")}
FENETRE_JOURS = 7
RETARD_POWER_JOURS = 3  # NASA POWER publie avec quelques jours de retard


def calculer(lat: float, lon: float, culture: str, date: dt.date, date_repiquage: dt.date | None) -> dict:
    fin = date - dt.timedelta(days=RETARD_POWER_JOURS)
    debut = fin - dt.timedelta(days=FENETRE_JOURS)
    alertes = []

    if any(culture in c for c in MALADIES.values()):
        jours = regles.resume_jours(meteo.horaire(lat, lon, debut, fin))
        if not jours:
            raise meteo.MeteoIndisponible("aucune journée complète dans la période")
        periode = [jours[0]["date"].isoformat(), jours[-1]["date"].isoformat()]
        hutton = regles.jours_hutton(jours)
        alertes.append({
            "risque": "late_blight", "regle": "hutton_plafonne",
            "niveau": "favorable" if hutton else "aucun",
            "detail": {"jours_conditions_remplies": len(hutton), "plafond_c": regles.PLAFOND_MILDIOU},
        })
        dsv = sum(j["dsv"] for j in jours)
        alertes.append({
            "risque": "alternaria", "regle": "tomcast",
            "niveau": "favorable" if dsv >= regles.SEUIL_TOMCAST else "aucun",
            "detail": {"notes_cumulees": dsv, "seuil": regles.SEUIL_TOMCAST, "fenetre_jours": len(jours)},
        })
    else:
        periode = [debut.isoformat(), fin.isoformat()]

    for risque, (cible, seuil, dd_gen) in regles.RAVAGEURS.items():
        if culture != cible or date_repiquage is None or date_repiquage >= fin:
            continue
        serie = meteo.journalier(lat, lon, date_repiquage, fin)
        gen = regles.generations(serie, seuil, dd_gen)
        alertes.append({
            "risque": risque, "regle": "degres_jours",
            "niveau": "surveiller" if gen >= regles.GENERATION_SURVEILLER else "aucun",
            "detail": {"generations_depuis_repiquage": round(gen, 1), "seuil_c": seuil,
                       "degres_jours_par_generation": dd_gen},
        })

    for a in alertes:
        a["id"] = f"a-{date.isoformat()}-{a['risque']}-{round(lat, 2)}-{round(lon, 2)}"
        a["conseil"] = CONSEILS.get((a["risque"], a["niveau"]))
    return {"alertes": alertes,
            "meteo": {"source": "NASA POWER (horaire et journalier)", "periode": periode}}
