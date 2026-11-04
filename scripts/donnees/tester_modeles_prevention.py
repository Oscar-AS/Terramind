"""Fait tourner les règles du module Prévention sur la météo 2020-2025 des 4 points pilotes.

Usage (depuis la racine, après `telecharger_sources.py power`) :
    python3 -I scripts/donnees/tester_modeles_prevention.py

But : vérifier que le calendrier produit par chaque règle concorde avec les saisons
d'attaque documentées dans les Niayes (voir docs/sources/seuils-meteo-maladies-ravageurs.md).
Ce n'est pas une validation au champ : aucune donnée d'observation par parcelle n'existe.

Règles (sources dans le document des seuils) :
- Mildiou, critères Hutton : 2 jours de suite avec Tmin ≥ 10 °C et ≥ 6 h d'humidité ≥ 90 %.
- Alternariose, TOMCAST : note du jour 0 à 4 selon les heures d'humectation (estimées par
  humidité ≥ 90 %) et la température moyenne pendant ces heures (tableau UC IPM).
- Mineuse de la tomate : seuil 8 °C, 440 degrés-jours par génération (Barrientos et al. 1998,
  Krechemer et Foerster 2015 : 417 à 454).
- Teigne du chou : seuil 7,3 °C, 290 degrés-jours par génération (UC IPM : 283 à 293 au champ).
Degrés-jours par la méthode de la moyenne : max(0, (Tmax + Tmin) / 2 - seuil).

Sortie : data/extraits/prevention_calendrier_2020-2025.csv
"""

import csv
import io
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
POWER = RACINE / "data" / "raw" / "nasa_power"
SORTIE = RACINE / "data" / "extraits" / "prevention_calendrier_2020-2025.csv"
ANNEES = range(2020, 2026)

# TOMCAST : (borne basse incluse, borne haute exclue) -> heures minimales pour les notes 1, 2, 3, 4
TOMCAST = [((13, 18), (7, 16, 21, None)), ((18, 21), (4, 9, 16, 23)),
           ((21, 26), (3, 6, 13, 21)), ((26, 30), (4, 9, 16, 23))]
TUTA = (8.0, 440)
TEIGNE = (7.3, 290)


def lire(fichier):
    texte = fichier.read_text(encoding="utf-8")
    corps = texte.split("-END HEADER-", 1)[1].lstrip()
    for r in csv.DictReader(io.StringIO(corps)):
        t, h = float(r["T2M"]), float(r["RH2M"])
        if t <= -999 or h <= -999:
            continue
        yield (int(r["YEAR"]), int(r["MO"]), int(r["DY"])), t, h


def note_tomcast(heures, t_moy):
    for (bas, haut), seuils in TOMCAST:
        if bas <= t_moy < haut:
            return sum(1 for s in seuils if s is not None and heures >= s)
    return 0


def jours(point):
    j = defaultdict(lambda: {"t": [], "humide": []})
    for an in ANNEES:
        for date, t, h in lire(POWER / point / f"horaire_{an}.csv"):
            j[date]["t"].append(t)
            if h >= 90:
                j[date]["humide"].append(t)
    resultat = []
    for date in sorted(j):
        d = j[date]
        if len(d["t"]) < 20:  # journée incomplète
            continue
        tmin, tmax = min(d["t"]), max(d["t"])
        h90 = len(d["humide"])
        resultat.append({
            "date": date, "tmin": tmin, "tmax": tmax, "h90": h90,
            "dsv": note_tomcast(h90, sum(d["humide"]) / h90) if h90 else 0,
            "dd_tuta": max(0.0, (tmax + tmin) / 2 - TUTA[0]),
            "dd_teigne": max(0.0, (tmax + tmin) / 2 - TEIGNE[0]),
        })
    for veille, jour in zip(resultat, resultat[1:]):
        jour["hutton"] = all(x["tmin"] >= 10 and x["h90"] >= 6 for x in (veille, jour))
    resultat[0]["hutton"] = False
    return resultat


def main():
    points = sorted(p.name for p in POWER.iterdir() if p.is_dir())
    lignes = []
    for point in points:
        par_mois = defaultdict(list)
        for j in jours(point):
            par_mois[j["date"][1]].append(j)
        for mois in range(1, 13):
            js = par_mois[mois]
            n_ans = len({j["date"][0] for j in js})
            dd_tuta = sum(j["dd_tuta"] for j in js) / len(js)
            dd_teigne = sum(j["dd_teigne"] for j in js) / len(js)
            lignes.append([
                point, mois, n_ans,
                round(sum(j["hutton"] for j in js) / n_ans, 1),
                round(sum(j["dsv"] for j in js) / n_ans, 1),
                round(sum(j["h90"] for j in js) / len(js), 1),
                round(TUTA[1] / dd_tuta), round(TEIGNE[1] / dd_teigne),
            ])
    entete = ["point", "mois", "annees", "jours_hutton_par_mois", "notes_tomcast_par_mois",
              "heures_hr90_par_jour", "jours_par_generation_mineuse", "jours_par_generation_teigne"]
    with SORTIE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(entete)
        w.writerows(lignes)
    print(f"  ok  {SORTIE.relative_to(RACINE)}")
    noms = ["jan", "fév", "mar", "avr", "mai", "juin", "juil", "août", "sep", "oct", "nov", "déc"]
    for i, titre in ((3, "Jours Hutton (mildiou) par mois"), (4, "Notes TOMCAST (alternariose) par mois"),
                     (6, "Jours par génération, mineuse"), (7, "Jours par génération, teigne du chou")):
        print(f"\n{titre}")
        print(f"  {'':10}" + "".join(f"{m:>6}" for m in noms))
        for point in points:
            vals = [l[i] for l in lignes if l[0] == point]
            print(f"  {point:10}" + "".join(f"{v:>6}" for v in vals))


if __name__ == "__main__":
    main()
