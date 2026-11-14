"""Premier essai d'écoute de la voix wolof, avec contrôle automatique « aller-retour ».

Usage (depuis la racine, dans l'environnement .venv qui contient Coqui TTS 0.19) :
    .venv/bin/python scripts/outils/essai_voix_wolof.py

Pour chaque phrase :
1. normalisation (engine/app/responses/voix/normalisation.py) : nombres en toutes lettres,
   lexique, découpage ;
2. synthèse avec AIHubSN/Kiriku-Wolof-TTS (modeles/) -> fichier WAV ;
3. retranscription de l'audio avec un modèle de reconnaissance wolof (modeles/) ;
4. taux d'erreur sur les caractères (CER) entre le texte lu et le texte retranscrit.

Les phrases ne sont pas inventées : elles viennent du livret PIESAN (ministère de
l'Agriculture, 2022, bilingue français-wolof) et de l'exemple de la fiche du modèle.
Les WAV vont dans modeles/essais/ (exclu de Git).
"""

import csv
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "engine" / "app" / "responses" / "voix"))
import normalisation as nz  # noqa: E402

VOIX = RACINE / "modeles" / "AIHubSN__Kiriku-Wolof-TTS"
ASR = [RACINE / "modeles" / "AIHubSN__M-Kiriku-ASR", RACINE / "modeles" / "dofbi__wolof-asr"]
SORTIE = RACINE / "modeles" / "essais"

PHRASES = [  # (source, texte wolof)
    ("Fiche du modèle Kiriku-Wolof-TTS", "Salamalekum, na nga def."),
    ("Livret PIESAN oignon 2022, p. 11", "Suxatal 5 ba 6 liitar ci meetar kaare bune, subba teel walla bu jant buy so."),
    ("Livret PIESAN oignon 2022, p. 17", "Moytu leen ba fàaw iire ci mbayum sople."),
    ("Livret PIESAN oignon 2022, p. 23", "Néemeeku gàancax gi ngir fagaru ci feebar yi ak gunóor yi."),
    ("Livret PIESAN oignon 2022, p. 26", "Bàayil sople bi ci tool bi mu wow benn ba ñaari fan."),
]


def cer(ref, hyp):
    """Taux d'erreur sur les caractères (distance d'édition / longueur de la référence), sans ponctuation."""
    def nettoie(s):
        return " ".join("".join(c for c in s.lower() if c.isalnum() or c.isspace()).split())
    a, b = nettoie(ref), nettoie(hyp)
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prec, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            prec, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prec + (ca != cb))
    return d[len(b)] / max(1, len(a))


def main():
    from TTS.utils.synthesizer import Synthesizer
    SORTIE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    synth = Synthesizer(tts_checkpoint=str(VOIX / "model.pth"), tts_config_path=str(VOIX / "config.json"))
    print(f"Voix chargée en {time.time() - t0:.1f} s")

    resultats = []
    for k, (source, texte) in enumerate(PHRASES, 1):
        pret = nz.preparer(texte)
        lu = " ".join(pret.morceaux)
        t = time.time()
        audio = []
        for morceau in pret.morceaux:
            audio += list(synth.tts(text=morceau))
            audio += [0.0] * int(0.4 * synth.output_sample_rate)  # pause fixe entre morceaux
        duree_calcul = time.time() - t
        fichier = SORTIE / f"essai_{k}.wav"
        sf.write(fichier, np.array(audio, dtype=np.float32), synth.output_sample_rate)
        duree_audio = len(audio) / synth.output_sample_rate
        resultats.append({"n": k, "source": source, "texte_lu": lu, "problemes": "; ".join(pret.problemes),
                          "fichier": fichier.name, "duree_audio_s": round(duree_audio, 1),
                          "calcul_s": round(duree_calcul, 1)})
        print(f"{k}. {lu}\n   -> {fichier.name} ({duree_audio:.1f} s d'audio, calculé en {duree_calcul:.1f} s)"
              + (f"\n   problèmes signalés : {pret.problemes}" if pret.problemes else ""))

    # Aller-retour : retranscription par le premier modèle de reconnaissance qui se charge.
    try:
        from transformers import pipeline
        asr, nom_asr = None, None
        for chemin in ASR:
            try:
                asr = pipeline("automatic-speech-recognition", model=str(chemin), device="cpu")
                nom_asr = chemin.name
                break
            except Exception as e:  # version de transformers trop ancienne, etc.
                print(f"Reconnaissance {chemin.name} non chargée : {type(e).__name__}: {str(e)[:160]}")
        if asr:
            print(f"\nAller-retour avec {nom_asr}")
            for r in resultats:
                audio, sr = sf.read(SORTIE / r["fichier"])
                import librosa
                audio16 = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=16000)
                hyp = asr({"raw": audio16, "sampling_rate": 16000})["text"].strip()
                r["retranscrit"], r["cer"] = hyp, round(cer(r["texte_lu"], hyp), 3)
                r["asr"] = nom_asr
                print(f"{r['n']}. CER {r['cer']:.2f} | entendu : {hyp}")
    except ImportError:
        print("transformers absent : pas d'aller-retour")

    with (SORTIE / "resultats.csv").open("w", newline="", encoding="utf-8") as f:
        champs = ["n", "source", "texte_lu", "problemes", "fichier", "duree_audio_s", "calcul_s", "asr",
                  "retranscrit", "cer"]
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(resultats)
    print(f"\nRésultats : {(SORTIE / 'resultats.csv').relative_to(RACINE)}")


if __name__ == "__main__":
    main()
