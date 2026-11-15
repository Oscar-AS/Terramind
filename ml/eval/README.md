# ml/eval/ : les résultats de chaque version du modèle

| Version | Fiche | Test TOM2024 (terrain) | Test PlantDoc (web) | Statut |
|---|---|---|---|---|
| v0 | [diagnostic_v0.md](diagnostic_v0.md) | — | 54,9 % | remplacée |
| **v1** (MobileNetV3) | [diagnostic_v1.md](diagnostic_v1.md) | **91,7 %** | 56,9 % | **en ligne** |
| v1 ConvNeXt-Tiny | [diagnostic_v1_convnext_tiny.json](diagnostic_v1_convnext_tiny.json) | 91,8 % | 58,8 % | écartée : 6,6 fois plus lourde pour environ 2 points |
| v2 (+ CCMT) | [diagnostic_v2.md](diagnostic_v2.md) | moins bonne que v1 | moins bonne que v1 | écartée (biais de source) |

**Points faibles connus de la v1** : le mildiou de la tomate (50 % sur TOM2024, peu d'images d'entraînement), les acariens, et les photos très variées venues du web (PlantDoc). Sous le seuil de confiance de 0,6, l'application répond « je ne suis pas sûr » plutôt que de deviner.

Les fichiers `.json` contiennent toutes les métriques (par classe, matrices de confusion) ; les `.md` les expliquent.
