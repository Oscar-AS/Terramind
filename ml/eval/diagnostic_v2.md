# Modèle de diagnostic v2 (v1 + tomate CCMT du Ghana) : non retenu (14 nov 2026)

Script : `ml/training/entrainer_diagnostic_v2.py --arch mobilenet_v3_large` (graine 2026, 10 époques).
Métriques complètes : [diagnostic_v2_mobilenet_v3_large.json](diagnostic_v2_mobilenet_v3_large.json).

**Ajout par rapport à la v1** : photos de tomate de CCMT Raw Data (Mensah et al. 2023, CC BY 4.0), nettoyées
selon les décisions D14 et D15 d'Oscar : tomate saine et septoriose seulement. « leaf blight » et
« leaf curl » sont exclus, faute de source qui dise de quelle maladie il s'agit
([docs/sources/verification-regles-oscar.md](../../docs/sources/verification-regles-oscar.md)).

| Jeu de test (jamais vu à l'entraînement) | Images | v1 | v2 |
|---|---|---|---|
| PlantDoc test (photos du web, très variées) | 102 | **56,9 %** | 48,0 % |
| TOM2024 test (photos de terrain, Burkina Faso) | 1 058 | **91,7 %** | 90,7 % |
| CCMT test (Ghana) | 395 | (non mesuré) | 98,7 % |

- La validation terrain monte (84,2 → 89,0 %) parce qu'elle contient maintenant des photos CCMT, faciles pour le modèle.
- Sur PlantDoc, la septoriose s'effondre (91 % → 18 %), la tache bactérienne de la tomate aussi (33 → 11 %).
- 98,7 % sur CCMT : le modèle reconnaît surtout le style des photos du Ghana (images de 400 × 400 px, mêmes
  conditions de prise de vue). C'est le biais de source signalé par Oscar dans ml/MODEL_CARD.md.

**Décision : la v1 reste en ligne.** Piste si l'on veut réessayer : moins d'images CCMT par classe (plafond,
comme pour PlantVillage), et mesurer chaque source séparément.
