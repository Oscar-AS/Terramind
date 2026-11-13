"""Recherche dans les fiches validées (content/fiches/), sans dépendance externe (D8).

Chaque fiche est découpée en passages (une section « ## »). La recherche utilise BM25 sur des
mots normalisés (minuscules, sans accents, sans mots vides, pluriels simples retirés). Les
références entre crochets ([G87 p. 140]) sont retirées du texte et converties en sources.
"""

from __future__ import annotations

import math
import os
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parents[4]
DOSSIER = Path(os.environ.get("FICHES_PATH") or RACINE / "content" / "fiches")
VIDES = set("""a au aux avec ce ces cet cette comme dans de des du elle en est et eux il ils je la le les leur lui
ma mais me mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une
vos votre vous y quoi quand comment quel quelle quels quelles est-ce sont suis faire fait faut peut peux dois
mon ma mes plus tres bien aussi alors donc ca cela ceci tout tous toute toutes j l d c n s m t qu y""".split())
REF = re.compile(r"\s*\[([^\]]+)\]")
SYNONYMES = {  # mots courants des agriculteurs → mots des fiches
    "tomates": "tomate", "oignons": "oignon", "choux": "chou", "pdt": "pomme",
    "taches": "tache", "jaunes": "jaune", "trous": "trou", "chenilles": "chenille",
    "semer": "semis", "seme": "semis", "planter": "plantation", "plante": "plantation", "repiquer": "repiquage",
    "arrosage": "arroser", "sale": "sel", "salee": "sel", "salinite": "sel", "traiter": "traitement",
    "soigner": "traitement", "engrais": "engrais", "puit": "puits",
}
NOMS_CULTURES = {"tomato": "tomate", "onion": "oignon", "cabbage": "chou", "potato": "pomme terre",
                 "pepper": "poivron", "carrot": "carotte", "bitter_eggplant": "jaxatu"}


def normaliser(texte: str) -> list[str]:
    t = unicodedata.normalize("NFD", texte.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    mots = re.findall(r"[a-z0-9]+", t)
    sortie = []
    for m in mots:
        m = SYNONYMES.get(m, m)
        if m in VIDES or len(m) < 2:
            continue
        if len(m) > 4 and m.endswith(("s", "x")):
            m = m[:-1]
        sortie.append(m)
    return sortie


@dataclass
class Passage:
    fiche: str
    titre: str
    section: str
    texte: str
    references: list[str] = field(default_factory=list)
    mots: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _abreviations() -> dict[str, str]:
    chemin = DOSSIER / "_SOURCES.md"
    if not chemin.exists():
        return {}
    table = {}
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Z0-9]+)\s*\|\s*(.+?)\s*\|$", ligne)
        if m and m.group(1) != "Abréviation":
            document = re.sub(r"<[^>]+>", "", m.group(2)).replace("*", "").strip(" .")
            table[m.group(1)] = document
    return table


def _source(ref: str) -> dict:
    if ref.startswith("FICHE "):
        return {"document": f"Fiche TerraMind « {ref[6:]} »", "page": "content/fiches"}
    abrev, _, page = ref.partition(" ")
    abrev = abrev.rstrip(",;")
    document = _abreviations().get(abrev, abrev)
    page = page.replace("p.", "").strip(" ;,") or "—"
    return {"document": document, "page": page}


@lru_cache(maxsize=1)
def passages() -> list[Passage]:
    resultat = []
    for chemin in sorted(DOSSIER.glob("*.md")):
        if chemin.name.startswith("_"):
            continue
        brut = chemin.read_text(encoding="utf-8")
        entete, _, corps = brut.partition("\n---\n") if brut.startswith("---") else ("", "", brut)
        titre = re.search(r"^titre:\s*(.+)$", entete, re.M)
        titre = titre.group(1).strip() if titre else chemin.stem
        cultures = re.search(r"^cultures:\s*(.+)$", entete, re.M)
        noms = " ".join(NOMS_CULTURES.get(c.strip(), "") for c in (cultures.group(1).split(",") if cultures else []))
        for bloc in re.split(r"\n(?=## )", corps):
            if not bloc.startswith("## "):
                continue
            section, _, texte = bloc.partition("\n")
            refs = [r for groupe in REF.findall(texte) for r in re.split(r"\s*;\s*", groupe)]
            propre = REF.sub("", texte).strip()
            if not propre:
                continue
            # Les fiches sans référence pour une section restent citées par leur titre.
            refs = refs or [f"FICHE {titre}"]
            resultat.append(Passage(chemin.stem, titre, section[3:].strip(), propre, refs,
                                    normaliser(f"{titre} {noms} {section} {section} {propre}")))
    return resultat


@lru_cache(maxsize=1)
def _index():
    ps = passages()
    df = Counter(m for p in ps for m in set(p.mots))
    moyenne = sum(len(p.mots) for p in ps) / max(len(ps), 1)
    return ps, df, moyenne


def chercher(question: str, n: int = 3, k1: float = 1.4, b: float = 0.75) -> list[tuple[float, Passage]]:
    ps, df, moyenne = _index()
    q = set(normaliser(question))
    scores = []
    for p in ps:
        tf = Counter(p.mots)
        s = 0.0
        for m in q:
            if m not in tf:
                continue
            idf = math.log(1 + (len(ps) - df[m] + 0.5) / (df[m] + 0.5))
            s += idf * tf[m] * (k1 + 1) / (tf[m] + k1 * (1 - b + b * len(p.mots) / moyenne))
        if s > 0:
            scores.append((s, p))
    scores.sort(key=lambda x: -x[0])
    return scores[:n]


def sources_de(ps: list[Passage]) -> list[dict]:
    vues, sortie = set(), []
    for p in ps:
        for r in p.references:
            s = _source(r)
            cle = (s["document"], s["page"])
            if cle not in vues:
                vues.add(cle)
                sortie.append(s)
    return sortie
