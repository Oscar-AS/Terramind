"""Sol au point demandé, lu dans iSDAsoil (30 m, 0-20 cm, CC BY 4.0) sans compte.

Les cartes sont des GeoTIFF publics sur AWS : on ne télécharge que la tuile qui contient le
point (requêtes HTTP partielles). Code repris de scripts/donnees/telecharger_sources.py
(isdasoil_points), réduit aux propriétés utiles au plan. Valeur = moyenne d'un carré de
5 × 5 pixels (≈ 150 m) autour du point, plus stable qu'un pixel isolé.
Limite : iSDAsoil ne donne pas la salinité (on la demande à l'agriculteur).
"""

from __future__ import annotations

import csv
import io
import json
import math
import struct
import urllib.request
import zlib
from functools import lru_cache

ISDASOIL = "https://isdasoil.s3.amazonaws.com/soil_data/{p}/{p}.{ext}"
TEXTURES = "https://isdasoil.s3.amazonaws.com/soil_data/texture_class/texture_class_attribute_table.csv"
PROPRIETES = {"ph": "ph", "sand_content": "sable_pct", "clay_content": "argile_pct", "texture_class": "texture"}
FENETRE = 2


class SolIndisponible(RuntimeError):
    pass


def _get(url: str, debut: int | None = None, fin: int | None = None) -> bytes:
    req = urllib.request.Request(url)
    if debut is not None:
        req.add_header("Range", f"bytes={debut}-{fin}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _tags(entete: bytes) -> dict:
    """Premier IFD d'un BigTIFF petit-boutiste ; tableaux longs renvoyés comme (offset, nombre)."""
    if entete[:4] != b"II+\x00":
        raise SolIndisponible("BigTIFF attendu")
    tailles = {2: 1, 3: 2, 4: 4, 12: 8, 16: 8}
    formats = {3: "H", 4: "I", 12: "d", 16: "Q"}
    off = struct.unpack("<Q", entete[8:16])[0]
    n = struct.unpack("<Q", entete[off:off + 8])[0]
    tags = {}
    for i in range(n):
        e = entete[off + 8 + i * 20: off + 28 + i * 20]
        tag, typ, nb = struct.unpack("<HHQ", e[:12])
        taille = tailles.get(typ, 1) * nb
        if taille <= 8:
            brut = e[12:12 + taille]
        else:
            pos = struct.unpack("<Q", e[12:20])[0]
            if pos + taille > len(entete):
                tags[tag] = ("tableau", pos, nb)
                continue
            brut = entete[pos:pos + taille]
        tags[tag] = brut.decode("ascii", "ignore").strip("\x00 ") if typ == 2 else struct.unpack("<" + formats[typ] * nb, brut)
    return tags


@lru_cache(maxsize=8)
def _meta(prop: str) -> tuple[str, str, dict]:
    meta = json.loads(_get(ISDASOIL.format(p=prop, ext="json")))
    url = meta["assets"]["image"]["href"]
    return url, meta.get("back-transformation") or "", _tags(_get(url, 0, 65535))


@lru_cache(maxsize=1)
def _legende() -> dict[int, str]:
    texte = _get(TEXTURES).decode("utf-8-sig")
    return {int(r["Value"]): r["Description"] for r in csv.DictReader(io.StringIO(texte))}


def _valeur(prop: str, lat: float, lon: float):
    url, regle, t = _meta(prop)
    larg, tl, th, nb_bandes = t[256][0], t[322][0], t[323][0], t[277][0]
    bits, nodata = t[258][0], int(t[42113])
    pas, x0, y0 = t[33550][0], t[33922][3], t[33922][4]
    _, pos_off, _ = t[324]
    _, pos_nb, _ = t[325]
    fmt, octets = ("B", 1) if bits == 8 else ("H", 2)
    x = 6378137 * math.radians(lon)  # Web Mercator (EPSG:3857)
    y = 6378137 * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    col, lig = int((x - x0) / pas), int((y0 - y) / pas)
    k = (lig // th) * ((larg + tl - 1) // tl) + col // tl
    debut = struct.unpack("<Q", _get(url, pos_off + 8 * k, pos_off + 8 * k + 7))[0]
    taille = struct.unpack("<I", _get(url, pos_nb + 4 * k, pos_nb + 4 * k + 3))[0]
    tuile = zlib.decompress(_get(url, debut, debut + taille - 1))
    ly, lx = lig % th, col % tl
    bruts = [struct.unpack_from("<" + fmt, tuile, ((yy * tl + xx) * nb_bandes) * octets)[0]  # bande 0 = moyenne
             for yy in range(max(0, ly - FENETRE), min(th, ly + FENETRE + 1))
             for xx in range(max(0, lx - FENETRE), min(tl, lx + FENETRE + 1))]
    bruts = [b for b in bruts if b != nodata]
    if not bruts:
        return None
    if prop == "texture_class":
        return _legende()[max(set(bruts), key=bruts.count)]
    retro = {"x/10": lambda v: v / 10, "x/100": lambda v: v / 100, "": lambda v: v}[regle]
    return round(sum(retro(b) for b in bruts) / len(bruts), 1)


# Secours hors ligne (idée d'Oscar, branche ml/dataset-merge, b28a1e1) : valeurs iSDAsoil 0-20 cm déjà
# relevées aux 4 points pilotes des Niayes (data/raw/isdasoil/isdasoil_points_pilotes.csv, bande
# mean_0_20). Servent seulement si le serveur iSDAsoil ne répond pas et que le champ est à moins de
# RAYON_SECOURS_KM d'un point ; la source le dit. Au-delà, on préfère « indisponible » à une valeur fausse.
POINTS_PILOTES = {
    "Kébémer": (15.3042, -16.2611, {"ph": 6.9, "sable_pct": 83, "argile_pct": 11, "texture": "Sandy Loam"}),
    "Rufisque": (14.7593, -17.2054, {"ph": 6.8, "sable_pct": 59, "argile_pct": 22, "texture": "Sandy Clay Loam"}),
    "Thiès": (14.7459, -16.8698, {"ph": 6.3, "sable_pct": 72, "argile_pct": 17, "texture": "Sandy Loam"}),
    "Tivaouane": (15.0884, -16.6518, {"ph": 6.4, "sable_pct": 76, "argile_pct": 12, "texture": "Sandy Loam"}),
}
RAYON_SECOURS_KM = 5.0


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def sol_secours(lat: float, lon: float) -> dict | None:
    """Valeurs du point pilote le plus proche s'il est à moins de RAYON_SECOURS_KM, sinon None."""
    dist, nom, valeurs = min((_distance_km(lat, lon, la, lo), nom, v) for nom, (la, lo, v) in POINTS_PILOTES.items())
    if dist > RAYON_SECOURS_KM:
        return None
    return {**valeurs, "source": f"iSDAsoil 30 m, 0-20 cm, relevé au point pilote de {nom} "
                                 f"(à {nombre_km(dist)} km ; serveur iSDAsoil injoignable)"}


def nombre_km(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def sol(lat: float, lon: float) -> dict:
    """{texture, sable_pct, argile_pct, ph, source} ; lat/lon arrondis à 0,01° par l'appelant."""
    try:
        return _sol_en_ligne(lat, lon)
    except SolIndisponible as e:
        secours = sol_secours(lat, lon)
        if secours is None or "pas de donnée" in str(e):
            raise
        return secours


@lru_cache(maxsize=512)
def _sol_en_ligne(lat: float, lon: float) -> dict:
    try:
        resultat = {nom: _valeur(prop, lat, lon) for prop, nom in PROPRIETES.items()}
    except SolIndisponible:
        raise
    except Exception as e:
        raise SolIndisponible(f"iSDAsoil indisponible : {e}") from e
    if all(v is None for v in resultat.values()):
        raise SolIndisponible("pas de donnée de sol à ce point (mer, ville ?)")
    resultat["source"] = "iSDAsoil 30 m, 0-20 cm (moyenne sur environ 150 m)"
    return resultat
