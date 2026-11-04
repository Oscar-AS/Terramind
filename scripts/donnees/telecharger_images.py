"""Télécharge les photos de feuilles utiles au module Diagnostic, sans tout rapatrier.

Usage (depuis la racine du dépôt) :
    python3 scripts/donnees/telecharger_images.py [plantvillage] [plantdoc]

- PlantVillage (Mohanty et al. 2016, Hugging Face mohanty/PlantVillage, CC BY-SA 3.0) :
  l'archive data.zip fait 2,2 Go ; on lit son répertoire central par requêtes HTTP
  Range et on n'extrait que les images couleur des cultures retenues.
- PlantDoc (Singh et al. 2020, GitHub pratikkayal/PlantDoc-Dataset, CC BY 4.0) :
  photos prises au champ ; on ne récupère que les dossiers des cultures retenues.

Les images vont dans data/raw/images/ (exclu de Git) ; un inventaire par classe
est écrit dans data/raw/images/INVENTAIRE.csv et recopié dans data/extraits/.
"""

import csv
import io
import json
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "data" / "raw" / "images"
UA = {"User-Agent": "TerraMind-collecte/1.0 (projet etudiant PAS Challenge 2026)"}

PV_URL = "https://huggingface.co/datasets/mohanty/PlantVillage/resolve/main/data.zip"
PV_CULTURES = ("Tomato___", "Potato___", "Pepper,_bell___")
PD_DEPOT = "pratikkayal/PlantDoc-Dataset"
PD_MOTS = ("Tomato", "Potato", "Bell_pepper")


class FichierDistant(io.RawIOBase):
    """Fichier en lecture seule dont chaque lecture est une requête HTTP Range."""

    def __init__(self, url):
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            self.url, self.taille = r.url, int(r.headers["Content-Length"])
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, decalage, origine=0):
        self.pos = {0: 0, 1: self.pos, 2: self.taille}[origine] + decalage
        return self.pos

    def read(self, n=-1):
        fin = self.taille if n is None or n < 0 else min(self.taille, self.pos + n)
        if fin <= self.pos:
            return b""
        req = urllib.request.Request(self.url, headers={**UA, "Range": f"bytes={self.pos}-{fin - 1}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            donnees = r.read()
        self.pos += len(donnees)
        return donnees

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)


def plantvillage():
    print("PlantVillage : lecture du répertoire de l'archive…")
    brut = FichierDistant(PV_URL)
    # Grand tampon : regroupe les petites lectures du module zipfile en peu de requêtes.
    zf = zipfile.ZipFile(io.BufferedReader(brut, buffer_size=4 * 1024 * 1024))
    entrees = [i for i in zf.infolist() if not i.is_dir() and "/color/" in f"/{i.filename}"
               and any(f"/{c}" in f"/{i.filename}" for c in PV_CULTURES)]
    entrees.sort(key=lambda i: i.header_offset)  # lecture dans l'ordre du fichier
    print(f"  {len(entrees)} images à extraire "
          f"({sum(i.compress_size for i in entrees) / 1e6:.0f} Mo compressés)")
    for k, info in enumerate(entrees, 1):
        classe, nom = Path(info.filename).parent.name, Path(info.filename).name
        cible = SORTIE / "plantvillage" / classe / nom
        if cible.exists() and cible.stat().st_size == info.file_size:
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, cible.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if k % 2000 == 0:
            print(f"  {k}/{len(entrees)}")


def plantdoc():
    print("PlantDoc : liste des dossiers…")
    api = f"https://api.github.com/repos/{PD_DEPOT}/git/trees/master?recursive=1"
    with urllib.request.urlopen(urllib.request.Request(api, headers=UA), timeout=60) as r:
        arbre = json.load(r)["tree"]
    fichiers = [f for f in arbre if f["type"] == "blob" and f["path"].count("/") == 2
                and any(m in f["path"].split("/")[1] for m in PD_MOTS)]
    print(f"  {len(fichiers)} images à télécharger")
    for k, f in enumerate(fichiers, 1):
        cible = SORTIE / "plantdoc" / f["path"]
        if cible.exists() and cible.stat().st_size == f.get("size"):
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/{PD_DEPOT}/master/{urllib.parse.quote(f['path'])}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                cible.write_bytes(r.read())
        except Exception as e:  # une image manquante ne bloque pas le reste
            print(f"  échec {f['path']} : {e}")
        if k % 200 == 0:
            print(f"  {k}/{len(fichiers)}")


def inventaire():
    lignes = []
    for source, licence in (("plantvillage", "CC BY-SA 3.0"), ("plantdoc", "CC BY 4.0")):
        base = SORTIE / source
        if not base.exists():
            continue
        for d in sorted(p for p in base.rglob("*") if p.is_dir()):
            n = sum(1 for x in d.iterdir() if x.is_file())
            if n:
                lignes.append([source, str(d.relative_to(base)), n, licence])
    entete = ["source", "classe", "images", "licence"]
    for chemin in (SORTIE / "INVENTAIRE.csv", RACINE / "data" / "extraits" / "images_diagnostic_inventaire.csv"):
        chemin.parent.mkdir(parents=True, exist_ok=True)
        with chemin.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(entete)
            w.writerows(lignes)
    for l in lignes:
        print(f"  {l[0]:12} {l[1]:55} {l[2]:>6}")


if __name__ == "__main__":
    choix = sys.argv[1:] or ["plantvillage", "plantdoc"]
    if "plantvillage" in choix:
        plantvillage()
    if "plantdoc" in choix:
        plantdoc()
    inventaire()
