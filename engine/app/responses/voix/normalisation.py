"""Préparation d'un texte wolof avant la synthèse vocale (voir docs/voix-wolof.md).

La voix de synthèse wolof lit mal les chiffres, les symboles et les mots
français, et dérape sur les phrases trop longues ou sans ponctuation finale.
Ce module :
1. retire ce qui ne doit pas être lu (sources entre crochets, liens, émojis,
   mise en forme) ;
2. écrit les nombres entiers en toutes lettres en wolof ;
3. remplace les mots du lexique (unités, mois, noms de cultures…) ;
4. signale tout ce qu'il ne sait pas traiter (décimales, mot français,
   symbole, entrée de lexique non remplie) ;
5. découpe le texte en morceaux courts, chacun terminé par une ponctuation, en minuscules
   (la voix wolof ignore les majuscules).

Règle d'usage : si `problemes` n'est pas vide, on ne synthétise PAS en direct ;
on passe au repli (réponse type enregistrée, ou texte).

Le lexique (content/voix/lexique_wolof.csv) est à valider par un locuteur :
les entrées « a_remplir » sont ignorées et signalées si le mot apparaît.
"""

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

LEXIQUE = Path(__file__).resolve().parents[4] / "content" / "voix" / "lexique_wolof.csv"

TAILLE_MAX = 160   # caractères par morceau envoyé à la synthèse
TAILLE_MIN = 30    # en dessous, on fusionne avec le morceau voisin

# Petits mots français fréquents : leur présence dans un texte censé être en
# wolof indique un mélange de langues que la voix lira mal.
MOTS_FRANCAIS = {"le", "la", "les", "des", "du", "et", "pour", "avec", "dans", "est", "une", "un",
                 "sur", "pas", "vous", "votre", "il", "elle", "qui", "que", "au", "aux"}


@dataclass
class TextePret:
    morceaux: list = field(default_factory=list)   # texte à synthétiser, morceau par morceau
    problemes: list = field(default_factory=list)  # raisons de ne pas synthétiser en direct

    @property
    def synthetisable(self):
        return bool(self.morceaux) and not self.problemes


def charger_lexique(chemin=LEXIQUE):
    chiffres, bases, mots, a_remplir = {}, {}, {}, set()
    with open(chemin, encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            ecrit, dit = ligne["ecrit"].strip(), ligne["a_dire_en_wolof"].strip()
            if ligne["type"] == "chiffre":
                chiffres[int(ecrit)] = dit
            elif ligne["type"] == "base":
                bases[int(ecrit)] = dit
            elif ligne["type"] == "liaison":
                bases["ak"] = dit
            elif ligne["type"] == "mot":
                (mots.__setitem__(ecrit.lower(), dit) if dit else a_remplir.add(ecrit.lower()))
    return chiffres, bases, mots, a_remplir


def nombre_en_wolof(n, chiffres, bases):
    """Entier de 0 à 999 999 en toutes lettres, selon le système décrit par les sources du lexique :
    6 à 9 = cinq + unité ; dizaines = multiplicateur + « fukk » ; centaines et milliers =
    multiplicateur suffixé par « -i » + « téeméer » / « junni » ; parties liées par « ak »."""
    if not 0 <= n <= 999_999:
        raise ValueError("nombre hors plage")
    if n < 10:
        return chiffres[n]
    ak, fukk, teemeer, junni = bases["ak"], bases[10], bases[100], bases[1000]
    parties = []
    milliers, reste = divmod(n, 1000)
    if milliers:
        parties.append(junni if milliers == 1 else f"{_multiplicateur(milliers, chiffres, bases)}i {junni}")
    centaines, reste = divmod(reste, 100)
    if centaines:
        parties.append(teemeer if centaines == 1 else f"{chiffres[centaines]}i {teemeer}")
    dizaines, unites = divmod(reste, 10)
    if dizaines:
        parties.append(fukk if dizaines == 1 else f"{chiffres[dizaines]} {fukk}")
    if unites:
        parties.append(chiffres[unites])
    return f" {ak} ".join(parties)


def _multiplicateur(n, chiffres, bases):
    # « ñaari junni » (2 000) ; au-delà de 9, on écrit le nombre complet devant « -i junni ».
    return chiffres[n] if n < 10 else nombre_en_wolof(n, chiffres, bases)


def preparer(texte, lexique=None):
    chiffres, bases, mots, a_remplir = lexique or charger_lexique()
    resultat = TextePret()

    t = re.sub(r"\[[^\]]*\]", " ", texte)                    # sources [Guide 1987, p. 140]
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)              # liens
    t = re.sub(r"[*_#>`]", " ", t)                            # mise en forme
    t = "".join(c for c in t if unicodedata.category(c) not in ("So", "Sk", "Cs"))  # émojis

    if re.search(r"\d+[.,]\d+", t):
        resultat.problemes.append("nombre décimal : à reformuler (arrondir ou dire en mots)")

    for ecrit in sorted(mots, key=len, reverse=True):         # mots du lexique (unités, mois…)
        t = re.sub(rf"(?<!\w){re.escape(ecrit)}(?!\w)", mots[ecrit], t, flags=re.IGNORECASE)
    for ecrit in a_remplir:
        if re.search(rf"(?<!\w){re.escape(ecrit)}(?!\w)", t, flags=re.IGNORECASE):
            resultat.problemes.append(f"« {ecrit} » : prononciation wolof absente du lexique")

    def en_lettres(m):
        valeur = int(m.group(0).replace(" ", ""))
        try:
            return nombre_en_wolof(valeur, chiffres, bases)
        except ValueError:
            resultat.problemes.append(f"nombre trop grand : {m.group(0)}")
            return m.group(0)
    t = re.sub(r"\d{1,3}(?: \d{3})+|\d+", en_lettres, t)

    restes = sorted(set(re.findall(r"[%°/=+<>&@€$]", t)))
    if restes:
        resultat.problemes.append(f"symboles non lus correctement : {' '.join(restes)}")
    francais = sorted({m for m in re.findall(r"[a-zàâçéèêëîïôûùüÿœ]+", t.lower()) if m in MOTS_FRANCAIS})
    if francais:
        resultat.problemes.append(f"mots français dans le texte wolof : {', '.join(francais)}")

    t = re.sub(r"\s+", " ", t).strip()
    # La voix wolof (Kiriku-Wolof-TTS) n'a appris que des minuscules : une majuscule est ignorée,
    # ce qui fait disparaître la première lettre de la phrase (constaté à l'essai du 4 nov 2026).
    resultat.morceaux = [m.lower() for m in decouper(t)]
    return resultat


def decouper(texte):
    """Morceaux de TAILLE_MAX caractères au plus, coupés aux fins de phrase puis aux virgules,
    fusion des morceaux trop courts, ponctuation finale garantie (limite les dérapages de la voix)."""
    phrases = [p.strip() for p in re.split(r"(?<=[.!?;])\s+", texte) if p.strip()]
    morceaux = []
    for p in phrases:
        while len(p) > TAILLE_MAX:
            coupe = p.rfind(",", 0, TAILLE_MAX)
            coupe = coupe if coupe > TAILLE_MIN else p.rfind(" ", 0, TAILLE_MAX)
            morceaux.append(p[:coupe + 1].strip())
            p = p[coupe + 1:].strip()
        morceaux.append(p)
    fusionnes = []
    for m in morceaux:
        if fusionnes and (len(m) < TAILLE_MIN or len(fusionnes[-1]) < TAILLE_MIN) \
                and len(fusionnes[-1]) + len(m) + 1 <= TAILLE_MAX:
            fusionnes[-1] = f"{fusionnes[-1]} {m}"
        else:
            fusionnes.append(m)
    return [m if m[-1] in ".!?" else (m[:-1] if m[-1] in ",;:" else m) + "." for m in fusionnes]
