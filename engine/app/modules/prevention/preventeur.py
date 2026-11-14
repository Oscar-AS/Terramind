"""Module Prévention : calcul des risques météo (mildiou, alternariose, ravageurs).

Conformément aux décisions D6, D7 et D11 (docs/decisions.md), aux seuils documentés
(docs/sources/seuils-meteo-maladies-ravageurs.md) et au contrat d'API (docs/api.md § 4) :
- Sans culture déclarée, aucune alerte n'est calculée (statut = 'culture_requise').
- Les règles utilisées sont :
  1. Mildiou (late_blight, tomate/pomme de terre) : critères de Hutton plafonnés à 26,6 °C (Wallin).
  2. Alternariose (alternaria, tomate/pomme de terre) : modèle TOMCAST (UC IPM / Madden et al. 1978).
  3. Mineuse de la tomate (tuta_absoluta, tomate) : degrés-jours (seuil 8,0 °C, 440 DJ/génération).
  4. Teigne du chou (plutella_xylostella, chou) : degrés-jours (seuil 7,3 °C, 290 DJ/génération).
- Les conseils disent toujours « conditions favorables » ou « surveille », jamais « ta culture est malade »,
  et ne prescrivent aucun produit chimique ni aucune dose.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

from ..planification.planificateur import arrondir_gps, sol

RACINE = Path(__file__).resolve().parents[4]
POWER_DIR = RACINE / "data" / "raw" / "nasa_power"
CALENDRIER_CSV = RACINE / "data" / "extraits" / "prevention_calendrier_2020-2025.csv"

POWER_HORAIRE_URL = (
    "https://power.larc.nasa.gov/api/temporal/hourly/point"
    "?parameters=T2M,RH2M,PRECTOTCORR&community=AG"
    "&longitude={lon}&latitude={lat}&start={debut}&end={fin}&format=CSV&time-standard=UTC"
)

PLAFOND_MILDIOU_C = 26.6  # Borne haute de Wallin (Blitecast)
TUTA_SEUIL_C, TUTA_DJ_GENERATION = 8.0, 440
TEIGNE_SEUIL_C, TEIGNE_DJ_GENERATION = 7.3, 290

# Tableau TOMCAST (UC IPM) : (t_min_incluse, t_max_exclue) -> seuils d'heures RH>=90% pour notes 1, 2, 3, 4
TOMCAST = [
    ((13.0, 18.0), (7, 16, 21, None)),
    ((18.0, 21.0), (4, 9, 16, 23)),
    ((21.0, 26.0), (3, 6, 13, 21)),
    ((26.0, 30.0), (4, 9, 16, 23)),
]

CULTURES_CONNUES = {
    "tomato",
    "potato",
    "cabbage",
    "onion",
    "pepper",
    "chili",
    "bitter_eggplant",
    "carrot",
    "maize",
}


def note_tomcast(heures_hr90: int, temp_moy_humide: float) -> int:
    """Calcule la note journalière TOMCAST (0 à 4) à partir des heures à RH >= 90 % et leur T moyenne."""
    if heures_hr90 <= 0:
        return 0
    for (bas, haut), seuils in TOMCAST:
        if bas <= temp_moy_humide < haut:
            return sum(1 for s in seuils if s is not None and heures_hr90 >= s)
    return 0


def parser_csv_nasa_power(texte_csv: str) -> list[tuple[dt.date, float, float]]:
    """Extrait les relevés horaires (date, T2M, RH2M) depuis un texte CSV NASA POWER."""
    if "-END HEADER-" in texte_csv:
        corps = texte_csv.split("-END HEADER-", 1)[1].lstrip()
    else:
        corps = texte_csv.lstrip()
    releves: list[tuple[dt.date, float, float]] = []
    for r in csv.DictReader(io.StringIO(corps)):
        try:
            t = float(r["T2M"])
            h = float(r["RH2M"])
            if t <= -900 or h <= -900:
                continue
            d = dt.date(int(r["YEAR"]), int(r["MO"]), int(r["DY"]))
            releves.append((d, t, h))
        except (KeyError, ValueError):
            continue
    return releves


def agreger_jours_meteo(releves: list[tuple[dt.date, float, float]]) -> list[dict]:
    """Agrège les relevés horaires en indicateurs journaliers (Hutton plafonné, TOMCAST, degrés-jours)."""
    par_jour: dict[dt.date, dict] = defaultdict(lambda: {"t": [], "humide": [], "humide_frais": 0})
    for d, t, h in releves:
        par_jour[d]["t"].append(t)
        if h >= 90.0:
            par_jour[d]["humide"].append(t)
            if t <= PLAFOND_MILDIOU_C:
                par_jour[d]["humide_frais"] += 1

    jours: list[dict] = []
    for d in sorted(par_jour):
        info = par_jour[d]
        if len(info["t"]) < 18:
            continue
        tmin, tmax = min(info["t"]), max(info["t"])
        h90 = len(info["humide"])
        h90_frais = info["humide_frais"]
        t_moy_humide = sum(info["humide"]) / h90 if h90 else 0.0
        cond_jour_mildiou = tmin >= 10.0 and h90_frais >= 6
        jours.append(
            {
                "date": d,
                "tmin": tmin,
                "tmax": tmax,
                "h90": h90,
                "h90_frais": h90_frais,
                "cond_mildiou": cond_jour_mildiou,
                "dsv": note_tomcast(h90, t_moy_humide),
                "dd_tuta": max(0.0, (tmax + tmin) / 2.0 - TUTA_SEUIL_C),
                "dd_teigne": max(0.0, (tmax + tmin) / 2.0 - TEIGNE_SEUIL_C),
            }
        )

    for i, j in enumerate(jours):
        if i == 0:
            j["hutton_plafonne"] = False
        else:
            j["hutton_plafonne"] = bool(jours[i - 1]["cond_mildiou"] and j["cond_mildiou"])
    return jours


def _charger_meteo_locale_ou_api(
    lat: float,
    lon: float,
    point_pilote: str,
    debut: dt.date,
    fin: dt.date,
    autoriser_reseau: bool = True,
) -> tuple[list[dict], str]:
    """Tente de lire les relevés horaires depuis data/raw/nasa_power/ ou l'API NASA POWER."""
    releves: list[tuple[dt.date, float, float]] = []
    dossier_point = POWER_DIR / point_pilote.lower()
    if dossier_point.is_dir():
        for an in range(debut.year, fin.year + 1):
            f_an = dossier_point / f"horaire_{an}.csv"
            if f_an.is_file():
                for d, t, h in parser_csv_nasa_power(f_an.read_text(encoding="utf-8")):
                    if debut <= d <= fin:
                        releves.append((d, t, h))
        if releves:
            jours = agreger_jours_meteo(releves)
            if jours:
                return jours, "NASA POWER horaire"

    # Si date non future et réseau autorisé, interroger l'API NASA POWER en direct
    if autoriser_reseau and fin <= dt.date.today():
        url = POWER_HORAIRE_URL.format(
            lon=lon,
            lat=lat,
            debut=debut.strftime("%Y%m%d"),
            fin=fin.strftime("%Y%m%d"),
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TerraMind-Afrique/0.1"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                texte = resp.read().decode("utf-8")
            releves_api = parser_csv_nasa_power(texte)
            jours_api = agreger_jours_meteo(releves_api)
            if jours_api:
                return jours_api, "NASA POWER horaire"
        except (urllib.error.URLError, TimeoutError, OSError):
            pass

    return [], ""


def _charger_calendrier_climatologique(point_pilote: str, mois: int) -> dict:
    """Lit la ligne correspondante dans data/extraits/prevention_calendrier_2020-2025.csv."""
    clef = point_pilote.lower()
    with CALENDRIER_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["point"].strip().lower() == clef and int(row["mois"]) == mois:
                return {
                    "jours_hutton_plafonne_par_mois": float(row["jours_hutton_plafonne_par_mois"]),
                    "notes_tomcast_par_mois": float(row["notes_tomcast_par_mois"]),
                    "heures_hr90_par_jour": float(row["heures_hr90_par_jour"]),
                    "jours_par_generation_mineuse": int(row["jours_par_generation_mineuse"]),
                    "jours_par_generation_teigne": int(row["jours_par_generation_teigne"]),
                }
    raise ValueError(f"Aucune entrée climatologique pour {point_pilote} au mois {mois}")


def calculer_alertes(
    lat: float,
    lon: float,
    culture: str | None = None,
    date_repiquage: str | dt.date | None = None,
    date: str | dt.date | None = None,
    releves_horaires: list[tuple[dt.date, float, float]] | None = None,
    autoriser_reseau: bool = True,
) -> dict:
    """Calcule les alertes météo de la semaine pour POST /v1/alert."""
    lat_arr, lon_arr = arrondir_gps(lat, lon)

    if date is None:
        date_eval = dt.date.today()
    elif isinstance(date, dt.date):
        date_eval = date
    else:
        date_eval = dt.date.fromisoformat(str(date))

    debut_7j = date_eval - dt.timedelta(days=7)

    # Garde-fou obligatoire (docs/api.md § 4) : sans culture déclarée, statut = culture_requise
    culture_norm = (culture or "").strip().lower()
    if not culture_norm:
        return {
            "statut": "culture_requise",
            "alertes": [],
            "meteo": {
                "source": "NASA POWER horaire",
                "date": date_eval.isoformat(),
                "periode": [debut_7j.isoformat(), date_eval.isoformat()],
            },
            "sources": [
                {
                    "document": "Critères de Hutton / Wallin (Blitecast), TOMCAST (UC IPM) et degrés-jours (DPV Sénégal)",
                    "page": "docs/sources/seuils-meteo-maladies-ravageurs.md",
                }
            ],
        }

    # Vérification que la position GPS est dans la zone couverte (réutilise sol())
    infos_sol = sol(lat_arr, lon_arr)
    point_pilote = infos_sol["departement_proche"].lower()

    if date_repiquage is None:
        repiquage_obj = date_eval - dt.timedelta(days=45)
    elif isinstance(date_repiquage, dt.date):
        repiquage_obj = date_repiquage
    else:
        repiquage_obj = dt.date.fromisoformat(str(date_repiquage))

    debut_collecte = min(debut_7j, repiquage_obj)
    if releves_horaires is not None:
        jours_meteo = agreger_jours_meteo(releves_horaires)
        source_meteo = "NASA POWER horaire"
    else:
        jours_meteo, source_meteo = _charger_meteo_locale_ou_api(
            lat_arr,
            lon_arr,
            point_pilote,
            debut_collecte,
            date_eval,
            autoriser_reseau=autoriser_reseau,
        )

    jours_7j = [j for j in jours_meteo if debut_7j <= j["date"] <= date_eval]
    clim = _charger_calendrier_climatologique(point_pilote, date_eval.month)
    if not source_meteo:
        source_meteo = "NASA POWER horaire (référence 2020-2025)"

    alertes: list[dict] = []
    prefixe_id = f"a-{date_eval.isoformat()}-{point_pilote}"

    # 1. Mildiou (late_blight) et Alternariose (alternaria) : tomate et pomme de terre
    if culture_norm in ("tomato", "potato"):
        if len(jours_7j) >= 2:
            nb_hutton = sum(1 for j in jours_7j if j["hutton_plafonne"])
            nb_cond_jour = sum(1 for j in jours_7j if j["cond_mildiou"])
            jours_remplis = 2 if nb_hutton >= 1 else (1 if nb_cond_jour >= 1 else 0)
            dsv_7j = sum(j["dsv"] for j in jours_7j)
        else:
            # Estimation hebdomadaire à partir du calendrier 2020-2025 NASA POWER du point pilote
            hutton_mois = clim["jours_hutton_plafonne_par_mois"]
            if hutton_mois >= 3.5:
                jours_remplis = 2
            elif hutton_mois >= 1.5:
                jours_remplis = 1
            else:
                jours_remplis = 0
            dsv_7j = int(round(clim["notes_tomcast_par_mois"] * 7.0 / 30.0))

        if jours_remplis >= 2:
            niveau_mildiou = "favorable"
            conseil_mildiou = (
                "Les conditions sont favorables au mildiou cette semaine : "
                "surveille le dessous des feuilles et évite d'arroser le feuillage le soir."
            )
        elif jours_remplis == 1:
            niveau_mildiou = "surveiller"
            conseil_mildiou = (
                "Une journée humide et fraîche a été relevée : "
                "surveille l'apparition de taches huileuses sur le bord des feuilles."
            )
        else:
            niveau_mildiou = "aucun"
            conseil_mildiou = (
                "L'air reste trop sec ou trop chaud pour favoriser le mildiou cette semaine : "
                "maintiens une surveillance habituelle."
            )

        alertes.append(
            {
                "id": f"{prefixe_id}-late_blight",
                "risque": "late_blight",
                "niveau": niveau_mildiou,
                "regle": "hutton_plafonne",
                "detail": {
                    "jours_conditions_remplies": jours_remplis,
                    "plafond_c": PLAFOND_MILDIOU_C,
                },
                "conseil": conseil_mildiou,
            }
        )

        if dsv_7j >= 5:
            niveau_alt = "favorable"
            conseil_alt = (
                "Les rosées et températures sont favorables à l'alternariose : "
                "surveille les taches noires en anneaux sur les feuilles basses."
            )
        elif dsv_7j >= 3:
            niveau_alt = "surveiller"
            conseil_alt = (
                "Humectation modérée du feuillage : "
                "inspecte les vieilles feuilles à la base des plants."
            )
        else:
            niveau_alt = "aucun"
            conseil_alt = "Risque d'alternariose faible sur les 7 derniers jours."

        alertes.append(
            {
                "id": f"{prefixe_id}-alternaria",
                "risque": "alternaria",
                "niveau": niveau_alt,
                "regle": "tomcast",
                "detail": {"notes_cumulees_7j": dsv_7j},
                "conseil": conseil_alt,
            }
        )

    # 2. Mineuse de la tomate (tuta_absoluta) : tomate
    if culture_norm == "tomato":
        jours_depuis_rep = [j for j in jours_meteo if repiquage_obj <= j["date"] <= date_eval]
        nb_jours_ecoules = max(0, (date_eval - repiquage_obj).days)
        if len(jours_depuis_rep) >= max(5, nb_jours_ecoules - 3) and nb_jours_ecoules > 0:
            dj_cumul = sum(j["dd_tuta"] for j in jours_depuis_rep)
            generations = round(dj_cumul / TUTA_DJ_GENERATION, 1)
        else:
            # Calcul par le rythme moyen de génération du mois au point pilote (NASA POWER 2020-2025)
            generations = round(nb_jours_ecoules / clim["jours_par_generation_mineuse"], 1)

        if generations >= 2.0:
            niveau_tuta = "surveiller"
            conseil_tuta = (
                "Une nouvelle génération de mineuse est probable : "
                "regarde s'il y a des galeries claires dans les feuilles et retire les feuilles atteintes."
            )
        elif generations >= 0.8:
            niveau_tuta = "surveiller"
            conseil_tuta = (
                "La première génération depuis le repiquage approche : "
                "inspecte les jeunes feuilles du sommet."
            )
        else:
            niveau_tuta = "aucun"
            conseil_tuta = (
                "Culture jeune : maintiens les filets ou l'observation régulière des feuilles."
            )

        alertes.append(
            {
                "id": f"{prefixe_id}-tuta_absoluta",
                "risque": "tuta_absoluta",
                "niveau": niveau_tuta,
                "regle": "degres_jours",
                "detail": {
                    "generations_depuis_repiquage": generations,
                    "seuil_c": TUTA_SEUIL_C,
                    "degres_jours_par_generation": TUTA_DJ_GENERATION,
                },
                "conseil": conseil_tuta,
            }
        )

    # 3. Teigne du chou (plutella_xylostella) : chou pommé
    if culture_norm == "cabbage":
        jours_depuis_rep = [j for j in jours_meteo if repiquage_obj <= j["date"] <= date_eval]
        nb_jours_ecoules = max(0, (date_eval - repiquage_obj).days)
        if len(jours_depuis_rep) >= max(5, nb_jours_ecoules - 3) and nb_jours_ecoules > 0:
            dj_cumul = sum(j["dd_teigne"] for j in jours_depuis_rep)
            generations = round(dj_cumul / TEIGNE_DJ_GENERATION, 1)
        else:
            generations = round(nb_jours_ecoules / clim["jours_par_generation_teigne"], 1)

        if generations >= 2.0 or date_eval.month == 2:
            niveau_teigne = "surveiller"
            conseil_teigne = (
                "Une nouvelle génération de teigne du chou est probable : "
                "inspecte le cœur de la pomme et le dessous des feuilles (petites chenilles vertes)."
            )
        elif generations >= 0.8:
            niveau_teigne = "surveiller"
            conseil_teigne = (
                "Fin de la première génération depuis le repiquage : "
                "vérifie l'absence de petites fenêtres transparentes sur les feuilles."
            )
        else:
            niveau_teigne = "aucun"
            conseil_teigne = "Début de cycle : surveille l'état des jeunes plants après repiquage."

        alertes.append(
            {
                "id": f"{prefixe_id}-plutella_xylostella",
                "risque": "plutella_xylostella",
                "niveau": niveau_teigne,
                "regle": "degres_jours",
                "detail": {
                    "generations_depuis_repiquage": generations,
                    "seuil_c": TEIGNE_SEUIL_C,
                    "degres_jours_par_generation": TEIGNE_DJ_GENERATION,
                },
                "conseil": conseil_teigne,
            }
        )

    # 4. Oignon (taches pourpres / mildiou de l'oignon selon humectation)
    if culture_norm == "onion":
        h90_moy = (
            round(sum(j["h90"] for j in jours_7j) / len(jours_7j), 1)
            if jours_7j
            else clim["heures_hr90_par_jour"]
        )
        if h90_moy >= 4.0:
            niveau_oignon = "surveiller"
            conseil_oignon = (
                "Les rosées prolongées favorisent les taches foliaires de l'oignon : "
                "surveille l'extrémité des feuilles et évite tout excès d'azote."
            )
        else:
            niveau_oignon = "aucun"
            conseil_oignon = "Humidité modérée cette semaine : surveille principalement les thrips au cœur des feuilles."

        alertes.append(
            {
                "id": f"{prefixe_id}-alternaria_porri",
                "risque": "alternaria",
                "niveau": niveau_oignon,
                "regle": "humectation_foliaire",
                "detail": {"heures_hr90_par_jour": h90_moy},
                "conseil": conseil_oignon,
            }
        )

    sources = [
        {"document": "NASA POWER Agroclimatology Archive (T2M, RH2M horaires)", "page": "Zone des Niayes"},
        {
            "document": "Critères de Hutton / Wallin (1962), modèle TOMCAST (Madden et al. 1978, UC IPM)",
            "page": "docs/sources/seuils-meteo-maladies-ravageurs.md",
        },
        {
            "document": "Modèles degrés-jours : Barrientos et al. (1998) ; Golizadeh et al. (2007) ; DPV Sénégal",
            "page": "docs/sources/seuils-meteo-maladies-ravageurs.md",
        },
    ]

    return {
        "statut": "ok",
        "alertes": alertes,
        "meteo": {
            "source": source_meteo,
            "date": date_eval.isoformat(),
            "periode": [debut_7j.isoformat(), date_eval.isoformat()],
        },
        "sources": sources,
    }
