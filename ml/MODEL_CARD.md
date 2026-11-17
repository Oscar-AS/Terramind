# Fiche du modèle : Diagnostic

> Version complétée avec le découpage stratifié `terramind_v1` et la pipeline de fine-tuning. Les métriques d'évaluation finale (`ml/eval/metrics.json`) s'ajoutent dès la fin de l'exécution GPU Colab.

## Résumé
Modèle de classification d'images de feuilles (`224×224 px`) identifiant la culture et la maladie ou le ravageur probable parmi les classes de `terramind_v1` (TOM2024 Burkina Faso + CCMT Ghana), avec un score de confiance calibré et un seuil « incertain » au-dessous duquel le moteur refuse de diagnostiquer et oriente vers un agent agricole.

## Cultures couvertes
Liste fermée (voir [docs/decisions.md](../docs/decisions.md), D3 et D13) :
- **Dans `terramind_v1` (35 448 images, 38 classes foliaires + 2 classes fruits)** : `tomato` (tomate), `onion` (oignon), `maize` (maïs), `cassava` (manioc), `cashew` (cajou).
- **Compléments maraîchers (PlantVillage / PlantDoc / Chou Mendeley)** : `potato` (pomme de terre), `pepper` (poivron), `cabbage` (chou pommé).
- **Hors périmètre photo** (`carrot`, `chili`, `bitter_eggplant`) : reçoivent `culture non prise en charge` et un renvoi vers un agent agricole.

## Données
Jeux publics téléchargés le 2026-10-30 (provenance : [data/README.md](../data/README.md)). Les images restent hors Git, dans `data_local/raw/`.

### TOM2024 (Burkina Faso) : base de terrain
- Hugging Face `Project-AgML/TOM2024_disease_classification`, configuration `raw`, split `train`, commit `ce3661e` ; CC BY 4.0, attribution requise.
- 12 082 images, 24 classes : maïs 4 589, oignon 3 044, tomate 4 449.
- Contrôles : aucune ligne vide ; 0 image illisible.
- Limites : classes très petites retirées sous le seuil de 50 images (`aphids-p` 4, `alternaria-mite-d` 8, `fusarium-d` chez la tomate 18, `tuta-absoluta-p` 17, `bulb-blight-d` 29) ; les étiquettes mêlent maladies, ravageurs, stress et 2 classes de fruits.

### CCMT (Ghana) : base de terrain
- Raw Data uniquement (jamais la version augmentée) ; Mendeley Data DOI 10.17632/bwh3zbpkpv.1, téléchargé via Kaggle `irakozekelly/crop-pest-and-disease-dataset` ; CC BY 4.0, attribution requise.
- 25 220 images, 22 classes ; après nettoyage (décision D12) : 24 071 images, soit cajou 6 548, manioc 7 376, maïs 4 822, tomate 5 325.
- Contrôles : les 25 220 images ont été ouvertes ; empreintes de `Tomato/healthy` identiques à celles publiées par Mendeley.
- Limites : images déjà réduites à 400×400 px ; étiquettes peu fiables entre `leaf blight`, `leaf spot` et `streak virus` chez le maïs (voir D12).

### Base fusionnée terramind_v1 (décision D13) et découpage train / val / test
`data_local/processed/terramind_v1/` : `images/<culture>/<classe>/`, `manifest.csv`, `splits.csv`, `classes.csv`, `exclusions.csv`.
Reconstruction :
1. `python ml/training/build_merged_dataset.py`
2. `python ml/training/split_dataset.py`

35 448 images, 40 classes (38 classes de feuilles = 34 807 images ; 2 classes de fruits de la tomate = 641 images) :

| Culture | Sain | Maladie | Ravageur | Abiotique | Total | Train (80 %) | Val (10 %) | Test (10 %) |
|---|---|---|---|---|---|---|---|---|
| Cajou | 1 368 | 3 802 | 1 378 | – | 6 548 | 5 238 | 655 | 655 |
| Manioc | 1 193 | 5 169 | 1 014 | – | 7 376 | 5 904 | 736 | 736 |
| Maïs | 754 | 5 384 | 3 046 | 76 | 9 260 | 7 410 | 925 | 925 |
| Oignon | 660 | 1 416 | 758 | – | 2 834 | 2 266 | 284 | 284 |
| Tomate | 1 745 | 6 944 | 627 | 114 | 9 430 | 7 548 | 941 | 941 |
| **Total** | **5 720** | **22 715** | **6 823** | **190** | **35 448** | **28 366** | **3 541** | **3 541** |

Détail complet par classe et par split : [data/splits_terramind_v1.csv](../data/splits_terramind_v1.csv). Correspondance des étiquettes : [data/label_mapping.csv](../data/label_mapping.csv).

## Méthode
- **Architecture (Décision D5)** : Transfer learning / fine-tuning à partir de **`linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification`** (MobileNetV2 pré-entraîné sur PlantVillage, sous licence permissive) ou **`mobilenet_v3_large`** (`torchvision`, ImageNet-1K). Aucun composant sous licence AGPL (YOLOv8 écarté).
- **Entraînement (`ml/training/train_classifier.py` & `ml/notebooks/Colab_FineTuning_TerraMind_v1.ipynb`)** :
  - Option `--leaf-only` activée par défaut (exclut `healthy_fruit` et `blossom_end_rot` pour ne garder que les 38 classes foliaires, soit 34 807 images).
  - Redimensionnement systématique en `224×224 px` pour éliminer le biais de taille entre CCMT (`400×400`) et TOM2024.
  - Augmentation réservée au jeu `train` (`RandomResizedCrop`, `RandomHorizontalFlip`, `ColorJitter`). Aucune augmentation sur `val` ni `test`.
  - Fonction de perte `CrossEntropyLoss` pondérée en $1 / \sqrt{n_c}$ pour protéger les petites classes.
  - Fine-tuning en 2 étapes : tête seule gelée (2 époques, `lr = 1e-3`), puis déblocage complet avec `CosineAnnealingLR` (6 époques, `lr = 1e-4`).
- **Confiance et seuil « incertain » (`engine/app/modules/diagnostic/diagnostiqueur.py`)** :
  - Seuil par défaut : `0.60` (configurable via `DIAGNOSTIC_CONFIDENCE_THRESHOLD` et calibré sur `val`).
  - Seuil relevé à **`0.75`** pour les petites classes de moins de 100 images (`tomato/late_blight` [72], `maize/abiotic_disorder` [76], `maize/rust` [94]).
  - Sous le seuil : `statut = "incertain"`, `renvoi_agent = True`, aucune maladie annoncée.
  - Ravageurs absents ou sous-représentés en photo (*Tuta absoluta* sur tomate, *Plutella xylostella* sur chou) : couverts par la combinaison **alerte météo en degrés-jours + questions de suivi du manuel de la DPV** (`questions_suivi`).

## Métriques
Évaluation exécutée le **2026-11-17** sur l'intégralité du jeu de test stratifié de `terramind_v1` (**34 807 images foliaires** : `train = 27 853`, `val = 3 477`, `test = 3 477` sur les 38 classes foliaires, détail complet dans [ml/eval/metrics.json](eval/metrics.json)) :

| Jeu / Sous-ensemble | Métrique | Valeur | Date |
|---|---|---|---|
| **Test global (38 classes foliaires, `n = 3 477`)** | Exactitude Top-1 (toutes images) | **80,30 %** | 2026-11-17 |
| **Test filtré (`seuil_incertain = 0.60`)** | Exactitude hors réponses « incertain » | **83,60 %** (taux d'incertain : 10,24 %) | 2026-11-17 |
| **Test filtré strict (`seuil = 0.75`)** | Exactitude hors réponses « incertain » | **88,32 %** (taux d'incertain : 20,71 %) | 2026-11-17 |
| **Test filtré très haute confiance (`seuil = 0.90`)** | Exactitude hors réponses « incertain » | **93,05 %** (taux d'incertain : 35,06 %) | 2026-11-17 |
| **Par source : TOM2024 (Burkina Faso)** | Exactitude Top-1 (`n = 1 074`) | **81,84 %** | 2026-11-17 |
| **Par source : CCMT (Ghana)** | Exactitude Top-1 (`n = 2 403`) | **79,61 %** | 2026-11-17 |
| **Par culture : Cajou (`cashew`)** | Exactitude Top-1 (`n = 655`, 5 classes) | **89,47 %** | 2026-11-17 |
| **Par culture : Maïs (`maize`)** | Exactitude Top-1 (`n = 925`, 12 classes) | **83,35 %** (Chenille légionnaire : 87,5 %, Stries : 94,4 %) | 2026-11-17 |
| **Par culture : Manioc (`cassava`)** | Exactitude Top-1 (`n = 736`, 5 classes) | **82,47 %** (Sain : 96,6 %, Mosaïque : 85,6 %) | 2026-11-17 |
| **Par culture : Oignon (`onion`)** | Exactitude Top-1 (`n = 284`, 5 classes) | **81,34 %** (Chenilles : 94,7 %, Fusariose : 83,3 %, Sain : 83,3 %) | 2026-11-17 |
| **Par culture : Tomate (`tomato`)** | Exactitude Top-1 (`n = 877`, 11 classes foliaires) | **68,07 %** (Virose : 86,6 %, Mildiou : 85,7 %, Sain : 77,9 %, Septoriose : 71,6 %) | 2026-11-17 |

## Limites
- **Biais de source** : la majorité des classes ne proviennent que d'un seul des deux jeux (TOM2024 ou CCMT). Même après redimensionnement à `224×224 px`, le fond et l'appareil photo diffèrent selon le pays d'origine (Burkina Faso vs Ghana).
- **Ravageurs** : *Tuta absoluta* (17 images dans TOM2024) et *Plutella xylostella* (0 image) ne sont pas reconnus sur photo seule ; leur détection repose sur `questions_suivi` (DPV) et `/v1/alert` (degrés-jours).
- **Petites classes** : mildiou de la tomate (58 train / 7 val / 7 test), trouble abiotique du maïs (60 / 8 / 8) et rouille du maïs (76 / 9 / 9) ont des intervalles de confiance larges en test et sont soumises au seuil strict `0.75`.

## Usage prévu et hors périmètre
- **Usage prévu** : aide à l'orientation préliminaire pour les maraîchers du Sénégal sur WhatsApp et PWA, accompagnée de conseils culturaux préventifs sourcés.
- **Hors périmètre** : prescription de produits phytosanitaires ou de dosages chimiques (strictement interdite dans tout le système) ; diagnostic sur racines, tiges internes ou semences.
