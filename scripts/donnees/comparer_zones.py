"""Compare les Niayes à d'autres zones dont on utilise les fiches techniques (climat ET sol).

Usage (depuis la racine du dépôt) :
    python3 -I scripts/donnees/comparer_zones.py

Pour chaque zone : climat moyen NASA POWER (climatologie) et sol iSDAsoil 0-20 cm (moyenne
d'un carré d'environ 630 m autour du point). Chaque écart est divisé par une « unité de
différence notable » (ÉCHELLES) puis moyenné : 0 = identique aux Niayes, 1 = en moyenne une
différence notable par critère. Résultat : data/extraits/zones_analogues_comparaison.csv.

Limite : la salinité n'est disponible dans aucune carte ouverte ; elle n'entre pas dans le calcul.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telecharger_sources as ts  # noqa: E402

# Points : zones de maraîchage connues (pas les centres-villes, souvent sans données de sol).
ZONES = {
    # Niayes (référence) : centroïdes des départements pilotes
    "Rufisque (Niayes)": (14.7593, -17.2054, "Niayes"),
    "Thiès (Niayes)": (14.7459, -16.8698, "Niayes"),
    "Tivaouane (Niayes)": (15.0884, -16.6518, "Niayes"),
    "Kébémer (Niayes)": (15.3042, -16.2611, "Niayes"),
    # Sénégal hors zone pilote
    "Gandiol (nord des Niayes, Saint-Louis)": (15.93, -16.47, "Sénégal"),
    "Podor (vallée du fleuve)": (16.65, -14.96, "Sénégal"),
    # Mauritanie : CNRADA (station de Kaédi, vallée) et littoral
    "Kaédi (station CNRADA, vallée)": (16.15, -13.50, "Mauritanie"),
    "Rosso (Trarza, vallée)": (16.51, -15.81, "Mauritanie"),
    "Nouakchott (maraîchage périurbain)": (18.03, -15.99, "Mauritanie"),
    # Niger : fiches des chambres régionales d'agriculture
    "Dosso (Niger)": (13.05, 3.19, "Niger"),
    "Maradi (Niger)": (13.50, 7.10, "Niger"),
}
REFERENCE = [n for n, (_, _, pays) in ZONES.items() if pays == "Niayes"]

SOL = {  # propriété iSDAsoil -> (nom court, échelle d'écart notable)
    "sand_content": ("sable_pct", 15),
    "clay_content": ("argile_pct", 10),
    "ph": ("ph", 0.5),
    "carbon_organic": ("carbone_org_g_kg", 3),
    "cation_exchange_capacity": ("cec_cmol_kg", 5),
}
CLIMAT = {  # nom court -> échelle
    "t_moy_annuelle_c": 2,
    "t_moy_saison_fraiche_c": 2,
    "hr_saison_fraiche_pct": 10,
    "pluie_annuelle_mm": 150,
}
FRAIS = ["NOV", "DEC", "JAN", "FEB", "MAR"]


def climat(lat, lon):
    url = (
        "https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=T2M,RH2M,PRECTOTCORR"
        f"&community=AG&latitude={lat}&longitude={lon}&format=JSON"
    )
    p = json.loads(ts.telecharger(url))["properties"]["parameter"]
    return {
        "t_moy_annuelle_c": round(p["T2M"]["ANN"], 1),
        "t_moy_saison_fraiche_c": round(sum(p["T2M"][m] for m in FRAIS) / 5, 1),
        "hr_saison_fraiche_pct": round(sum(p["RH2M"][m] for m in FRAIS) / 5, 1),
        "pluie_annuelle_mm": round(p["PRECTOTCORR"]["ANN"] * 365),
    }


def main():
    print("Climat (NASA POWER, climatologie)")
    valeurs = {n: climat(lat, lon) for n, (lat, lon, _) in ZONES.items()}
    print("Sol (iSDAsoil 0-20 cm, fenêtre d'environ 630 m)")
    legende = ts.telecharger(ts.ISDASOIL_TEXTURE_URL)
    points = {n: (lat, lon) for n, (lat, lon, _) in ZONES.items()}
    lignes = ts.isdasoil_points(points, list(SOL) + ["texture_class"], legende, fenetre=10)
    for prop, bande, nom, _lat, _lon, _brut, valeur, _unite, _regle in lignes:
        if bande == "mean_0_20":
            valeurs[nom]["texture" if prop == "texture_class" else SOL[prop][0]] = valeur

    criteres_sol = [c for c, _ in SOL.values()]
    echelles = {**CLIMAT, **{c: e for c, e in SOL.values()}}
    ref = {c: sum(valeurs[n][c] for n in REFERENCE) / len(REFERENCE) for c in echelles}

    def ecart(n, criteres):
        dispo = [c for c in criteres if valeurs[n].get(c) is not None]
        if not dispo:
            return None
        return round(sum(abs(valeurs[n][c] - ref[c]) / echelles[c] for c in dispo) / len(dispo), 2)

    sortie = ts.RACINE / "data" / "extraits" / "zones_analogues_comparaison.csv"
    entete = (
        ["zone", "pays", "latitude", "longitude"]
        + list(CLIMAT)
        + criteres_sol
        + ["texture", "ecart_climat", "ecart_sol", "ecart_total"]
    )
    rangs = []
    for n, (lat, lon, pays) in ZONES.items():
        ec, es = ecart(n, CLIMAT), ecart(n, criteres_sol)
        tot = None if ec is None or es is None else round((ec + es) / 2, 2)
        rangs.append(
            [n, pays, lat, lon]
            + [valeurs[n].get(c) for c in list(CLIMAT) + criteres_sol]
            + [valeurs[n].get("texture"), ec, es, tot]
        )
    rangs.append(
        ["Moyenne des 4 points Niayes (référence)", "Niayes", "", ""]
        + [round(ref[c], 1) for c in list(CLIMAT) + criteres_sol]
        + ["", 0, 0, 0]
    )
    with sortie.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(entete)
        w.writerows(rangs)
    print(f"  ok  {sortie.relative_to(ts.RACINE)}")
    for r in sorted(rangs[:-1], key=lambda r: (r[-1] is None, r[-1])):
        print(
            f"  {r[0]:42} climat {r[-3]}  sol {r[-2]}  total {r[-1]}  | sable {r[8]} argile {r[9]} "
            f"pH {r[10]} C {r[11]} CEC {r[12]} | {r[13]}"
        )


if __name__ == "__main__":
    main()
