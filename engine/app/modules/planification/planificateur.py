"""Module Planification : propriétés du sol (iSDAsoil 30 m) et recommandation de cultures.

Conformément aux décisions D3, D6 et D7 (docs/decisions.md) et au contrat d'API (docs/api.md § 3) :
- La position GPS est arrondie à 0,01° (~1 km) par respect de la vie privée.
- Les données de sol proviennent d'iSDAsoil (30 m, 0-20 cm) aux points pilotes des Niayes.
- Les règles agronomiques viennent de content/regles_sol_culture.csv (Guide ISRA 1987, PADEN, PIESAN, FAO).
- Aucun rendement chiffré n'est promis à l'agriculteur ; aucun produit chimique ni dose n'est prescrit.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
from pathlib import Path

RACINE = Path(__file__).resolve().parents[4]
ISDASOIL_CSV = RACINE / "data" / "raw" / "isdasoil" / "isdasoil_points_pilotes.csv"
REGLES_CSV = RACINE / "content" / "regles_sol_culture.csv"

SOURCE_SOL = "iSDAsoil 30 m, 0-20 cm"
DATE_SOL = "2026-11-02"

# Boîte englobante approximative du Sénégal continental (WGS84)
LAT_MIN_SENEGAL, LAT_MAX_SENEGAL = 12.2, 16.8
LON_MIN_SENEGAL, LON_MAX_SENEGAL = -17.6, -11.3
RAYON_MAX_ZONE_PILOTE_KM = 120.0

TEXTURE_FR = {
    "Sand": "sableux",
    "Loamy Sand": "sablo-limoneux léger",
    "Sandy Loam": "sablo-limoneux",
    "Sandy Clay Loam": "sablo-argileux",
    "Loam": "limoneux",
    "Clay Loam": "argilo-limoneux",
}


class HorsZoneError(ValueError):
    """Position GPS hors de la zone pilote couverte par les données de sol."""


def arrondir_gps(lat: float, lon: float) -> tuple[float, float]:
    """Arrondit les coordonnées GPS à 0,01° (~1 km) avant tout traitement ou journalisation."""
    return round(float(lat), 2), round(float(lon), 2)


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique (Haversine) en kilomètres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _charger_points_isdasoil() -> dict[str, dict]:
    """Charge les propriétés 0-20 cm des points pilotes depuis isdasoil_points_pilotes.csv."""
    points: dict[str, dict] = {}
    with ISDASOIL_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["bande"] != "mean_0_20":
                continue
            dep = row["departement"]
            p = points.setdefault(
                dep,
                {
                    "departement": dep,
                    "lat": float(row["latitude"]),
                    "lon": float(row["longitude"]),
                },
            )
            prop = row["propriete"]
            val = row["valeur"]
            if prop == "ph":
                p["ph"] = float(val)
            elif prop == "sand_content":
                p["sable_pct"] = int(round(float(val)))
            elif prop == "clay_content":
                p["argile_pct"] = int(round(float(val)))
            elif prop == "silt_content":
                p["limon_pct"] = int(round(float(val)))
            elif prop == "texture_class":
                p["texture"] = val
            elif prop == "carbon_organic":
                p["carbone_org_g_kg"] = round(float(val), 2)
    return points


def sol(lat: float, lon: float) -> dict:
    """Renvoie la texture, le % de sable, le % d'argile et le pH (0-20 cm) pour un point GPS.

    Lève HorsZoneError si le point est hors du Sénégal ou à plus de 120 km des points pilotes.
    """
    lat_arr, lon_arr = arrondir_gps(lat, lon)
    if not (LAT_MIN_SENEGAL <= lat_arr <= LAT_MAX_SENEGAL and LON_MIN_SENEGAL <= lon_arr <= LON_MAX_SENEGAL):
        raise HorsZoneError(
            f"Position ({lat_arr}, {lon_arr}) hors du Sénégal : seules les parcelles sénégalaises sont couvertes."
        )

    points = _charger_points_isdasoil()
    distances = [
        (_distance_km(lat_arr, lon_arr, p["lat"], p["lon"]), dep, p)
        for dep, p in points.items()
    ]
    distances.sort(key=lambda x: x[0])
    dist_min, dep_proche, p_proche = distances[0]

    if dist_min > RAYON_MAX_ZONE_PILOTE_KM:
        raise HorsZoneError(
            f"Position ({lat_arr}, {lon_arr}) à {dist_min:.0f} km des Niayes : "
            "seule la zone pilote (Rufisque, Thiès, Tivaouane, Kébémer) est couverte pour l'instant."
        )

    # Si on est très proche d'un centroïde (< 15 km), on renvoie directement la mesure exacte du point pilote.
    # Sinon, interpolation par inverse de la distance (IDW) pour les valeurs continues, et texture du plus proche.
    if dist_min <= 15.0:
        sable = p_proche["sable_pct"]
        argile = p_proche["argile_pct"]
        ph_val = round(p_proche["ph"], 1)
    else:
        poids = [(1.0 / max(d, 0.1) ** 2, p) for d, _, p in distances]
        somme_poids = sum(w for w, _ in poids)
        sable = int(round(sum(w * p["sable_pct"] for w, p in poids) / somme_poids))
        argile = int(round(sum(w * p["argile_pct"] for w, p in poids) / somme_poids))
        ph_val = round(sum(w * p["ph"] for w, p in poids) / somme_poids, 1)

    return {
        "texture": p_proche["texture"],
        "sable_pct": sable,
        "argile_pct": argile,
        "ph": ph_val,
        "source": SOURCE_SOL,
        "date": DATE_SOL,
        "departement_proche": dep_proche,
        "distance_point_pilote_km": round(dist_min, 1),
    }


def _charger_regles() -> list[dict]:
    with REGLES_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _evaluer_culture(
    regle: dict,
    infos_sol: dict,
    mois: int,
    eau_puits_salee: str,
    champ_en_bas_fond: str,
) -> dict:
    """Évalue l'adaptation d'une culture selon la saison, le sol, la salinité et le bas-fond."""
    raisons: list[str] = []
    avertissements: list[str] = []

    mois_opt = {int(m) for m in regle["mois_optimaux"].split(";") if m.strip()}
    mois_pos = {int(m) for m in regle["mois_possibles"].split(";") if m.strip()}
    textures_ok = {t.strip() for t in regle["texture_sol"].split(",") if t.strip()}
    ph_min = float(regle["ph_min"])
    ph_max = float(regle["ph_max"])

    texture = infos_sol["texture"]
    texture_nom_fr = TEXTURE_FR.get(texture, texture.lower())
    ph = infos_sol["ph"]

    # 1. Saison
    if mois in mois_opt:
        statut_saison = "optimale"
        if mois in (11, 12, 1, 2):
            raisons.append("saison sèche et fraîche idéale")
        else:
            raisons.append("période favorable de semis")
    elif mois in mois_pos:
        statut_saison = "possible"
        raisons.append("semis possible à cette période avec une variété adaptée")
        if mois in (6, 7, 8, 9):
            avertissements.append("hivernage : choisir une variété tolérante à la chaleur et à l'humidité")
    else:
        statut_saison = "hors_saison"
        avertissements.append(f"hors période de semis recommandée ({regle['saison_semis']})")

    # 2. Texture du sol
    sol_ok = texture in textures_ok
    if sol_ok:
        raisons.append(f"sol {texture_nom_fr} adapté")
    else:
        avertissements.append(
            f"sol {texture_nom_fr} moins habituel pour cette culture (idéal : {', '.join(textures_ok)})"
        )

    # 3. pH du sol
    ph_ok = ph_min <= ph <= ph_max
    if ph_ok:
        raisons.append(f"pH {ph} dans la plage recommandée ({ph_min}–{ph_max})")
    elif ph_min - 0.3 <= ph <= ph_max + 0.3:
        raisons.append(f"pH {ph} proche de la plage recommandée ({ph_min}–{ph_max})")
        avertissements.append(f"pH {ph} légèrement en bordure de l'optimum ({ph_min}–{ph_max})")
        ph_ok = True
    else:
        avertissements.append(f"pH {ph} hors de la plage recommandée ({ph_min}–{ph_max})")

    # 4. Détermination initiale de l'adaptation
    if statut_saison == "hors_saison" or not ph_ok:
        adaptation = "deconseillee"
    elif statut_saison == "optimale" and sol_ok:
        adaptation = "conseillee"
    else:
        adaptation = "possible"

    # 5. Règle salinité (Guide ISRA 1987, stratégie § 8)
    sensibilite_sel = regle["sensibilite_sel"]
    if sensibilite_sel == "tres_sensible":
        if eau_puits_salee == "oui":
            adaptation = "deconseillee"
            avertissements.append(
                "très sensible au sel : déconseillée car l'eau du puits est déclarée salée (Guide ISRA 1987)"
            )
        else:
            avertissements.append("très sensible au sel : à éviter si l'eau du puits est salée")
    elif sensibilite_sel == "moderee" and eau_puits_salee == "oui":
        if adaptation == "conseillee":
            adaptation = "possible"
        avertissements.append("sensibilité modérée au sel : surveiller le bord des feuilles en cas d'eau salée")

    # 6. Règle bas-fond (recensement DHORT 2012 : 44 % des sites en bas-fonds)
    if regle["craint_bas_fond"] == "oui" and champ_en_bas_fond == "oui":
        if adaptation == "conseillee":
            adaptation = "possible"
        avertissements.append(
            "champ en bas-fond : craint les sols gorgés d'eau (risque de pourriture ; billonner et drainer)"
        )

    # Conseil spécifique oignon issu du livret PIESAN
    if regle["culture"] == "onion":
        avertissements.append("ne jamais utiliser d'urée en culture d'oignon (Livret PIESAN p. 17)")

    return {
        "culture": regle["culture"],
        "libelle": regle["libelle_fr"],
        "adaptation": adaptation,
        "periode_semis": regle["saison_semis"],
        "cycle_jours": [int(regle["cycle_min_j"]), int(regle["cycle_max_j"])],
        "raisons": raisons,
        "avertissements": avertissements,
    }


def planifier(
    lat: float,
    lon: float,
    date: str | dt.date | None = None,
    eau_puits_salee: str = "ne_sait_pas",
    champ_en_bas_fond: str = "ne_sait_pas",
) -> dict:
    """Calcule le profil de sol et la liste triée des cultures maraîchères pour POST /v1/plan."""
    if date is None:
        date_obj = dt.date.today()
    elif isinstance(date, dt.date):
        date_obj = date
    else:
        date_obj = dt.date.fromisoformat(str(date))

    eau_puits_salee = (eau_puits_salee or "ne_sait_pas").strip().lower()
    champ_en_bas_fond = (champ_en_bas_fond or "ne_sait_pas").strip().lower()
    if eau_puits_salee not in ("oui", "non", "ne_sait_pas"):
        raise ValueError("eau_puits_salee doit valoir 'oui', 'non' ou 'ne_sait_pas'")
    if champ_en_bas_fond not in ("oui", "non", "ne_sait_pas"):
        raise ValueError("champ_en_bas_fond doit valoir 'oui', 'non' ou 'ne_sait_pas'")

    infos_sol = sol(lat, lon)
    regles = _charger_regles()

    ordre_adaptation = {"conseillee": 0, "possible": 1, "deconseillee": 2}
    cultures_eval = [
        _evaluer_culture(r, infos_sol, date_obj.month, eau_puits_salee, champ_en_bas_fond)
        for r in regles
    ]
    cultures_eval.sort(key=lambda c: (ordre_adaptation[c["adaptation"]], -len(c["raisons"])))

    sources = [
        {"document": "iSDAsoil Africa 30 m (couche 0-20 cm)", "page": "Points pilotes Niayes"},
        {"document": "Guide pratique du maraîchage au Sénégal (ISRA / CDH, 1987)", "page": "79-141"},
        {"document": "Livrets techniques PADEN (chou, pomme de terre, 2014-2016) et PIESAN (oignon, 2022)", "page": "3-29"},
    ]

    return {
        "sol": {
            "texture": infos_sol["texture"],
            "sable_pct": infos_sol["sable_pct"],
            "argile_pct": infos_sol["argile_pct"],
            "ph": infos_sol["ph"],
            "source": infos_sol["source"],
            "date": infos_sol["date"],
            "departement_proche": infos_sol["departement_proche"],
        },
        "cultures": cultures_eval,
        "sources": sources,
    }
