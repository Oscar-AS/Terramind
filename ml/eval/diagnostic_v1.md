# Modèle de diagnostic v1 : résultats (13 nov 2026)

**Modèle déployé : MobileNetV3-Large v1** (`ml/training/entrainer_diagnostic_v1.py --arch mobilenet_v3_large`). Métriques complètes : [diagnostic_v1_mobilenet_v3_large.json](diagnostic_v1_mobilenet_v3_large.json). Version précédente : [diagnostic_v0.md](diagnostic_v0.md).

## Ce qui change par rapport à la v0

| | v0 | v1 |
|---|---|---|
| Données | PlantVillage + PlantDoc | + **TOM2024** (Burkina Faso, photos de terrain, tomate et oignon), PlantVillage réduit à 600 images par classe |
| Classes | 15 (tomate, pomme de terre, poivron) | **26**, dont **5 pour l'oignon** et des ravageurs (chenilles, noctuelle) |
| Choix de l'époque | validation labo | **validation terrain** (1 291 photos : 20 % de PlantDoc entraînement + 15 % de TOM2024) |
| Calibration | aucune | température 0,81 apprise sur la validation terrain |
| Augmentations | standard | plus fortes (recadrage serré, flou, effacement), échantillonnage équilibré entre classes |

## Résultats

| Jeu (jamais vu à l'entraînement) | Images | v0 | **v1** |
|---|---|---|---|
| Validation terrain (choix de l'époque) | 1 291 | — | 84,2 % |
| **Test TOM2024** (photos de terrain africaines) | 1 058 | — | **91,7 %** |
| Test PlantDoc (photos du web, très variées) | 102 | 54,9 % | 56,9 % |

- Sur les photos de terrain africaines, le modèle est bon : oignon sain 99 %, chenilles de l'oignon 100 %, fusariose de l'oignon 95 %, virose de la tomate 90 %.
- **Points faibles** : mildiou de la tomate (50 % sur TOM2024, seulement 74 images d'entraînement), acariens (71 %), et en général les photos de type PlantDoc (fonds variés, plusieurs feuilles, images du web).

## Seuil d'incertitude : 0,6

| Seuil | Validation terrain | Test TOM2024 | Test PlantDoc |
|---|---|---|---|
| 0,4 | 97 % couverts, 86 % justes | 99 %, 92 % | 84 %, 62 % |
| **0,6** | **90 %, 90 %** | **93 %, 94 %** | **60 %, 72 %** |
| 0,8 | 80 %, 93 % | 86 %, 96 % | 33 %, 65 % |

La règle automatique du script (« plus petit seuil donnant 85 % de réponses justes en validation ») donnait 0,4. Nous avons retenu **0,6**, plus prudent, parce que la validation est dominée par les photos TOM2024, plus faciles. **Limite** : ce choix a été fait après avoir vu les tests. Les chiffres des tests au seuil 0,6 sont donc légèrement optimistes.

Garde-fous inchangés : sous le seuil, aucune maladie n'est nommée ; au-dessus, le message dit « première indication, pas un diagnostic sûr » et renvoie vers un agent agricole ; la prévention affichée vient des fiches sourcées.

## Prochaines étapes

- ConvNeXt-Tiny (plus robuste, mais 7 fois plus lourd) : en cours d'entraînement, à comparer.
- Ajouter CCMT (Ghana) pour la tomate ; des photos consenties des Niayes pour un vrai test local.

## Comparaison avec ConvNeXt-Tiny (13 nov 2026)

Même données, même protocole, 8 époques (`ml/eval/diagnostic_v1_convnext_tiny.json`).

| | MobileNetV3-Large | ConvNeXt-Tiny |
|---|---|---|
| Validation terrain | 84,2 % | 86,0 % |
| Test PlantDoc (102 photos variées) | 56,9 % | 58,8 % |
| Test TOM2024 (1 058 photos de terrain) | 91,7 % | 91,8 % |
| PlantDoc au seuil 0,4 (couverture / précision) | 84,3 % / 61,6 % | 90,2 % / 59,8 % |
| Taille du modèle ONNX | 17 Mo | 111 Mo |
| Temps par photo (1 cœur du Mac) | 15 ms | 126 ms |

**Décision : MobileNetV3 reste le modèle en ligne.** Le gain de ConvNeXt est faible (environ 2 points) et mitigé au seuil retenu, alors que le modèle est 6,6 fois plus lourd et 8 fois plus lent. L'hébergement gratuit (Render : 512 Mo de mémoire, une petite fraction de processeur) laisse peu de marge, et une panne de mémoire pendant la démonstration coûterait plus cher que 2 points de précision. ConvNeXt est gardé hors Git (`modeles/diagnostic_v1_convnext_tiny/`) pour un hébergement plus puissant.

## Feuilles, fruits ou plante entière ? (vérifié le 15 nov 2026)

Planches contact des images TOM2024 tomate (toutes les images de chaque classe, entraînement + validation + test) regardées une à une par classe :

| Ce que montrent les photos | Classes (images TOM2024) |
|---|---|
| **Fruits** | mildiou `late_blight` (72, quasiment que des fruits), `healthy_fruit` (527), `blossom_end_rot` (114), `helicoverpa_armigera` (272), `sunburn` (49), `alternaria` (317, surtout des fruits, quelques feuilles) |
| **Feuilles ou plante entière** | `healthy` (764), `virosis` (1 498), `mites` (380), `bacterial_wilt` (250), souvent des vues larges de plusieurs plants |

PlantVillage et PlantDoc ne contiennent que des feuilles. Conséquences :

- Le modèle a appris sur des feuilles, des fruits et des plantes entières. La consigne photo n'impose donc plus « une seule feuille » : l'agriculteur montre ce qui l'inquiète (feuille, fruit, tige ou toute la plante).
- Le mildiou de la tomate est appris surtout sur feuilles (PlantVillage 600 + PlantDoc 83 en entraînement) et sur peu de fruits (environ 48 en entraînement). Sur les fruits du test TOM2024, il ne reconnaît le mildiou qu'une fois sur deux (50 %, tableau plus haut). Un bon score sur une photo de démonstration ne prouve pas que le modèle soit fiable sur les fruits.
