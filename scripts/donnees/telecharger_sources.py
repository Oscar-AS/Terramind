"""Télécharge les jeux de données publics du projet dans data/raw/.

Usage (depuis la racine du dépôt) :
    python3 scripts/donnees/telecharger_sources.py            # toutes les sources
    python3 scripts/donnees/telecharger_sources.py power faostat

Sources : geoboundaries, power, soilgrids, isdasoil, faostat, wfp, chirps, documents.
Bibliothèque standard uniquement, sauf la source chirps qui a besoin de
Pillow (décodage des tuiles GeoTIFF). Chaque fichier écrit est ajouté à
data/raw/MANIFESTE.csv (source, URL, date, taille, SHA-256).
Les fichiers bruts ne sont jamais modifiés après téléchargement ; les
extraits (FAOSTAT) sont signalés comme tels dans le manifeste.
"""

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import struct
import sys
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
RAW = RACINE / "data" / "raw"
MANIFESTE = RAW / "MANIFESTE.csv"

# Départements pilotes (zone des Niayes et Rufisque). Les coordonnées ne sont
# pas saisies à la main : ce sont les centroïdes calculés à partir des limites
# geoBoundaries (voir points_pilotes()).
DEPARTEMENTS_PILOTES = ["Rufisque", "Thies", "Tivaoune", "Kebemer"]

GEOBOUNDARIES_API = "https://www.geoboundaries.org/api/current/gbOpen/SEN/{niveau}/"
POWER_HORAIRE = (
    "https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,PRECTOTCORR,WS2M"
    "&community=AG&longitude={lon}&latitude={lat}&start={debut}&end={fin}&format=CSV&time-standard=UTC"
)
POWER_JOURNALIER = (
    "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,RH2M,PRECTOTCORR"
    "&community=AG&longitude={lon}&latitude={lat}&start={debut}&end={fin}&format=CSV"
)
SOILGRIDS = (
    "https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}"
    "&property=phh2o&property=clay&property=sand&property=silt&property=soc&property=cec&property=nitrogen"
    "&depth=0-5cm&depth=5-15cm&depth=15-30cm&value=mean&value=Q0.05&value=Q0.95"
)
ISDASOIL = "https://isdasoil.s3.amazonaws.com/soil_data/{p}/{p}.{ext}"
# Toutes les couches de sol iSDAsoil sauf « fcc » (classification de fertilité au codage particulier).
ISDASOIL_PROPRIETES = [
    "ph", "sand_content", "silt_content", "clay_content", "texture_class", "carbon_organic", "carbon_total",
    "nitrogen_total", "phosphorous_extractable", "potassium_extractable", "calcium_extractable",
    "magnesium_extractable", "sulphur_extractable", "zinc_extractable", "iron_extractable",
    "aluminium_extractable", "cation_exchange_capacity", "bulk_density", "stone_content", "bedrock_depth",
]
FAOSTAT_ZIP = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_Africa.zip"
WFP_PAQUET = "https://data.humdata.org/api/3/action/package_show?id=wfp-food-prices-for-senegal"

# CHIRPS v3, pentades (totaux sur 5 jours ; le produit journalier n'est qu'une
# redistribution des pentades, déconseillée par le Climate Hazards Center).
CHIRPS_COG = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/pentads/global/cogs/chirps-v3.0.{a}.{m:02d}.{p}.cog"
ANNEES_CHIRPS = range(1991, 2026)

# Rapports publics (ANSD, DAPSA via ANADS, ministère de l'Agriculture) dont on
# extrait des tableaux avec scripts/donnees/extraire_rapports.py.
DOCUMENTS = [
    ("ansd_rgph5_ch10_agriculture_def.pdf",
     "https://www.ansd.sn/sites/default/files/recensements/rapport/Chapitre-10_AGRICULTURE-Rapport-def-RGPH-5.pdf",
     "ANSD, RGPH-5 (2023), chapitre 10 Agriculture, rapport définitif"),
    ("ansd_ses_2019_agriculture.pdf",
     "https://www.ansd.sn/sites/default/files/2022-12/8-SES-2019_Agriculture.pdf",
     "ANSD, Situation économique et sociale 2019, chapitre Agriculture"),
    ("ansd_bulletin_oct_2023.pdf",
     "https://www.ansd.sn/sites/default/files/2024-01/BULLETIN_OCT_2023.pdf",
     "ANSD, bulletin mensuel des statistiques économiques, octobre 2023"),
    ("dapsa_eaa_2020-2021_rapport.pdf", "https://anads.ansd.sn/index.php/catalog/241/download/2099",
     "DAPSA, rapport de l'Enquête agricole annuelle 2020-2021 (documents ANADS)"),
    ("dapsa_eaa_2020-2021_tableaux_annexes.xlsx", "https://anads.ansd.sn/index.php/catalog/241/download/2100",
     "DAPSA, tableaux annexes du rapport EAA 2020-2021 (documents ANADS)"),
    ("dapsa_eaa_2022-2023_rapport.pdf", "https://anads.ansd.sn/index.php/catalog/290/download/2586",
     "DAPSA, rapport de l'Enquête agricole annuelle 2022-2023 (documents ANADS)"),
    ("dapsa_eaa_2022-2023_tableaux.xlsx", "https://anads.ansd.sn/index.php/catalog/290/download/2611",
     "DAPSA, plan de tabulation EAA 2022-2023 (documents ANADS)"),
    ("dapsa_eaa_2017-2022_superficie_rendement_production.xlsx", "https://anads.ansd.sn/index.php/catalog/290/download/2594",
     "DAPSA, EAA 2017-2022, tableau T3 superficie, rendement et production (documents ANADS)"),
    ("masae_forum_horticulture_2025.pdf",
     "https://agriculture.gouv.sn/wp-content/uploads/2025/07/Forum-National-de-Lhorticulture.pdf",
     "Ministère de l'Agriculture, Forum national de l'horticulture, 2025"),
]

ANNEES_HORAIRES = range(2020, 2026)  # années civiles complètes
JOURNALIER = ("19910101", "20251231")


def telecharger(url, essais=3, delai=10, timeout=180):
    """Renvoie le contenu (bytes) ou lève l'erreur après plusieurs essais."""
    derniere = None
    for i in range(essais):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            derniere = e
            time.sleep(delai * (i + 1))
    raise derniere


def ecrire(chemin, contenu, source, url, note=""):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(contenu)
    nouveau = not MANIFESTE.exists()
    with MANIFESTE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nouveau:
            w.writerow(["fichier", "source", "url", "telecharge_le_utc", "octets", "sha256", "note"])
        w.writerow([
            chemin.relative_to(RAW).as_posix(), source, url,
            dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            len(contenu), hashlib.sha256(contenu).hexdigest(), note,
        ])
    print(f"  ok  {chemin.relative_to(RACINE)} ({len(contenu) // 1024} Ko)")


def centroide(geometrie):
    """Centroïde surfacique (lat, lon) du contour extérieur, pondéré par l'aire."""
    polygones = geometrie["coordinates"] if geometrie["type"] == "MultiPolygon" else [geometrie["coordinates"]]
    aire_tot = sx = sy = 0.0
    for poly in polygones:
        anneau = poly[0]
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(anneau, anneau[1:] + anneau[:1]):
            c = x0 * y1 - x1 * y0
            a += c
            cx += (x0 + x1) * c
            cy += (y0 + y1) * c
        a /= 2
        aire_tot += abs(a)
        sx += cx / (6 * a) * abs(a)
        sy += cy / (6 * a) * abs(a)
    return round(sy / aire_tot, 4), round(sx / aire_tot, 4)


def points_pilotes():
    chemin = RAW / "geoboundaries" / "geoBoundaries-SEN-ADM2_simplified.geojson"
    if not chemin.exists():
        geoboundaries()
    g = json.loads(chemin.read_text(encoding="utf-8"))
    points = {}
    for f in g["features"]:
        nom = f["properties"]["shapeName"]
        if nom in DEPARTEMENTS_PILOTES:
            points[nom] = centroide(f["geometry"])
    manquants = set(DEPARTEMENTS_PILOTES) - set(points)
    if manquants:
        raise SystemExit(f"Départements absents de geoBoundaries : {manquants}")
    return points


def geoboundaries():
    print("geoBoundaries (limites administratives, CC BY 3.0 IGO)")
    for niveau in ("ADM1", "ADM2"):
        meta_url = GEOBOUNDARIES_API.format(niveau=niveau)
        meta = telecharger(meta_url)
        ecrire(RAW / "geoboundaries" / f"meta_SEN_{niveau}.json", meta, "geoBoundaries", meta_url)
        url = json.loads(meta)["simplifiedGeometryGeoJSON"]
        ecrire(RAW / "geoboundaries" / f"geoBoundaries-SEN-{niveau}_simplified.geojson",
               telecharger(url), "geoBoundaries", url)


def power():
    print("NASA POWER (météo, données publiques NASA)")
    for nom, (lat, lon) in points_pilotes().items():
        dossier = RAW / "nasa_power" / nom.lower()
        url = POWER_JOURNALIER.format(lat=lat, lon=lon, debut=JOURNALIER[0], fin=JOURNALIER[1])
        ecrire(dossier / f"journalier_{JOURNALIER[0][:4]}-{JOURNALIER[1][:4]}.csv", telecharger(url),
               "NASA POWER", url, f"centroïde {nom} ({lat}, {lon})")
        for annee in ANNEES_HORAIRES:
            url = POWER_HORAIRE.format(lat=lat, lon=lon, debut=f"{annee}0101", fin=f"{annee}1231")
            ecrire(dossier / f"horaire_{annee}.csv", telecharger(url), "NASA POWER", url,
                   f"centroïde {nom} ({lat}, {lon}), heures UTC")


def soilgrids():
    print("SoilGrids 2.0 (sols, CC BY 4.0)")
    for nom, (lat, lon) in points_pilotes().items():
        url = SOILGRIDS.format(lat=lat, lon=lon)
        try:
            contenu = telecharger(url, essais=4, delai=20)
        except Exception as e:  # le service est souvent indisponible
            print(f"  ÉCHEC {nom} : {e}. À relancer plus tard : python3 {Path(__file__).name} soilgrids")
            continue
        ecrire(RAW / "soilgrids" / f"{nom.lower()}.json", contenu, "SoilGrids 2.0 (ISRIC)", url,
               f"centroïde {nom} ({lat}, {lon}), résolution 250 m")


def _bigtiff_tags(entete):
    """Premier IFD d'un BigTIFF petit-boutiste ; les tableaux trop longs sont renvoyés comme (offset, nombre)."""
    if entete[:4] != b"II+\x00":
        raise ValueError("BigTIFF attendu")
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


def _retransformer(regle, x):
    if regle in (None, ""):
        return x
    if regle == "x/10":
        return x / 10
    if regle == "x/100":
        return x / 100
    if regle == "expm1(x/10)":
        return math.expm1(x / 10)
    raise ValueError(f"règle de retransformation inconnue : {regle}")


def isdasoil():
    """Valeurs iSDAsoil (30 m) aux points pilotes, lues dans les COG publics d'AWS sans compte.
    Seule la tuile contenant chaque point est téléchargée (requêtes HTTP partielles)."""
    print("iSDAsoil (sols à 30 m, CC BY 4.0), lecture des tuiles utiles sur AWS")
    points = points_pilotes()
    lignes = []
    for prop in ISDASOIL_PROPRIETES:
        meta_url = ISDASOIL.format(p=prop, ext="json")
        meta_brut = telecharger(meta_url)
        ecrire(RAW / "isdasoil" / "metadonnees" / f"{prop}.json", meta_brut, "iSDAsoil (iSDA)", meta_url)
        meta = json.loads(meta_brut)
        regle, unite = meta.get("back-transformation"), meta.get("unit") or ""
        bandes = [b["name"] for b in meta["assets"]["image"]["eo:bands"]]
        url = meta["assets"]["image"]["href"]
        t = _bigtiff_tags(_plage(url, 0, 65535))
        larg, tl, th, nb_bandes = t[256][0], t[322][0], t[323][0], t[277][0]
        bits, nodata = t[258][0], int(t[42113])
        if t[259][0] != 8 or t[284][0] != 1 or t[317][0] != 1 or nb_bandes != len(bandes) or bits not in (8, 16):
            raise ValueError(f"{prop} : structure de fichier inattendue")
        pas, x0, y0 = t[33550][0], t[33922][3], t[33922][4]
        _, pos_off, _ = t[324]
        _, pos_nb, _ = t[325]
        fmt, octets = ("B", 1) if bits == 8 else ("H", 2)
        tuiles = {}
        for nom, (lat, lon) in points.items():
            # Projection Web Mercator (EPSG:3857), celle des fichiers iSDAsoil.
            x = 6378137 * math.radians(lon)
            y = 6378137 * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
            col, lig = int((x - x0) / pas), int((y0 - y) / pas)
            k = (lig // th) * ((larg + tl - 1) // tl) + col // tl
            if k not in tuiles:
                debut = struct.unpack("<Q", _plage(url, pos_off + 8 * k, pos_off + 8 * k + 7))[0]
                taille = struct.unpack("<I", _plage(url, pos_nb + 4 * k, pos_nb + 4 * k + 3))[0]
                tuiles[k] = zlib.decompress(_plage(url, debut, debut + taille - 1))
            px = ((lig % th) * tl + col % tl) * nb_bandes
            for i, bande in enumerate(bandes):
                brut = struct.unpack_from("<" + fmt, tuiles[k], (px + i) * octets)[0]
                if brut == nodata:
                    valeur = None
                elif bande.startswith("mean"):
                    valeur = round(_retransformer(regle, brut), 3)
                else:
                    valeur = None  # écart type : retransformation non documentée pour les échelles log
                lignes.append([prop, bande, nom, lat, lon, brut, valeur, unite, regle or ""])
        print(f"  {prop} : {len(tuiles)} tuile(s)")
    sortie = io.StringIO()
    w = csv.writer(sortie)
    w.writerow(["propriete", "bande", "departement", "latitude", "longitude", "valeur_brute", "valeur",
                "unite", "retransformation"])
    w.writerows(lignes)
    ecrire(RAW / "isdasoil" / "isdasoil_points_pilotes.csv", sortie.getvalue().encode("utf-8"),
           "iSDAsoil (iSDA), COG publics sur AWS", ISDASOIL.format(p="PROPRIETE", ext="tif"),
           "EXTRAIT : pixel de 30 m sous chaque centroïde ; valeur = moyenne retransformée selon les métadonnées ; "
           "écarts types laissés bruts ; texture_class = code brut (légende à trouver)")


def faostat():
    print("FAOSTAT, production végétale (extrait Sénégal, CC BY 4.0)")
    archive = telecharger(FAOSTAT_ZIP)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        # Fichier « large » (une colonne par année, avec indicateurs de qualité F/N).
        nom_csv = next(n for n in z.namelist() if n.endswith("_E_Africa.csv"))
        lignes = io.TextIOWrapper(z.open(nom_csv), encoding="utf-8")
        lecteur = csv.reader(lignes)
        entete = next(lecteur)
        i_zone = entete.index("Area")
        sortie = io.StringIO()
        w = csv.writer(sortie)
        w.writerow(entete)
        n = 0
        for ligne in lecteur:
            if ligne[i_zone] == "Senegal":
                w.writerow(ligne)
                n += 1
    ecrire(RAW / "faostat" / "faostat_qcl_senegal_extrait.csv", sortie.getvalue().encode("utf-8"),
           "FAOSTAT QCL", FAOSTAT_ZIP,
           f"EXTRAIT : lignes Area == Senegal de {nom_csv} ({n} lignes), valeurs non modifiées")


def wfp():
    print("PAM / HDX, prix des marchés (CC BY-IGO)")
    paquet = json.loads(telecharger(WFP_PAQUET))["result"]
    for res in paquet["resources"]:
        if res["format"].upper() == "CSV":
            nom = res["url"].rsplit("/", 1)[-1]
            ecrire(RAW / "wfp_prix" / nom, telecharger(res["url"]), "PAM (WFP) via HDX", res["url"],
                   f"jeu « {paquet['title']} », source : {paquet.get('dataset_source', '')}")


def _plage(url, debut, fin, essais=4):
    for i in range(essais):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={debut}-{fin}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError):
            if i == essais - 1:
                raise
            time.sleep(5 * (i + 1))


def _tags_tiff(entete):
    """Lit le premier IFD d'un TIFF classique petit-boutiste (cas des COG CHIRPS)."""
    if entete[:4] != b"II*\x00":
        raise ValueError("format TIFF inattendu")
    tailles = {2: 1, 3: 2, 4: 4, 12: 8}
    formats = {3: "H", 4: "I", 12: "d"}
    off = struct.unpack("<I", entete[4:8])[0]
    n = struct.unpack("<H", entete[off:off + 2])[0]
    tags = {}
    for i in range(n):
        e = entete[off + 2 + i * 12: off + 14 + i * 12]
        tag, typ, nb = struct.unpack("<HHI", e[:8])
        if typ not in formats:
            continue
        taille = tailles[typ] * nb
        brut = e[8:8 + taille] if taille <= 4 else entete[struct.unpack("<I", e[8:12])[0]:][:taille]
        tags[tag] = struct.unpack("<" + formats[typ] * nb, brut)
    return tags


def _valeurs_cog(url, points):
    """Valeur du pixel CHIRPS sous chaque point, en ne téléchargeant que les tuiles utiles."""
    from PIL import Image  # seule dépendance hors bibliothèque standard

    t = _tags_tiff(_plage(url, 0, 65535))
    larg, tl, th = t[256][0], t[322][0], t[323][0]
    if t[259][0] != 5 or t[339][0] != 3:
        raise ValueError("compression ou type de données inattendus")
    pas_x, pas_y = t[33550][0], t[33550][1]
    x0, y0 = t[33922][3], t[33922][4]
    tuiles, resultats = {}, {}
    for nom, (lat, lon) in points.items():
        col, lig = int((lon - x0) / pas_x), int((y0 - lat) / pas_y)
        k = (lig // th) * ((larg + tl - 1) // tl) + col // tl
        if k not in tuiles:
            comp = _plage(url, t[324][k], t[324][k] + t[325][k] - 1)
            # Petit TIFF d'une seule tuile, décodé par Pillow (LZW, flottant 32 bits).
            entrees = [(256, 3, tl), (257, 3, th), (258, 3, 32), (259, 3, 5), (262, 3, 1), (273, 4, 0),
                       (277, 3, 1), (278, 3, th), (279, 4, len(comp)), (339, 3, 3)]
            debut_donnees = 10 + len(entrees) * 12 + 4
            b = io.BytesIO()
            b.write(b"II*\x00" + struct.pack("<IH", 8, len(entrees)))
            for tag, typ, val in entrees:
                val = debut_donnees if tag == 273 else val
                b.write(struct.pack("<HHI", tag, typ, 1) + (struct.pack("<HH", val, 0) if typ == 3 else struct.pack("<I", val)))
            b.write(struct.pack("<I", 0) + comp)
            tuiles[k] = Image.open(io.BytesIO(b.getvalue()))
        v = tuiles[k].getpixel((col % tl, lig % th))
        resultats[nom] = None if v < -9000 else round(v, 3)
    return resultats


def chirps():
    print("CHIRPS v3, pluie par pentade aux points pilotes (domaine public)")
    points = points_pilotes()
    taches = [(a, m, p) for a in ANNEES_CHIRPS for m in range(1, 13) for p in range(1, 7)]
    lignes, echecs = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futurs = {pool.submit(_valeurs_cog, CHIRPS_COG.format(a=a, m=m, p=p), points): (a, m, p)
                  for a, m, p in taches}
        for i, f in enumerate(concurrent.futures.as_completed(futurs), 1):
            a, m, p = futurs[f]
            try:
                for nom, v in f.result().items():
                    lat, lon = points[nom]
                    lignes.append([a, m, p, nom, lat, lon, v])
            except Exception as e:
                echecs.append(f"{a}.{m:02d}.{p} ({e})")
            if i % 200 == 0:
                print(f"  {i}/{len(taches)} pentades")
    lignes.sort()
    sortie = io.StringIO()
    w = csv.writer(sortie)
    w.writerow(["annee", "mois", "pentade", "departement", "latitude", "longitude", "pluie_mm"])
    w.writerows(lignes)
    a0, a1 = ANNEES_CHIRPS[0], ANNEES_CHIRPS[-1]
    note = (f"EXTRAIT : valeur du pixel 0,05° sous chaque centroïde, {len(taches) - len(echecs)}/{len(taches)} "
            f"pentades (pentades 1 à 5 = jours 1-5…21-25, pentade 6 = du 26 à la fin du mois)")
    if echecs:
        note += f" ; échecs : {', '.join(echecs[:20])}"
        print(f"  {len(echecs)} pentades en échec, relancer : python3 {Path(__file__).name} chirps")
    ecrire(RAW / "chirps" / f"chirps_v3_pentades_{a0}-{a1}_points_pilotes.csv",
           sortie.getvalue().encode("utf-8"), "CHIRPS v3.0 (Climate Hazards Center, UCSB)",
           CHIRPS_COG.format(a="AAAA", m=1, p=1).replace(".01.1.", ".MM.P."), note)


def documents():
    print("Rapports publics ANSD, DAPSA et ministère de l'Agriculture")
    for nom, url, titre in DOCUMENTS:
        try:
            contenu = telecharger(url)
        except Exception as e:
            print(f"  ÉCHEC {nom} : {e}")
            continue
        ecrire(RAW / "documents" / nom, contenu, titre, url)


SOURCES = {"geoboundaries": geoboundaries, "power": power, "soilgrids": soilgrids, "isdasoil": isdasoil,
           "faostat": faostat, "wfp": wfp, "chirps": chirps, "documents": documents}

if __name__ == "__main__":
    demandes = sys.argv[1:] or list(SOURCES)
    inconnues = [s for s in demandes if s not in SOURCES]
    if inconnues:
        raise SystemExit(f"Sources inconnues : {inconnues}. Choix : {', '.join(SOURCES)}")
    for s in demandes:
        SOURCES[s]()
