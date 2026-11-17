<p align="center"><img src="../../docs/assets/readme/training.svg" alt="ml/training/ : l'entraînement du modèle" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/PyTorch-entraînement-1f4d3a?style=for-the-badge" alt="PyTorch">
  <img src="https://img.shields.io/badge/export-ONNX-3f8f5f?style=for-the-badge" alt="ONNX">
  <img src="https://img.shields.io/badge/reproductible-oui-d08a2e?style=for-the-badge" alt="Reproductible">
</p>

| Script | Rôle |
|---|---|
| `entrainer_diagnostic.py` | v0 : première référence (PlantVillage + PlantDoc). |
| `entrainer_diagnostic_v1.py` | **v1, en ligne** : ajoute TOM2024 (photos de terrain du Burkina Faso), calibration, choix de l'époque sur une validation de terrain. |
| `entrainer_diagnostic_v2.py` | v2 : v1 + la tomate de CCMT (Ghana). Non retenue (biais de source). |
| `exporter_onnx.py` | Export ONNX, léger à servir sans PyTorch. |
| `build_merged_dataset.py` | Base fusionnée TOM2024 + CCMT (travail d'Oscar). |

```bash
caffeinate -i .venv/bin/python ml/training/entrainer_diagnostic_v1.py --arch mobilenet_v3_large   # environ 40 min
```

Les séparations entraînement / validation / test sont fixées par une graine (2026) et l'empreinte de chaque image : les photos de test ne sont jamais vues à l'entraînement. Les résultats vont dans [`ml/eval/`](../eval/), le modèle dans `modeles/` (hors Git).

<p align="center"><img src="../../docs/assets/captures/app/resultat.webp" width="24%" alt="Le modèle v1 dans l'application"></p>
<p align="center"><sub>Le modèle v1 dans l'application, sur une photo du jeu de test de TOM2024 : « Mildiou, 93 % ».</sub></p>
