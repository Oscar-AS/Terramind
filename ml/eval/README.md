<p align="center"><img src="../../docs/assets/readme/eval.svg" alt="ml/eval/ : les résultats du modèle" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/TOM2024-91%2C7%20%25-1f4d3a?style=for-the-badge" alt="TOM2024 91,7 %">
  <img src="https://img.shields.io/badge/PlantDoc-56%2C9%20%25-3f8f5f?style=for-the-badge" alt="PlantDoc 56,9 %">
  <img src="https://img.shields.io/badge/en%20ligne-v1%20MobileNetV3-d08a2e?style=for-the-badge" alt="v1 en ligne">
</p>

| Version | Fiche | Test TOM2024 (terrain) | Test PlantDoc (web) | Statut |
|---|---|---|---|---|
| v0 | [diagnostic_v0.md](diagnostic_v0.md) | — | 54,9 % | remplacée |
| **v1** (MobileNetV3) | [diagnostic_v1.md](diagnostic_v1.md) | **91,7 %** | 56,9 % | **en ligne** |
| v1 ConvNeXt-Tiny | [diagnostic_v1_convnext_tiny.json](diagnostic_v1_convnext_tiny.json) | 91,8 % | 58,8 % | écartée : 6,6 fois plus lourde pour environ 2 points |
| v2 (+ CCMT) | [diagnostic_v2.md](diagnostic_v2.md) | moins bonne que v1 | moins bonne que v1 | écartée (biais de source) |

**Points faibles connus de la v1** : le mildiou de la tomate (50 % sur TOM2024, peu d'images d'entraînement), les acariens, et les photos très variées venues du web (PlantDoc). Sous le seuil de confiance de 0,6, l'application répond « je ne suis pas sûr » plutôt que de deviner.

Les fichiers `.json` contiennent toutes les métriques (par classe, matrices de confusion) ; les `.md` les expliquent.
