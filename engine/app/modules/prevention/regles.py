"""Règles du module Prévention (D11), reprises de scripts/donnees/tester_modeles_prevention.py.

Seuils et sources : docs/sources/seuils-meteo-maladies-ravageurs.md.
- Mildiou, Hutton plafonné : 2 jours de suite avec Tmin ≥ 10 °C et ≥ 6 h à humidité ≥ 90 %,
  une heure humide ne comptant que si T ≤ 26,6 °C (borne haute de Wallin).
- Alternariose, TOMCAST : note quotidienne 0 à 4 (tableau UC IPM), alerte à partir de 15 points
  cumulés (Madden et al. 1978 ; fourchette 15-20).
- Mineuse de la tomate : seuil 8 °C, 440 degrés-jours par génération.
- Teigne du chou : seuil 7,3 °C, 290 degrés-jours par génération.
- Mildiou de l'oignon, DOWNCAST (Jesperson et Sutton 1987, critères repris par AUSVEG VG203/VG402 et
  Agronomy 10:738, 2020) : la veille, température moyenne de 8 h à 20 h < 24 °C ; nuit (20 h - 6 h) en
  moyenne entre 4 et 24 °C ; humidité > 95 % de 2 h à 6 h ; pas plus de 1 mm de pluie de 23 h à 4 h (la
  pluie lave les spores ; seuil chiffré de la version du Queensland, AUSVEG VG97024 p. 3 et VG402 p. 10-11).
- Noctuelle des fruits (Helicoverpa armigera) : seuil 10,7 °C, 521 degrés-jours par génération (43 + 287 +
  191, Jung et al. 2023, J. Econ. Entomol. 116:1689, laboratoire + validation en semi-champ, Corée).
- Alternariose de la carotte : TOMCAST, alerte à 15 points cumulés (Plant Disease 90:264, 2006, Michigan).
Aucune de ces règles n'est validée au Sénégal : on parle de « conditions favorables » et de
« surveiller », jamais de maladie déclarée.
"""

from __future__ import annotations

import datetime as dt

PLAFOND_MILDIOU = 26.6
TOMCAST = [((13, 18), (7, 16, 21, None)), ((18, 21), (4, 9, 16, 23)),
           ((21, 26), (3, 6, 13, 21)), ((26, 30), (4, 9, 16, 23))]
SEUIL_TOMCAST = 15
RAVAGEURS = {  # risque : (cultures, seuil °C, degrés-jours par génération)
    "tuta_absoluta": (("tomato",), 8.0, 440),
    "plutella_xylostella": (("cabbage",), 7.3, 290),
    "helicoverpa_armigera": (("tomato", "pepper", "chili", "bitter_eggplant"), 10.7, 521),
}
PLUIE_MAX_NUIT_MM = 1.0  # DOWNCAST, version du Queensland
GENERATION_SURVEILLER = 3  # « surveiller » à partir de la 3e génération depuis le repiquage


def note_tomcast(heures_humides: int, t_moy: float) -> int:
    for (bas, haut), seuils in TOMCAST:
        if bas <= t_moy < haut:
            return sum(1 for s in seuils if s is not None and heures_humides >= s)
    return 0


def resume_jours(horaire: dict[dt.date, list[tuple[float, float]]]) -> list[dict]:
    """Une ligne par jour complet (au moins 20 heures) avec ce qu'il faut pour les règles."""
    jours = []
    for jour in sorted(horaire):
        heures = horaire[jour]
        if len(heures) < 20:
            continue
        humides = [t for t, h in heures if h >= 90]
        jours.append({
            "date": jour,
            "tmin": min(t for t, _ in heures),
            "h90_frais": sum(1 for t in humides if t <= PLAFOND_MILDIOU),
            "dsv": note_tomcast(len(humides), sum(humides) / len(humides)) if humides else 0,
        })
    return jours


def jours_hutton(jours: list[dict]) -> list[dt.date]:
    """Jours où le critère Hutton plafonné est rempli (avec la veille)."""
    ok = lambda j: j["tmin"] >= 10 and j["h90_frais"] >= 6  # noqa: E731
    return [b["date"] for a, b in zip(jours, jours[1:])
            if ok(a) and ok(b) and (b["date"] - a["date"]).days == 1]


def generations(journalier: dict[dt.date, tuple[float, float]], seuil: float, dd_generation: float) -> float:
    """Générations bouclées depuis le premier jour de la série (méthode de la moyenne)."""
    dd = sum(max(0.0, (tmin + tmax) / 2 - seuil) for tmin, tmax in journalier.values())
    return dd / dd_generation


def jours_downcast(heures: dict[dt.datetime, tuple], ecartes_pluie: list | None = None) -> list[dt.date]:
    """Jours où les critères DOWNCAST de sporulation du mildiou de l'oignon sont remplis. Les nuits qui
    remplissaient tout sauf la pluie sont ajoutées à `ecartes_pluie` (transparence : pluie du modèle)."""
    par_jour: dict[dt.date, dict[int, tuple[float, float]]] = {}
    for moment, th in heures.items():
        par_jour.setdefault(moment.date(), {})[moment.hour] = th
    favorables = []
    for jour in sorted(par_jour):
        veille = par_jour.get(jour - dt.timedelta(days=1), {})
        aujourd = par_jour[jour]
        journee = [veille[h][0] for h in range(8, 20) if h in veille]
        nuit = [veille[h][0] for h in range(20, 24) if h in veille] + [aujourd[h][0] for h in range(0, 6) if h in aujourd]
        petit_matin = [aujourd[h][1] for h in range(2, 6) if h in aujourd]
        if len(journee) < 10 or len(nuit) < 8 or len(petit_matin) < 4:
            continue  # heures manquantes : on ne conclut pas
        if (sum(journee) / len(journee) < 24 and 4 <= sum(nuit) / len(nuit) <= 24
                and all(h > 95 for h in petit_matin)):
            pluie = sum(th[2] for th in ([veille[23]] if 23 in veille else []) + [aujourd[h] for h in range(0, 4) if h in aujourd]
                        if len(th) > 2)
            if pluie > PLUIE_MAX_NUIT_MM:
                if ecartes_pluie is not None:
                    ecartes_pluie.append(jour)
                continue
            favorables.append(jour)
    return favorables
