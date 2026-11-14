"""Télécharge les photos de feuilles utiles au module Diagnostic, sans tout rapatrier.

Usage (depuis la racine du dépôt) :
    python3 scripts/donnees/telecharger_images.py [plantvillage] [plantdoc] [chou] [ccmt]

- PlantVillage (Mohanty et al. 2016, Hugging Face mohanty/PlantVillage, CC BY-SA 3.0) :
  l'archive data.zip fait 2,2 Go ; on lit son répertoire central par requêtes HTTP
  Range et on n'extrait que les images couleur des cultures retenues.
- PlantDoc (Singh et al. 2020, GitHub pratikkayal/PlantDoc-Dataset, CC BY 4.0) :
  photos prises au champ ; on ne récupère que les dossiers des cultures retenues.
- Chou (Ayawli et al. 2025, Mendeley Data DOI 10.17632/sjmgzhwrxv.1, CC BY 4.0, Sunyani
  Technical University, Ghana) : alternariose, pourriture noire, mildiou, sain ; l'archive
  mélange images d'origine et images augmentées (rotation, recadrage, bruit…).
- CCMT (Mensah et al. 2023, Mendeley Data DOI 10.17632/bwh3zbpkpv.1, CC BY 4.0, Ghana) : on ne
  garde que la tomate de « Raw Data » (jamais la version augmentée), lue par requêtes Range dans
  l'archive complète de 8,4 Go. L'API de Mendeley ne liste que 1 000 fichiers par dossier, d'où ce
  passage par l'archive. Nettoyage : décision D14 (data/exclusions/terramind_v1.csv).

Les images vont dans data/raw/images/ (exclu de Git) ; un inventaire par classe
est écrit dans data/raw/images/INVENTAIRE.csv et recopié dans data/extraits/.
"""

import csv
import io
import json
import shutil
import sys
import urllib.error
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
CHOU_URL = ("https://data.mendeley.com/public-files/datasets/sjmgzhwrxv/files/"
            "15717f20-a822-48c8-b1f1-cdaf53be636d/file_downloaded")
CCMT_ZIP = "https://data.mendeley.com/public-api/zip/bwh3zbpkpv/download/1"  # redirige vers un lien S3 de 5 min
CHOU_SHA256 = "4dba5e7a553b02eb28a17ac4ab2d671ee6b48223f3fa38ffd89163736240cd79"  # publié par Mendeley


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


class ArchiveMendeley(FichierDistant):
    """Comme FichierDistant, mais le lien signé (valable 5 minutes) est redemandé quand il expire."""

    def __init__(self, url):
        self.depart, self.pos = url, 0
        self._resoudre()

    def _resoudre(self):
        req = urllib.request.Request(self.depart, headers={**UA, "Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            self.url, self.taille = r.url, int(r.headers["Content-Range"].split("/")[-1])

    def read(self, n=-1):
        try:
            return super().read(n)
        except urllib.error.HTTPError as e:
            if e.code not in (400, 403):
                raise
            self._resoudre()
            return super().read(n)


def ccmt():
    print("CCMT (Mendeley Data, Ghana) : lecture du répertoire de l'archive (8,4 Go, rien n'est téléchargé en entier)…")
    zf = zipfile.ZipFile(io.BufferedReader(ArchiveMendeley(CCMT_ZIP), buffer_size=4 * 1024 * 1024))
    prefixe = "Raw Data/CCMT Dataset/Tomato/"
    entrees = [i for i in zf.infolist() if not i.is_dir() and prefixe in i.filename
               and i.filename.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not entrees:
        raise SystemExit("CCMT : aucun fichier « " + prefixe + " » ; noms vus : "
                         + ", ".join(sorted({i.filename.split("/")[0] for i in zf.infolist()})[:10]))
    entrees.sort(key=lambda i: i.header_offset)
    print(f"  {len(entrees)} images de tomate à extraire ({sum(i.compress_size for i in entrees) / 1e6:.0f} Mo)")
    for k, info in enumerate(entrees, 1):
        relatif = info.filename.split(prefixe, 1)[1]
        cible = SORTIE / "ccmt" / "Tomato" / relatif
        if cible.exists() and cible.stat().st_size == info.file_size:
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, cible.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if k % 500 == 0:
            print(f"  {k}/{len(entrees)}")


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


def chou():
    import hashlib
    print("Chou (Mendeley Data, Ghana) : téléchargement de l'archive (140 Mo)…")
    with urllib.request.urlopen(urllib.request.Request(CHOU_URL, headers=UA), timeout=600) as r:
        contenu = r.read()
    empreinte = hashlib.sha256(contenu).hexdigest()
    if empreinte != CHOU_SHA256:
        raise SystemExit(f"Chou : empreinte inattendue {empreinte}")
    # On ne garde que les images d'origine (archive ORIGINAL_ALL_COMBINE_CABBAGE_DISEASES.zip) :
    # les versions augmentées gonfleraient artificiellement les résultats (même règle que CCMT).
    classes = {"Cabbage_Altenaria_spot": "alternariose", "Cabbage - Black_rot": "pourriture_noire",
               "Cabbage - Healthy": "sain", "Cabbage downy mildew - Original": "mildiou"}
    base = SORTIE / "chou_mendeley"
    if base.exists():
        shutil.rmtree(base)
    with zipfile.ZipFile(io.BytesIO(contenu)) as externe:
        nom = next(n for n in externe.namelist() if n.endswith("ORIGINAL_ALL_COMBINE_CABBAGE_DISEASES.zip"))
        with zipfile.ZipFile(io.BytesIO(externe.read(nom))) as zf:
            for info in zf.infolist():
                dossier = Path(info.filename).parent.name
                if info.is_dir() or not info.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                cible = base / classes[dossier] / Path(info.filename).name
                cible.parent.mkdir(parents=True, exist_ok=True)
                cible.write_bytes(zf.read(info))
    print(f"  ok, empreinte SHA-256 conforme ({empreinte[:12]}…)")


def inventaire():
    lignes = []
    for source, licence in (("plantvillage", "CC BY-SA 3.0"), ("plantdoc", "CC BY 4.0"),
                            ("chou_mendeley", "CC BY 4.0"), ("ccmt", "CC BY 4.0")):
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
    choix = sys.argv[1:] or ["plantvillage", "plantdoc", "chou"]
    if "plantvillage" in choix:
        plantvillage()
    if "plantdoc" in choix:
        plantdoc()
    if "chou" in choix:
        chou()
    if "ccmt" in choix:  # pas dans la liste par défaut : à demander explicitement
        ccmt()
    inventaire()
