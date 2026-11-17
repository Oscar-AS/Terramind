"""Contrôle automatique « aller-retour » de la voix wolof (voir docs/voix-wolof.md § 7 ter).

Usage (depuis la racine, dans l'environnement .venv) :
    .venv/bin/python scripts/outils/controle_voix.py

Pour chaque texte :
1. normalisation (engine/app/responses/voix/normalisation.py) ;
2. synthèse avec AIHubSN/Kiriku-Wolof-TTS ;
3. retranscription avec AIHubSN/M-Kiriku-ASR ;
4. taux d'erreur sur les caractères (CER) ; statut « ok » si CER ≤ SEUIL, sinon « a_risque ».

Textes contrôlés :
- les mots du lexique qui ont une prononciation (content/voix/lexique_wolof.csv), **chacun dans une vraie
  phrase wolof qui le contient** (la plus courte trouvée dans les transcriptions validées puis le corpus écrit
  de Kallaama). Un mot isolé ne se teste pas : sur une demi-seconde d'audio, la reconnaissance invente
  (« hum hum »), constaté le 5 nov 2026. Le mot est « ok » si la reconnaissance le retrouve dans la phrase
  (meilleur passage avec CER ≤ SEUIL_MOT) ; « non_teste » s'il n'existe dans aucune phrase (ne bloque pas) ;
- les réponses types en wolof, dès qu'elles existent : content/templates/*.wo.txt (une réponse par ligne) ;
- les 30 questions de test D9 (research/questions_test_d9_wolof.csv), vraies phrases de Kallaama.

Sortie : content/voix/controle_voix.csv, lue par la normalisation : un mot du lexique « a_risque »
bloque la synthèse en direct (repli : réponse type enregistrée ou texte).

Limite : un mot isolé est plus difficile à retranscrire qu'une phrase ; un mot « a_risque » n'est pas
forcément mal prononcé, mais il mérite une écoute (complément) avant d'être utilisé en voix de synthèse.
"""

import csv
import datetime as dt
import sys
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "engine" / "app" / "responses" / "voix"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalisation as nz  # noqa: E402
from essai_voix_wolof import cer  # noqa: E402

VOIX = RACINE / "modeles" / "AIHubSN__Kiriku-Wolof-TTS"
ASR = RACINE / "modeles" / "AIHubSN__M-Kiriku-ASR"
SORTIE = RACINE / "content" / "voix" / "controle_voix.csv"
SEUIL = 0.20  # phrase entière
SEUIL_MOT = 0.34  # mot retrouvé dans la phrase (au plus 1 caractère faux sur 3)
KALLAAMA = RACINE / "data" / "raw" / "kallaama" / "data"


def phrases_kallaama():
    """Phrases réelles : transcriptions validées puis corpus écrit, nettoyées des balises d'annotation."""
    import glob
    import re

    for f in sorted(
        glob.glob(str(KALLAAMA / "transcriptions/checked/transcriptions-wol/stm/*.stm"))
    ):
        for ligne in open(f, encoding="utf-8"):
            parts = ligne.split(None, 6)
            if ligne.startswith(";;") or len(parts) < 7 or parts[2] == "excluded_region":
                continue
            s = re.sub(r"<[^>]*>|\[[^\]]*\]|%\w+|\(\([^)]*\)\)|\s*:fra\b", "", parts[6])
            yield " ".join(s.split())
    for ligne in open(KALLAAMA / "text_corpora/wolof.txt", encoding="utf-8"):
        yield " ".join(ligne.split())


def phrase_pour(mot, phrases):
    """Phrase la plus courte (5 à 15 mots, sans nom propre, chiffre ni guillemet) contenant le mot."""
    import re

    motif = re.compile(rf"(?<!\w){re.escape(mot.lower())}(?!\w)")
    meilleure = None
    for s in phrases:
        mots = s.split()
        if (
            not 5 <= len(mots) <= 15
            or re.search(r"[0-9\"«»()]", s)
            or any(m[:1].isupper() for m in mots[1:])
        ):
            continue
        if motif.search(s.lower()) and (meilleure is None or len(s) < len(meilleure)):
            meilleure = s
    return meilleure


def mot_retrouve(mot, entendu):
    """Meilleur CER entre le mot et un passage de même longueur (en mots, ±1) de la retranscription."""
    from essai_voix_wolof import cer as _cer

    cible = mot.lower().replace("-", " ").split()
    h = entendu.lower().replace("-", " ").split()
    meilleur = 9.0
    for n in {max(1, len(cible) - 1), len(cible), len(cible) + 1}:
        for i in range(0, max(1, len(h) - n + 1)):
            meilleur = min(meilleur, _cer(" ".join(cible), " ".join(h[i : i + n])))
    return round(meilleur, 3)


def textes():
    phrases = list(phrases_kallaama())
    for r in csv.DictReader(
        (RACINE / "content" / "voix" / "lexique_wolof.csv").open(encoding="utf-8")
    ):
        mot = r["a_dire_en_wolof"].strip()
        if mot:
            yield "lexique", r["ecrit"], mot, phrase_pour(mot, phrases)
    for f in sorted((RACINE / "content" / "templates").glob("*.wo.txt")):
        for k, ligne in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if ligne.strip():
                yield "reponse_type", f"{f.name}:{k}", ligne.strip(), None
    for r in csv.DictReader(
        (RACINE / "research" / "questions_test_d9_wolof.csv").open(encoding="utf-8")
    ):
        yield "question_d9", r["n"], r["question_wolof"], None


def main():
    import librosa
    from transformers import pipeline
    from TTS.utils.synthesizer import Synthesizer

    synth = Synthesizer(
        tts_checkpoint=str(VOIX / "model.pth"), tts_config_path=str(VOIX / "config.json")
    )
    asr = pipeline("automatic-speech-recognition", model=str(ASR), device="cpu")
    sr = synth.output_sample_rate
    lignes = []
    for type_, cle, texte, contexte in textes():
        if type_ == "lexique" and contexte is None:
            lignes.append([type_, cle, texte, "", "", "", "", "non_teste"])
            print(f"non_teste       lexique      {texte} (aucune phrase Kallaama ne le contient)")
            continue
        a_lire = contexte if type_ == "lexique" else texte
        pret = nz.preparer(a_lire, a_risque=set())
        lu = " ".join(pret.morceaux)
        audio = []
        for m in pret.morceaux:
            audio += list(synth.tts(text=m))
        audio16 = librosa.resample(np.array(audio, dtype=np.float32), orig_sr=sr, target_sr=16000)
        entendu = asr({"raw": audio16, "sampling_rate": 16000})["text"].strip()
        taux = round(cer(lu, entendu), 3)
        if type_ == "lexique":
            taux_mot = mot_retrouve(texte, entendu)
            statut = "ok" if taux_mot <= SEUIL_MOT else "a_risque"
        else:
            taux_mot = ""
            statut = "ok" if taux <= SEUIL else "a_risque"
        lignes.append([type_, cle, texte, lu, entendu, taux, taux_mot, statut])
        print(
            f"{statut:8} {taux:5.2f} {str(taux_mot):6} {type_:12} {texte[:14]:14} {lu[:50]:50} | {entendu[:45]}"
        )
    with SORTIE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["type", "cle", "texte", "texte_lu", "entendu", "cer_phrase", "cer_mot", "statut"]
        )
        w.writerows(lignes)
    n = len(lignes)
    ok = sum(1 for l in lignes if l[-1] == "ok")
    print(
        f"\n{ok}/{n} « ok » (phrases : CER ≤ {SEUIL} ; mots : CER ≤ {SEUIL_MOT} dans leur phrase) ; date {dt.date.today()} ; voix {VOIX.name} ; ASR {ASR.name}"
    )


if __name__ == "__main__":
    main()
