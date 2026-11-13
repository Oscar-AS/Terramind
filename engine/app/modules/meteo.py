"""Météo NASA POWER (données publiques NASA, sans clé), lue au point demandé.

Horaire (T2M, RH2M) pour le mildiou et l'alternariose ; journalier (T2M_MAX, T2M_MIN)
pour les degrés-jours des ravageurs. NASA POWER publie avec quelques jours de retard :
la « semaine » analysée est donc la dernière semaine disponible, indiquée dans la réponse.
"""

from __future__ import annotations

import datetime as dt
import json
import urllib.request
from functools import lru_cache

POWER = "https://power.larc.nasa.gov/api/temporal/{pas}/point"
MANQUANT = -999.0


class MeteoIndisponible(RuntimeError):
    pass


def _lire(pas: str, parametres: str, lat: float, lon: float, debut: dt.date, fin: dt.date) -> dict:
    url = (f"{POWER.format(pas=pas)}?parameters={parametres}&community=AG"
           f"&latitude={lat}&longitude={lon}&start={debut:%Y%m%d}&end={fin:%Y%m%d}&format=JSON"
           + ("&time-standard=UTC" if pas == "hourly" else ""))
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())["properties"]["parameter"]
    except Exception as e:  # réseau, quota, format
        raise MeteoIndisponible(f"NASA POWER indisponible : {e}") from e


@lru_cache(maxsize=256)
def horaire(lat: float, lon: float, debut: dt.date, fin: dt.date) -> dict[dt.date, list[tuple[float, float]]]:
    """{jour: [(température °C, humidité %), …]} ; heures manquantes retirées."""
    p = _lire("hourly", "T2M,RH2M", lat, lon, debut, fin)
    jours: dict[dt.date, list[tuple[float, float]]] = {}
    for cle, t in p["T2M"].items():
        h = p["RH2M"].get(cle, MANQUANT)
        if t <= MANQUANT or h <= MANQUANT:
            continue
        jour = dt.datetime.strptime(cle[:8], "%Y%m%d").date()
        jours.setdefault(jour, []).append((t, h))
    return jours


@lru_cache(maxsize=256)
def journalier(lat: float, lon: float, debut: dt.date, fin: dt.date) -> dict[dt.date, tuple[float, float]]:
    """{jour: (Tmin, Tmax)} ; jours manquants retirés."""
    p = _lire("daily", "T2M_MIN,T2M_MAX", lat, lon, debut, fin)
    jours = {}
    for cle, tmin in p["T2M_MIN"].items():
        tmax = p["T2M_MAX"].get(cle, MANQUANT)
        if tmin <= MANQUANT or tmax <= MANQUANT:
            continue
        jours[dt.datetime.strptime(cle, "%Y%m%d").date()] = (tmin, tmax)
    return jours
