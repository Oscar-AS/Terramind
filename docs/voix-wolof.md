# Voix wolof : limiter les défauts de la synthèse vocale

Décisions liées : D8, D9, D10 dans [decisions.md](decisions.md). Rédigé le 2 nov 2026.

La réponse en wolof part d'abord en message vocal (D10). La voix de synthèse wolof envisagée (`galsenai/xTTS-v2-wolof`) a trois défauts connus, relevés dans le dossier de conception et sur sa page Hugging Face : elle lit mal les chiffres et les mots français, elle fait des pauses aléatoires, et le modèle pèse plus de 7 Go (lenteur). Ce document décrit les parades techniques, à mettre en place dès les premiers tests.

Principe général : **on ne fait jamais confiance à une seule brique**. Chaque étape a un contrôle et un repli, et l'agriculteur reçoit toujours quelque chose de juste, quitte à être moins riche.

---

## 1. La chaîne et ses replis

Pour chaque réponse en wolof, le moteur essaie dans cet ordre et s'arrête au premier qui réussit :

| Ordre | Source de l'audio | Quand | Qualité | Délai |
|---|---|---|---|---|
| 1 | **Enregistrement humain** d'une réponse type (`content/audio/wo/`) | Cas sensibles : diagnostic incertain, alertes, « je ne sais pas », accueil, attente | La meilleure | Immédiat |
| 2 | **Cache** : audio déjà produit pour exactement le même texte | Réponses fréquentes (calendrier, symptômes courants) | Déjà contrôlée | Immédiat |
| 3 | **Synthèse en direct** (xTTS-v2 wolof) | Le texte a passé la normalisation sans problème (§ 2) | Bonne si contrôlée (§ 3, 4) | À mesurer |
| 4 | **Voix de secours** plus légère (candidat : `bilalfaye/speecht5_tts-wolof`, licence MIT, à tester) | Synthèse principale en panne ou trop lente | Moindre | Court |
| 5 | **Message vocal enregistré** « je n'ai pas pu préparer la réponse vocale, un agent peut t'aider » + texte en français | Tout le reste a échoué | Minimale mais honnête | Immédiat |

Le cache (2) utilise comme clé l'empreinte du texte normalisé + identifiant de la voix + version du modèle. On précalcule hors ligne les réponses les plus probables (fiches de la liste fermée de cultures) pour que la plupart des réponses viennent du cache.

## 2. Côté texte : préparer ce que la voix va lire

### 2.1 Demander au modèle un texte « pour l'oreille »
La consigne envoyée au modèle qui rédige en wolof (D9) impose :
- 3 à 5 phrases courtes, chacune terminée par un point ;
- **aucun chiffre** : nombres et dates en toutes lettres ;
- aucun symbole (%, °C, /), aucune abréviation, aucune source entre crochets ;
- **aucun mot français** quand un mot wolof existe ; sinon le mot du lexique (§ 2.3) ;
- pas de nombre décimal : arrondir (« environ deux kilos et demi » plutôt que « 2,5 kg »).

### 2.2 Normaliser automatiquement
Module : [engine/app/responses/voix/normalisation.py](../engine/app/responses/voix/normalisation.py), tests dans `engine/tests/test_normalisation_wolof.py` (`python3 -m unittest discover engine/tests`).

Il retire les sources, liens, émojis et la mise en forme, écrit les nombres entiers (0 à 999 999) en wolof selon le système décrit par les sources, remplace les mots du lexique, puis **signale** ce qu'il ne sait pas traiter : décimales, symboles restants, mots français, mot du lexique sans prononciation renseignée.

**Règle de sécurité : s'il y a un problème, on ne synthétise pas en direct**, on passe au repli suivant (§ 1). Mieux vaut une réponse type enregistrée qu'une voix qui lit « deux virgule cinq kagé ».

### 2.3 Lexique de prononciation
Fichier [content/voix/lexique_wolof.csv](../content/voix/lexique_wolof.csv). Les chiffres et les bases (dix, cent, mille) viennent de sources publiques (jangawolof.org, Boston University « 200 words ») et restent **à valider par un locuteur** (les sources divergent sur les traits d'union et les accents). Les unités, les mois, les noms de cultures et les sigles sont **à remplir par un locuteur** : tant qu'une entrée est vide, le mot correspondant bloque la synthèse en direct.

## 3. Côté audio : corriger les pauses et les dérapages

Recettes relevées dans la documentation de xTTS et les retours d'autres équipes qui l'ont adapté à une langue (liens en bas) :
- **Découper soi-même** le texte en morceaux de 160 caractères au plus (le modèle a une limite de contexte d'environ 250 caractères), coupés aux fins de phrase puis aux virgules, en fusionnant les morceaux de moins de 30 caractères. Chaque morceau se termine par une ponctuation : les phrases sans ponctuation finale font davantage « halluciner » la voix. (Déjà fait par `decouper()`.)
- **Synthétiser chaque morceau séparément**, puis les assembler avec un **silence fixe de 0,4 s** entre phrases.
- **Comprimer les silences internes** : tout silence de plus de 350 ms est ramené à 350 ms ; couper le silence de fin. C'est la parade aux pauses aléatoires (la page de l'adaptation wolof recommande elle-même un script de suppression des silences).
- **Réglages de génération plus stables** : température basse (0,3 à 0,55), `repetition_penalty` élevé, `length_penalty` inférieur à 1, et décodage glouton (`do_sample=False`) à comparer ; vitesse proche de 1,0. Les valeurs exactes se fixent au test (§ 5).
- **Couper les fins hallucinées** : si un morceau dure nettement plus que prévu pour son nombre de caractères, on tronque ou on régénère (§ 4).
- **Volume homogène** (normalisation de la sonie), puis conversion en **OGG/Opus mono** (format des notes vocales WhatsApp), viser moins de 100 Ko par réponse comme prévu dans le dossier.

## 4. Contrôle automatique avant envoi

Deux vérifications sur chaque audio produit en direct :
1. **Durée plausible** : rapport durée / nombre de caractères dans une fourchette mesurée sur des exemples validés. Hors fourchette = pause anormale ou fin hallucinée.
2. **Aller-retour par la reconnaissance vocale** : on retranscrit l'audio avec le modèle de reconnaissance wolof (Kiriku, whosper ou dofbi, D8) et on compare au texte de départ (taux d'erreur sur les caractères). Si l'écart dépasse le seuil, on régénère une fois avec d'autres réglages, puis on passe au repli.

Ces contrôles ne remplacent pas l'écoute humaine, mais ils attrapent les ratés grossiers sans personne derrière.

## 5. Temps de réponse (modèle de plus de 7 Go)

- **Ne jamais faire attendre l'agriculteur dans le silence** : dès qu'une question vocale arrive, le bot renvoie un court message vocal d'attente **enregistré** (réponse type), puis la réponse quand elle est prête. WhatsApp permet d'envoyer plusieurs messages de suite.
- **Synthèse hors du serveur principal** : un service séparé, sur processeur graphique, chargé une fois et gardé « chaud » (modèle en demi-précision). Le moteur FastAPI lui envoie les morceaux en parallèle.
- **Cache et précalcul** (§ 1) pour que la synthèse en direct reste l'exception.
- **Réponses courtes** : objectif 30 secondes d'audio au plus.
- **Mesures dès la première semaine de test** : délai médian et au 95ᵉ centile, temps de calcul par seconde d'audio, coût par réponse, sur processeur graphique et sur processeur classique.

## 6. Protocole de test (à faire avant de brancher la voix)

- **Corpus** : 30 phrases wolof réelles, dont 10 avec nombres et dates, 10 avec des mots d'origine française (noms de cultures, mois), 10 phrases longues.
- **Écoute** par au moins 2 locuteurs : note de 1 à 5 sur « compris », « correct », « naturel » ; relevé des pauses bizarres.
- **Comparaison** : xTTS-v2 wolof (GalsenAI), son adaptation `muhamadul/xtts-v2-wolof`, la voix SpeechT5 wolof, avec et sans normalisation, avec les différents réglages du § 3.
- **Résultat attendu** : réglages retenus, seuils des contrôles du § 4, liste des mots à ajouter au lexique, temps de réponse mesurés. Consigné dans `docs/sources/` ou un rapport hebdomadaire.

## 7. Licences (à vérifier avant tout usage hors démonstration)

- `galsenai/xTTS-v2-wolof` : accès sur demande, aucune licence indiquée sur la page ; mentionner GalsenAI. Le modèle de base XTTS-v2 de Coqui est diffusé sous une licence qui restreint l'usage commercial (à confirmer) : acceptable pour le prototype, à revoir pour une exploitation.
- `bilalfaye/speecht5_tts-wolof` : licence MIT annoncée, à confirmer.
- Il n'existe apparemment pas de voix wolof dans la collection MMS-TTS de Meta (selon un dépôt tiers ; à confirmer) ; les voix MMS sont de toute façon en CC BY-NC 4.0.

## 7 bis. Accès aux modèles (vérifié le 2 nov 2026 sur l'API Hugging Face)

| Modèle | Rôle | Accès | Licence affichée |
|---|---|---|---|
| `AIHubSN/Kiriku-Wolof-ASR` (base Whisper large-v2) | Reconnaissance vocale | Sur demande (« gated ») : accepter les conditions sur la page, avec un compte Hugging Face | Apache 2.0 |
| `AIHubSN/M-Kiriku-ASR` (base Whisper large-v3) | Reconnaissance vocale, plus récente | Sur demande | Apache 2.0 |
| `AIHubSN/Kiriku-Wolof-TTS` | **Voix de synthèse wolof, nouvelle piste** à ajouter au test d'écoute (§ 6) | Sur demande | Non indiquée |
| `galsenai/xTTS-v2-wolof` | Voix de synthèse | Sur demande | Non indiquée (base XTTS-v2 de Coqui) |
| `CAYTU/whosper-large-v2` | Reconnaissance vocale | Libre | Apache 2.0 |
| `dofbi/wolof-asr` | Reconnaissance vocale | Libre | MIT |
| `bilalfaye/speecht5_tts-wolof-v0.2` | Voix de secours | Libre | MIT |
| Corpus Kallaama (copies `yigagilbert/kallaama-trs-dataset-19hr`, `KeraCare/Wolof-Kallaama`…) | Ajustement de la reconnaissance | Libre | À vérifier sur chaque copie et sur la publication d'origine |

Téléchargement en local (`modeles/`, exclu de Git) : `python3 scripts/outils/telecharger_modeles.py` (M-Kiriku-ASR, dofbi/wolof-asr, Kiriku-Wolof-TTS, SpeechT5 wolof ; environ 8,8 Go).

Les demandes d'accès se font avec un compte Hugging Face de l'équipe ; le jeton Hugging Face va dans `.env` (`HF_TOKEN`), jamais dans le code.

**Accès vérifiés le 4 nov 2026** (compte de Salam, jeton en lecture) : les 4 modèles sur demande sont ouverts. Test : un fichier du modèle se lit avec le jeton (HTTP 200) et pas sans (401).

| Modèle | Taille | Remarque |
|---|---|---|
| `AIHubSN/Kiriku-Wolof-ASR` | 6,2 Go | Licence Apache 2.0 |
| `AIHubSN/M-Kiriku-ASR` | 6,2 Go | Licence Apache 2.0 |
| `AIHubSN/Kiriku-Wolof-TTS` | **1,0 Go** | Licence non indiquée. **Sept fois plus léger que la voix GalsenAI : à tester en premier.** VITS (Coqui TTS 0.19), une seule voix, 22 050 Hz, entraîné directement sur l'écriture wolof (pas de phonétiseur) : il lit ce qu'on lui écrit, d'où l'importance de notre normalisation (nombres en toutes lettres, lexique). Aucune mesure de qualité publiée. Le fichier `model.pth` est un fichier « pickle » de PyTorch : ne le charger que depuis cette source vérifiée |
| `galsenai/xTTS-v2-wolof` | plus de 7 Go | **Les poids ne sont pas sur Hugging Face** : la page ne contient qu'un identifiant Google Drive (`checkpoint-id.yml`), à télécharger avec `gdown`. Elle demande aussi une version modifiée de la bibliothèque TTS, fournie dans le dépôt GitHub `Galsenaicommunity/Wolof-TTS`. Conditions : respecter la loi sénégalaise ; la voix peut imiter n'importe qui à partir de 6 s d'audio, ce qui oblige à utiliser seulement une voix dont on a le consentement |

## 7 ter. Premier essai d'écoute et contrôle automatique (4 nov 2026)

Script : `.venv/bin/python scripts/outils/essai_voix_wolof.py`. Environnement : `scripts/outils/requirements-voix.txt`. Les fichiers audio sont dans `modeles/essais/`, hors Git.

**Méthode :**
- 5 phrases **non inventées** : l'exemple de la fiche du modèle et 4 phrases du livret PIESAN sur l'oignon (2022, bilingue) ;
- passage par la normalisation, puis synthèse avec Kiriku-Wolof-TTS ;
- retranscription avec M-Kiriku-ASR, et calcul du taux d'erreur sur les caractères (CER) entre le texte lu et le texte entendu.

| # | Texte lu (après normalisation) | Entendu par M-Kiriku | CER |
|---|---|---|---|
| 1 | salamalekum, na nga def. | salaamaalekum na nga def | 0,09 |
| 2 | suxatal juróom ba juróom-benn liitar ci meetar kaare bune, subba teel walla bu jant buy so. | soxatal juróom ba juróom benn liitar ci meeta kaare bu suba teel wala bu jant buy so | 0,08 |
| 3 | moytu leen ba fàaw iire ci mbayum sople. | moytuleen ba faa yiir ci mbayum sopp | 0,18 |
| 4 | néemeeku gàancax gi ngir fagaru ci feebar yi ak gunóor yi. | nemmeeku gàncax gi dafa garu ci feebar yi ak gunóor yi | 0,16 |
| 5 | bàayil sople bi ci tool bi mu wow benn ba ñaari fan. | bàyyil sopp bi ci tool bi mu wow benn ba ñaari fan | 0,06 |

**Ce qu'on en tire :**
- **Vitesse.** Sur un Mac sans carte graphique, 1 seconde d'audio se calcule en 0,1 seconde environ. La voix Kiriku (1 Go) lève la crainte de lenteur liée au modèle GalsenAI de 7 Go.
- **Défaut corrigé.** Le modèle ne connaît pas les majuscules et supprimait la première lettre de chaque phrase. La normalisation met désormais tout en minuscules, et un test le vérifie.
- **Mot à risque repéré automatiquement :** « sople » (oignon) est entendu « sopp » dans les 3 phrases où il apparaît. À traiter : soit l'écrire autrement pour la voix, soit le faire écouter par un locuteur (complément), soit l'éviter en voix de synthèse.
- **Limites.** Un CER faible prouve que la reconnaissance retrouve le texte, pas qu'un agriculteur comprend sans effort. Les deux modèles viennent du même laboratoire (AIHubSN) et peuvent partager les mêmes biais. Le modèle léger dofbi donne un CER plus élevé (0,16 à 0,41) sur les mêmes audios : on utilise M-Kiriku comme juge.
- **Seuil proposé** pour le contrôle automatique, à confirmer sur plus de phrases : CER ≤ 0,20 = acceptable ; au-delà, la phrase ne part pas en voix de synthèse.

## 8. Qui fait quoi

| Tâche | Qui | Quand |
|---|---|---|
| Remplir et valider le lexique de prononciation avec un locuteur | Rama | avant le 10 nov |
| Enregistrer les réponses types sensibles et le message d'attente | Rama | 12 nov (tâche « audios wolof ») |
| Service de synthèse, cache, chaîne de replis, conversion OGG | Salam | 10-13 nov |
| Réglages de génération, contrôles automatiques (§ 4), mesures (§ 5) | Oscar | test optionnel du 14 nov, à avancer si possible |
| Test d'écoute (§ 6) | Rama et 2 locuteurs | dès que la voix tourne |

## Sources

- Dossier de conception TerraMind (sections 08, 11, 13, risques).
- [galsenai/xTTS-v2-wolof](https://huggingface.co/galsenai/xTTS-v2-wolof) (pauses aléatoires, script de suppression des silences, réglages).
- [Documentation XTTS (Coqui)](https://docs.coqui.ai/en/latest/models/xtts.html) et [coqui-tts](https://coqui-tts.readthedocs.io/en/latest/models/xtts.html) : découpage du texte, température, vitesse.
- [Discussion coqui-ai/TTS #4146](https://github.com/coqui-ai/TTS/discussions/4146) : hallucinations en fin de phrase, ponctuation finale.
- [Adaptation arabe de XTTS-v2](https://huggingface.co/Moeeldouma/arabic-tts-xtts-v2) : découpage, plafonnement des silences à 350 ms, pause fixe de 0,4 s.
- Nombres en wolof : [jangawolof.org](https://jangawolof.org/numbers/), [Comprendre les nombres wolof](https://jangawolof.org/understanding-wolof-numbers-counting-in-wolof/), [Boston University, 200 words](https://www.bu.edu/200word/wolof/numbers).
- Voix de secours : [bilalfaye/speecht5_tts-wolof-v0.2](https://huggingface.co/bilalfaye/speecht5_tts-wolof-v0.2), [muhamadul/xtts-v2-wolof](https://huggingface.co/muhamadul) ; absence de MMS wolof : [rnjema-unima/mms-tts-wol-baseline](https://huggingface.co/rnjema-unima/mms-tts-wol-baseline).
