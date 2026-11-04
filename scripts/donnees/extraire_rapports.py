"""Extrait des tableaux des rapports publics de data/raw/documents/ vers data/extraits/.

Usage (depuis la racine du dépôt, après `telecharger_sources.py documents`) :
    python3 scripts/donnees/extraire_rapports.py

Dépendances : pdftotext (Poppler) et openpyxl.
Chaque fichier produit indique sa source (document, tableau, page) dans
data/extraits/SOURCES.csv. Les valeurs sont recopiées telles quelles ; les
contrôles de cohérence échouent bruyamment plutôt que de produire une table
fausse.
"""

import csv
import re
import subprocess
from pathlib import Path

import openpyxl

RACINE = Path(__file__).resolve().parents[2]
DOCS = RACINE / "data" / "raw" / "documents"
SORTIE = RACINE / "data" / "extraits"

REGIONS = ["Dakar", "Ziguinchor", "Diourbel", "Saint-Louis", "Tambacounda", "Kaolack", "Thiès", "Louga",
           "Fatick", "Kolda", "Matam", "Kaffrine", "Kédougou", "Sédhiou", "Urbain", "Rural", "National"]

# Ordre des colonnes des tableaux X21 à X24 du RGPH-5. L'extraction PDF brouille
# les en-têtes ; l'ordre a été reconstitué puis vérifié sur la ligne nationale,
# qui doit reproduire les chiffres cités dans le texte du rapport (voir CONTROLES).
COLONNES_A = ["Plantes ornementales", "Oignon", "Aubergine amère (jaxatu)", "Aubergine douce", "Chou",
              "Pomme de terre", "Gombo", "Piment", "Fraise", "Melon", "Pastèque", "Tomate", "Carotte",
              "Navet", "Concombre"]
COLONNES_B = ["Laitue/salade", "Riz irrigué", "Bissap", "Haricot vert", "Maïs", "Courge", "Poivron",
              "Persil", "Arachide", "Autres cultures irriguées, maraîchères ou florales"]
TABLEAUX_RGPH = [  # (tableau, saison, colonnes, page)
    ("X21", "contre-saison froide (octobre à mars)", COLONNES_A, 38),
    ("X22", "contre-saison froide (octobre à mars)", COLONNES_B, 39),
    ("X23", "contre-saison chaude (avril à juin)", COLONNES_A, 40),
    ("X24", "contre-saison chaude (avril à juin)", COLONNES_B, 41),
]
# Chiffres nationaux cités dans le texte du rapport (p. 37 et 40).
CONTROLES = {
    ("X21", "Oignon"): 47.5, ("X21", "Tomate"): 47.4, ("X21", "Piment"): 46.1,
    ("X23", "Piment"): 40.8, ("X23", "Tomate"): 38.2, ("X23", "Oignon"): 33.7, ("X23", "Chou"): 25.1,
    ("X24", "Bissap"): 38.8, ("X24", "Laitue/salade"): 24.5, ("X24", "Maïs"): 9.5,
}

sources = []


def texte_pdf(nom):
    return subprocess.run(["pdftotext", "-layout", str(DOCS / nom), "-"], check=True,
                          capture_output=True, text=True).stdout


def ecrire(nom, entete, lignes, source, detail):
    SORTIE.mkdir(parents=True, exist_ok=True)
    with (SORTIE / nom).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(entete)
        w.writerows(lignes)
    sources.append([nom, source, detail, len(lignes)])
    print(f"  ok  data/extraits/{nom} ({len(lignes)} lignes)")


def nombre(txt):
    return float(txt.replace(" ", "").replace(" ", "").replace(",", "."))


def rgph5_maraichage():
    texte = texte_pdf("ansd_rgph5_ch10_agriculture_def.pdf")
    lignes = []
    for tab, saison, colonnes, page in TABLEAUX_RGPH:
        # Dernière occurrence du titre = le tableau lui-même (la première est le sommaire).
        debut = texte.rindex(f"Tableau {tab} :")
        fin = texte.index("Source : ANSD. RGPH-5", debut)
        # Le tableau X21 continue sur la page suivante (Sédhiou, milieux, national).
        if tab in ("X21", "X23") and "National" not in texte[debut:fin]:
            fin = texte.index("Source : ANSD. RGPH-5", fin + 1)
        trouves = {}
        for brut in texte[debut:fin].splitlines():
            m = re.match(r"\s*(" + "|".join(map(re.escape, REGIONS)) + r")(?: \(%\))?\s+(.*)$", brut)
            if not m:
                continue
            valeurs = re.findall(r"\d+,\d", m.group(2))
            if len(valeurs) != len(colonnes):
                raise SystemExit(f"{tab} {m.group(1)} : {len(valeurs)} valeurs au lieu de {len(colonnes)}")
            trouves[m.group(1)] = [nombre(v) for v in valeurs]
        manquantes = set(REGIONS) - set(trouves)
        if manquantes:
            raise SystemExit(f"{tab} : lignes manquantes {manquantes}")
        for (t, culture), attendu in CONTROLES.items():
            if t == tab and trouves["National"][colonnes.index(culture)] != attendu:
                raise SystemExit(f"{tab} {culture} : contrôle national raté, ordre des colonnes à revoir")
        for zone in REGIONS:
            for culture, v in zip(colonnes, trouves[zone]):
                lignes.append([saison, zone, culture, v, tab, page])
    ecrire("rgph5_2023_part_menages_maraichers_par_culture.csv",
           ["saison", "zone", "culture", "pct_menages_maraichers", "tableau", "page"], lignes,
           "ANSD, RGPH-5 (2023), chapitre 10 Agriculture, rapport définitif",
           "Tableaux X21 à X24 : % des ménages agricoles pratiquant le maraîchage ou la floriculture "
           "dans la saison qui cultivent chaque produit, par région et milieu de résidence")


def dhort_production_nationale():
    texte = texte_pdf("ansd_bulletin_oct_2023.pdf")
    debut = texte.rindex("Tableau I.4- 3 : Production de produits horticoles")  # pas le sommaire
    fin = texte.index("Source: Direction de l", debut)
    bloc = texte[debut:fin]
    campagnes = re.findall(r"20\d\d/20?\d\d", bloc)[:7]
    if len(campagnes) != 7:
        raise SystemExit(f"Bulletin : en-tête de campagnes inattendu {campagnes}")
    campagnes = [c if len(c) == 9 else c[:5] + "20" + c[5:] for c in campagnes]
    lignes = []
    for brut in bloc.splitlines():
        m = re.match(r"([A-ZÉÈ/ ]+[A-ZÉÈ)])\s+((?:\d{1,3}(?: \d{3})*\s+){7})", brut.strip() + " ")
        if not m:
            continue
        valeurs = re.findall(r"\d{1,3}(?: \d{3})*", m.group(2))
        if len(valeurs) != 7:
            continue
        for camp, v in zip(campagnes, valeurs):
            lignes.append([m.group(1).strip().capitalize(), camp, int(v.replace(" ", ""))])
    if not any(l[0] == "Oignon" and l[1] == "2018/2019" and l[2] == 444871 for l in lignes):
        raise SystemExit("Bulletin : contrôle oignon 2018/2019 raté")
    ecrire("dhort_production_horticole_nationale_2015-2022.csv", ["produit", "campagne", "production_t"], lignes,
           "ANSD, bulletin mensuel d'octobre 2023, tableau I.4-3 (source : Direction de l'Horticulture)",
           "Production nationale en tonnes ; données antérieures révisées ; 2021/2022 provisoire")


def eaa_2020_2021_maraichage():
    ws = openpyxl.load_workbook(DOCS / "dapsa_eaa_2020-2021_tableaux_annexes.xlsx", read_only=True,
                                data_only=True)["4.2 Prod&Util_Maraichage"]
    rangs = list(ws.iter_rows(values_only=True))

    def cherche(titre):
        return next(i for i, r in enumerate(rangs) if r and isinstance(r[0], str) and r[0].startswith(titre))

    # 4.2.1 : part des ménages ayant fait du maraîchage, par région
    i = cherche("Tableau 4.2.1")
    lignes = [[r[0].strip().title(), r[1]] for r in rangs[i + 2:i + 16] if r[0] and r[1] is not None]
    ecrire("eaa_2020-2021_part_menages_maraichage_par_region.csv", ["region", "pct_menages_agricoles"], lignes,
           "DAPSA, EAA 2020-2021, tableaux annexes, tableau 4.2.1",
           "% des ménages agricoles ayant pratiqué une culture maraîchère sur 12 mois ; moyenne nationale 14,0 %")

    # 4.2.3 : production moyenne par ménage producteur, par région et culture
    i = cherche("Tableau 4.2.3")
    entete = [c for c in rangs[i + 1][1:] if c]
    lignes = []
    for r in rangs[i + 2:i + 17]:
        if not r[0]:
            continue
        for culture, v in zip(entete, r[1:]):
            lignes.append([r[0].strip().title(), culture, None if v in ("-", None) else v])
    ecrire("eaa_2020-2021_production_moyenne_menage_maraichage.csv", ["region", "culture", "kg_par_menage"],
           lignes, "DAPSA, EAA 2020-2021, tableaux annexes, tableau 4.2.3",
           "Production moyenne (kg) par ménage producteur ; vide = culture non observée ; petits effectifs par "
           "région (voir N national au tableau 4.2.2) : ordre de grandeur, pas une statistique précise")

    # 4.2.2 : moyenne nationale et nombre de ménages enquêtés (N) par culture
    i = cherche("Tableau 4.2.2")
    lignes = []
    for a, b in zip(rangs[i + 2:i + 40:2], rangs[i + 3:i + 41:2]):
        if a[0] and a[1] == "Moyenne" and b[1] == "N":
            lignes.append([a[0].strip(), a[4], b[4]])
    ecrire("eaa_2020-2021_production_moyenne_menage_national.csv",
           ["culture", "kg_par_menage", "menages_enquetes_n"], lignes,
           "DAPSA, EAA 2020-2021, tableaux annexes, tableau 4.2.2",
           "Production moyenne (kg) par ménage producteur et nombre de ménages de l'échantillon")

    # 4.2.4 et 4.2.5 : utilisation des productions et contrats de commercialisation
    i = cherche("Tableau 4.2.4")
    lignes = [[r[0].strip(), r[1], r[2], r[3], r[4]] for r in rangs[i + 2:i + 24]
              if r[0] and r[0].strip() != "Total" and isinstance(r[1], (int, float))]
    ecrire("eaa_2020-2021_utilisation_productions_maraicheres.csv",
           ["culture", "pct_vente", "pct_consommation", "pct_semences", "pct_dons"], lignes,
           "DAPSA, EAA 2020-2021, tableaux annexes, tableau 4.2.4", "Répartition (%) de la production par usage")


def eaa_2022_2023():
    """Tableaux du classeur EAA 2022-2023 utiles au besoin (ravageurs, traitements, usages).
    Les feuilles sont des données de graphiques : on repère chaque bloc par son titre et on
    s'arrête à la ligne « Total »."""
    wb = openpyxl.load_workbook(DOCS / "dapsa_eaa_2022-2023_tableaux.xlsx", read_only=True, data_only=True)

    def bloc(feuille, titre, decalage_entete):
        rangs = [[c for c in r if c is not None] for r in wb[feuille].iter_rows(values_only=True)]
        i = next(k for k, r in enumerate(rangs) if r and isinstance(r[0], str) and r[0].startswith(titre))
        entete = [str(c).strip(" ,") for c in rangs[i + decalage_entete]]
        lignes = []
        for r in rangs[i + decalage_entete + 1:]:
            if not r:
                continue
            lignes.append(r)
            if str(r[0]).strip() == "Total":
                return entete, lignes
        raise SystemExit(f"EAA 2022-2023 : fin du bloc « {titre} » introuvable")

    source = "DAPSA, Enquête agricole annuelle 2022-2023, classeur des tableaux et graphiques"
    # 8.1.2 : principaux chocs subis (8 premières colonnes du premier bloc ; % de ménages agricoles)
    entete, rangs = bloc("Chapitre 8", "Graphique 8.1 2", 2)
    lignes = [[r[0].strip().title(), choc.split(":")[-1].strip(), round(v * 100, 1)]
              for r in rangs for choc, v in zip(entete[1:], r[1:]) if isinstance(v, (int, float))]
    if not any(l[0] == "Louga" and "ravageurs" in l[1] and l[2] == 43.9 for l in lignes):
        raise SystemExit("EAA 2022-2023 : contrôle ravageurs Louga raté")
    ecrire("eaa_2022-2023_chocs_production_par_region.csv", ["region", "choc", "pct_menages"], lignes, source,
           "Graphique 8.1.2 : % des ménages agricoles ayant subi chaque choc de production (tous types de "
           "cultures, pas seulement le maraîchage) ; libellés recopiés du classeur")

    # 3.4.3 : produits phytosanitaires par culture principale (% des parcelles)
    entete, rangs = bloc("Chapitre 3", "Graphique 3.4 3", 1)
    lignes = [[r[0].strip(), produit, round(v * 100, 1)]
              for r in rangs for produit, v in zip(entete[1:], r[1:]) if isinstance(v, (int, float))]
    ecrire("eaa_2022-2023_produits_phytosanitaires_par_culture.csv", ["culture", "type_produit", "pct_parcelles"],
           lignes, source, "Graphique 3.4.3 : % des parcelles traitées par type de produit, selon la culture "
           "principale ; certaines cultures reposent sur très peu de parcelles (valeurs 0 ou 100 %)")

    # 4.2.3 : usages de la production maraîchère (bloc de gauche, en proportions)
    entete, rangs = bloc("Chapitre 4", "Graphique 4.2 3", 1)
    lignes = [[r[0].strip()] + [round(v * 100, 1) for v in r[1:5]] for r in rangs
              if all(isinstance(v, (int, float)) for v in r[1:5])]
    ecrire("eaa_2022-2023_utilisation_productions_maraicheres.csv",
           ["culture", "pct_vente", "pct_semences", "pct_dons", "pct_consommation"], lignes, source,
           "Graphique 4.2.3, bloc de gauche : répartition (%) de la production maraîchère par usage ; le bloc "
           "de droite du classeur n'a pas de titre clair et n'est pas repris")


if __name__ == "__main__":
    print("Extraction des tableaux")
    rgph5_maraichage()
    dhort_production_nationale()
    eaa_2020_2021_maraichage()
    eaa_2022_2023()
    with (SORTIE / "SOURCES.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fichier", "document_source", "contenu", "lignes"])
        w.writerows(sources)
