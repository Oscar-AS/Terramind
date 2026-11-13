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
