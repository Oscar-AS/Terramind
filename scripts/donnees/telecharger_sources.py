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

# Documents agronomiques publics qui remplacent les fiches ISRA-CDH 2022 introuvables (source `fiches`).
# Classés par proximité avec les Niayes : Sénégal, puis littoral mauritanien (CNRADA), puis Niger
# (zone la moins proche, voir research/itineraires-par-culture.md).
FICHES = [
    ("min_piesan_livret_oignon_niayes_fr_wo_2022.pdf",
     "https://agriculture.gouv.sn/wp-content/uploads/2022/06/Livret-oignon-francais-wolof.pdf",
     "Ministère de l'Agriculture (PIESAN), Bonnes pratiques de production d'oignon dans les Niayes, FR/wolof, 2022"),
    ("paden_fiche_oignon_niayes.pdf", "https://duddal.org/files/original/39a30d91086dcdf5d3705b8973c518d6be6d6356.pdf",
     "PADEN, fiche technique des bonnes pratiques de production d'oignon dans les Niayes (résultats ISRA-CDH)"),
    ("cirad_isra_guide_pratique_maraichage_senegal_1987.pdf",
     "https://open-library.cirad.fr/files/4/751__Guide_pratique_du_maraichage_au_Senegal.pdf",
     "Beniest et al., Guide pratique du maraîchage au Sénégal, ISRA/CDH-FAO, 1987"),
    ("fao_radhort_semences_tomate_senegal.pdf",
     "https://duddal.org/files/original/3b6754ae5981f3846f3b1cdf425dd647eaf5498c.pdf",
     "FAO/RADHORT/ISRA-CDH, Techniques de production de semences de tomate au Sénégal (variétés CDH) ; copie DUDDAL, le site de la FAO refuse les scripts"),
    ("fao_production_precoce_oignon_senegal.pdf",
     "https://openknowledge.fao.org/server/api/core/bitstreams/87539e9a-3717-4361-8937-06ad2c7a17af/content",
     "FAO, Les techniques de production précoce pour l'étalement de la culture de l'oignon au Sénégal"),
    ("fao_radhort_oignon_moyenne_vallee.pdf",
     "https://openknowledge.fao.org/server/api/core/bitstreams/55f53417-aee9-4afb-b73b-96645d8e67db/content",
     "FAO/RADHORT, La culture de l'oignon dans la moyenne vallée du fleuve Sénégal"),
    ("fao_pepinieres_maraicheres_afrique_ouest.pdf",
     "https://openknowledge.fao.org/server/api/core/bitstreams/f7907421-8016-46b3-a455-b312701cf893/content",
     "FAO GCP/RAF/244/BEL, Les pépinières maraîchères en Afrique soudano-sahélienne"),
    ("cirad_itineraires_oignon_vallee.pdf", "https://agritrop.cirad.fr/543957/1/document_543957.pdf",
     "CIRAD/ISRA, Quelques éléments d'analyse sur les itinéraires techniques (oignon, vallée du fleuve)"),
    ("stdf_pg302_aumn_chou_niayes_rapport.pdf",
     "https://www.standardsfacility.org/sites/default/files/PG_302_ProjectActivities_Report.pdf",
     "STDF/AUMN, projet PG 302, production durable du chou dans les Niayes, rapport d'activités"),
] + [
    (f"cnrada_{s}.html", f"https://cnrada.org/fiche-technique/{s}/",
     f"CNRADA (Mauritanie), {s.replace('-', ' ')}")
    for s in ("fiche-technique-de-la-tomate", "fiche-technique-du-poivron", "fiche-technique-du-choux-pomme",
              "fiche-technique-de-la-pomme-de-terre", "fiche-technique-de-loignon", "fiche-technique-de-la-carotte",
              "fiche-technique-du-piment", "fiche-technique-du-jacatou", "fiche-technique-de-laubergine",
              "fiche-technique-du-gombo", "fiche-technique-de-la-pepiniere-maraichere")
] + [
    ("niger_techniques_production_chou.pdf",
     "https://duddal.org/files/original/42982ad5f9b03fb4a86fbc3a9d146a07de108252.pdf",
     "Niger, ministère de l'Agriculture, techniques de production des cultures irriguées : le chou"),
    ("niger_cra_maradi_tomate.pdf", "https://duddal.org/files/original/e7629bcc5033ce35fe07dc456a3bae3091d7f291.pdf",
     "Niger, Chambre régionale d'agriculture de Maradi, fiche technico-économique tomate"),
    ("niger_cra_dosso_poivron.pdf", "https://reca-niger.org/IMG/pdf/FT_Poivron_CRADosso_V1.pdf",
     "Niger, Chambre régionale d'agriculture de Dosso, fiche technique poivron"),
    ("niger_cra_dosso_pomme_de_terre.pdf", "https://reca-niger.org/IMG/pdf/FTE_pommeDterre_Dosso_Mai2017.pdf",
     "Niger, Chambre régionale d'agriculture de Dosso, fiche technico-économique pomme de terre, 2017"),
]

# Documents du PADEN (Programme d'aménagement et de développement économique des Niayes, financé par
# le Canada). Le site paden-senegal.org n'existe plus ; copies de la Wayback Machine (adresse « id_ » = fichier
# d'origine, sans bandeau). Le manuel sur les pesticides n'est pas repris (règle : aucun produit ni dose).
PADEN = [
    ("paden_fiche_technique_pomme_de_terre_2014.pdf", "https://web.archive.org/web/20171215030645id_/http://www.paden-senegal.org:80/IMG/pdf/fiche_technique_de_production_pomme_de_terre.pdf",
     "PADEN, fiche technique de production intensive de la pomme de terre (A. Seck, janv. 2014) ; copie Wayback 20171215"),
    ("paden_fiche_bonnes_pratiques_pomme_de_terre.pdf", "https://web.archive.org/web/20160429021611id_/http://paden-senegal.org/IMG/pdf/fiche_technique_bp_pdt-v_finale.pdf",
     "PADEN, fiche des bonnes pratiques de production de pomme de terre dans les Niayes ; copie Wayback 20160429"),
    ("paden_fiche_bonnes_pratiques_chou.pdf", "https://web.archive.org/web/20160428213721id_/http://paden-senegal.org/IMG/pdf/fiche_technique_bp_chou.pdf",
     "PADEN, fiche des bonnes pratiques de production du chou dans les Niayes ; copie Wayback 20160428"),
    ("paden_livret_chou_fr.pdf", "https://web.archive.org/web/20171215080250id_/http://www.paden-senegal.org:80/IMG/pdf/livret_chou_fr.pdf",
     "PADEN, livret chou (français) ; copie Wayback 20171215"),
    ("paden_livret_chou_wolof.pdf", "https://web.archive.org/web/20170301231412id_/http://paden-senegal.org/IMG/pdf/livret_chou_wolof.pdf",
     "PADEN, livret chou (wolof) ; copie Wayback 20170301"),
    ("paden_livret_pomme_de_terre_fr.pdf", "https://web.archive.org/web/20170302033944id_/http://paden-senegal.org/IMG/pdf/livret_pdt_3_fr.pdf",
     "PADEN, livret pomme de terre (français) ; copie Wayback 20170302"),
    ("paden_livret_pomme_de_terre_wolof.pdf", "https://web.archive.org/web/20170302033947id_/http://paden-senegal.org/IMG/pdf/livret_pdt_wolof_2.pdf",
     "PADEN, livret pomme de terre (wolof) ; copie Wayback 20170302"),
    ("paden_livret_oignon_fr.pdf", "https://web.archive.org/web/20170301150712id_/http://paden-senegal.org/IMG/pdf/maquette_livret_a5_oignon_fr.pdf",
     "PADEN, livret oignon (français) ; copie Wayback 20170301"),
    ("paden_livret_oignon_wolof.pdf", "https://web.archive.org/web/20170301211212id_/http://paden-senegal.org/IMG/pdf/maquette_livret_a5_oignon_wolof.pdf",
     "PADEN, livret oignon (wolof) ; copie Wayback 20170301"),
    ("paden_fiche_technique_carotte.pdf", "https://web.archive.org/web/20170329161824id_/http://www.paden-senegal.org:80/IMG/pdf/fiche_technique_carotte.pdf",
     "PADEN, fiche technique carotte ; copie Wayback 20170329"),
    ("paden_livret_carotte_wolof.pdf", "https://web.archive.org/web/20170301210049id_/http://paden-senegal.org/IMG/pdf/maquette_livret_a5_carotte_wolof.pdf",
     "PADEN, livret carotte (wolof) ; copie Wayback 20170301"),
    ("paden_depliant_tuta_absoluta.pdf", "https://web.archive.org/web/20160428163414id_/http://paden-senegal.org/IMG/pdf/depliant_tuta_absoluta.pdf",
     "PADEN, dépliant sur la mineuse de la tomate (Tuta absoluta) ; copie Wayback 20160428"),
    ("paden_manuel_principaux_ravageurs_niayes.pdf", "https://web.archive.org/web/20160428092246id_/http://paden-senegal.org/IMG/pdf/manuel_principaux_ravageurs_decultures_niayes.pdf",
     "PADEN, manuel des principaux ravageurs des cultures des Niayes ; copie Wayback 20160428"),
    ("dhort_resultats_recensement_horticulture_niayes.pdf", "https://web.archive.org/web/20160428102140id_/http://paden-senegal.org/IMG/pdf/dhor_resultats_du_recensement_de_l_horticulture_dans_les_niayes.pdf",
     "Direction de l'Horticulture, résultats du recensement de l'horticulture dans les Niayes (diffusé par le PADEN) ; copie Wayback 20160428"),
]

# Kallaama (Gauthier, Ndiaye, Guissé 2024 ; Jokalante, Orange, EPT ; Lacuna Fund), CC BY 4.0 :
# paroles agricoles en wolof (radio interactive, groupes de discussion, messages vocaux).
# On ne prend que le texte (transcriptions validées par un superviseur, lexique de prononciation,
# corpus écrit), pas les 5,4 Go d'audio.
KALLAAMA_DEPOT = "gauthelo/kallaama-speech-dataset"
KALLAAMA_RACINE = "https://raw.githubusercontent.com/gauthelo/kallaama-speech-dataset/master/"
KALLAAMA_FICHIERS = ("LICENSE", "README.md", "data/metadata.md", "data/lexicons/wolof/README.md",
                     "data/lexicons/wolof/wol_lexicon.xsampa.txt", "data/text_corpora/README.md",
                     "data/text_corpora/wolof.txt")

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
    if regle == "expm1(x/100)":
        return math.expm1(x / 100)
    raise ValueError(f"règle de retransformation inconnue : {regle}")


# Corrections vérifiées des métadonnées iSDAsoil d'AWS. Pour l'azote total, le fichier JSON
# indique expm1(x/10), ce qui donne jusqu'à 445 g/kg (impossible : un sol en a ~0,2 à 3 g/kg).
# Le catalogue Google Earth Engine d'iSDA (ISDASOIL/Africa/v1/nitrogen_total, vérifié le
# 2 nov 2026) indique exp(x/100)-1 ; les autres règles des deux sources concordent.
ISDASOIL_REGLES_CORRIGEES = {"nitrogen_total": "expm1(x/100)"}
# Légende du code de texture (texture_class_attribute_table.csv, publiée avec la carte).
ISDASOIL_TEXTURE_URL = "https://isdasoil.s3.amazonaws.com/soil_data/texture_class/texture_class_attribute_table.csv"


def isdasoil():
    """Valeurs iSDAsoil (30 m) aux points pilotes, lues dans les COG publics d'AWS sans compte.
    Seule la tuile contenant chaque point est téléchargée (requêtes HTTP partielles)."""
    print("iSDAsoil (sols à 30 m, CC BY 4.0), lecture des tuiles utiles sur AWS")
    legende_brute = telecharger(ISDASOIL_TEXTURE_URL)
    ecrire(RAW / "isdasoil" / "metadonnees" / "texture_class_attribute_table.csv", legende_brute,
           "iSDAsoil (iSDA)", ISDASOIL_TEXTURE_URL)
    lignes = isdasoil_points(points_pilotes(), ISDASOIL_PROPRIETES, legende_brute, enregistrer_meta=True)
    sortie = io.StringIO()
    w = csv.writer(sortie)
    w.writerow(["propriete", "bande", "departement", "latitude", "longitude", "valeur_brute", "valeur",
                "unite", "retransformation"])
    w.writerows(lignes)
    ecrire(RAW / "isdasoil" / "isdasoil_points_pilotes.csv", sortie.getvalue().encode("utf-8"),
           "iSDAsoil (iSDA), COG publics sur AWS", ISDASOIL.format(p="PROPRIETE", ext="tif"),
           "EXTRAIT : pixel de 30 m sous chaque centroïde ; valeur = moyenne retransformée selon les métadonnées ; "
           "écarts types laissés bruts ; texture_class = classe USDA d'après la légende publiée ; "
           "azote : règle exp(x/100)-1 du catalogue Earth Engine (le JSON d'AWS indique x/10, erroné)")


def isdasoil_points(points, proprietes, legende_brute, enregistrer_meta=False, fenetre=0):
    """Lit les propriétés iSDAsoil sous chaque point {nom: (lat, lon)}. Avec fenetre=n, la valeur est la
    moyenne des pixels valides d'un carré de (2n+1)² pixels autour du point (dans la même tuile), plus
    représentative d'une zone qu'un pixel isolé. Renvoie des lignes [prop, bande, nom, lat, lon, brut, valeur,
    unite, regle] ; « brut » est la moyenne des valeurs brutes de la fenêtre."""
    legende = {int(r["Value"]): r["Description"]
               for r in csv.DictReader(io.StringIO(legende_brute.decode("utf-8-sig")))}
    lignes = []
    for prop in proprietes:
        meta_url = ISDASOIL.format(p=prop, ext="json")
        meta_brut = telecharger(meta_url)
        if enregistrer_meta:
            ecrire(RAW / "isdasoil" / "metadonnees" / f"{prop}.json", meta_brut, "iSDAsoil (iSDA)", meta_url)
        meta = json.loads(meta_brut)
        regle, unite = meta.get("back-transformation"), meta.get("unit") or ""
        regle = ISDASOIL_REGLES_CORRIGEES.get(prop, regle)
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
            ly, lx = lig % th, col % tl
            for i, bande in enumerate(bandes):
                if fenetre == 0:
                    bruts = [struct.unpack_from("<" + fmt, tuiles[k], ((ly * tl + lx) * nb_bandes + i) * octets)[0]]
                else:
                    bruts = [struct.unpack_from("<" + fmt, tuiles[k], ((yy * tl + xx) * nb_bandes + i) * octets)[0]
                             for yy in range(max(0, ly - fenetre), min(th, ly + fenetre + 1))
                             for xx in range(max(0, lx - fenetre), min(tl, lx + fenetre + 1))]
                bruts = [b for b in bruts if b != nodata]
                if not bruts:
                    brut, valeur = None, None
                elif prop == "texture_class":
                    brut = max(set(bruts), key=bruts.count)  # classe la plus fréquente
                    valeur = legende[brut]  # classe USDA en anglais (ex. « Sandy Loam »)
                elif bande.startswith("mean"):
                    brut = bruts[0] if fenetre == 0 else round(sum(bruts) / len(bruts), 2)
                    valeur = round(_retransformer(regle, brut) if fenetre == 0
                                   else sum(_retransformer(regle, b) for b in bruts) / len(bruts), 3)
                else:
                    brut = bruts[0] if fenetre == 0 else round(sum(bruts) / len(bruts), 2)
                    valeur = None  # écart type : retransformation non documentée pour les échelles log
                lignes.append([prop, bande, nom, lat, lon, brut, valeur, unite, regle or ""])
        print(f"  {prop} : {len(tuiles)} tuile(s)")
    return lignes


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


def fiches():
    """Documents agronomiques publics (itinéraires techniques), à la place des fiches ISRA-CDH 2022."""
    print("Fiches et guides agronomiques publics (Sénégal, Mauritanie, Niger)")
    for nom, url, titre in FICHES:
        try:
            contenu = telecharger(url)
        except Exception as e:
            print(f"  ÉCHEC {nom} : {e}")
            continue
        ecrire(RAW / "documents" / "fiches" / nom, contenu, titre, url)


def paden():
    """Documents du PADEN archivés (le site d'origine n'existe plus)."""
    print("Documents du PADEN (copies de la Wayback Machine)")
    for nom, url, titre in PADEN:
        try:
            contenu = telecharger(url, essais=4, delai=20)
        except Exception as e:
            print(f"  ÉCHEC {nom} : {e}")
            continue
        if not contenu.startswith(b"%PDF"):
            print(f"  ÉCHEC {nom} : la réponse n'est pas un PDF")
            continue
        ecrire(RAW / "documents" / "paden" / nom, contenu, titre, url)


def kallaama():
    """Corpus Kallaama, partie texte en wolof (transcriptions validées, lexique, corpus écrit)."""
    print("Kallaama (CC BY 4.0), texte wolof seulement")
    arbre = json.loads(telecharger(f"https://api.github.com/repos/{KALLAAMA_DEPOT}/git/trees/master?recursive=1"))
    stm = [x["path"] for x in arbre["tree"] if x["type"] == "blob"
           and x["path"].startswith("data/transcriptions/checked/transcriptions-wol/stm/") and x["path"].endswith(".stm")]
    for chemin in list(KALLAAMA_FICHIERS) + stm:
        url = KALLAAMA_RACINE + chemin
        ecrire(RAW / "kallaama" / chemin, telecharger(url), "Kallaama (Gauthier et al. 2024), CC BY 4.0", url)


SOURCES = {"geoboundaries": geoboundaries, "power": power, "soilgrids": soilgrids, "isdasoil": isdasoil,
           "faostat": faostat, "wfp": wfp, "chirps": chirps, "documents": documents, "fiches": fiches,
           "paden": paden, "kallaama": kallaama}

if __name__ == "__main__":
    demandes = sys.argv[1:] or list(SOURCES)
    inconnues = [s for s in demandes if s not in SOURCES]
    if inconnues:
        raise SystemExit(f"Sources inconnues : {inconnues}. Choix : {', '.join(SOURCES)}")
    for s in demandes:
        SOURCES[s]()
