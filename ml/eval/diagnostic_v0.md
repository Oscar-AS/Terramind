# Modèle de diagnostic v0 : résultats (13 nov 2026)

**Statut : modèle de départ, proposé pour être comparé puis fusionné avec la base TOM2024 + CCMT d'Oscar (branche `ml/dataset-merge`).**

## Ce qui a été fait

| Élément | Choix |
|---|---|
| Architecture | MobileNetV3-Large pré-entraîné sur ImageNet (licence BSD), dernière couche remplacée, tout le réseau affiné |
| Données | PlantVillage (CC BY-SA 3.0, plafonné à 1 500 images par classe) + PlantDoc entraînement (CC BY 4.0) ; 15 754 images, 15 classes |
| Cultures | tomate, pomme de terre, poivron (aucun oignon ni chou dans ces jeux) |
| Étiquettes | vocabulaire de `data/label_mapping.csv` (`alternaria`, `late_blight`, `leaf_curl`…) pour pouvoir fusionner avec TOM2024 + CCMT |
| Entraînement | 6 époques, AdamW, OneCycle, augmentations (recadrage, rotation, couleurs), poids de classe, lissage des étiquettes 0,1 ; Mac M-series (MPS), environ 17 min |
| Choix du modèle | sur la validation labo uniquement ; le test terrain n'a servi à aucun réglage |
| Service | export ONNX (16 Mo), servi par ONNX Runtime sans PyTorch (écart avec PyTorch : 1e-6) |

Reproduire : `.venv/bin/python ml/training/entrainer_diagnostic.py`, puis `ml/training/exporter_onnx.py`. Métriques détaillées : [diagnostic_v0.json](diagnostic_v0.json).

## Résultats

| Jeu | Images | Précision |
|---|---|---|
| Validation labo (PlantVillage, fond uni) | 2 599 | **99,8 %** |
| **Test terrain** (PlantDoc test, photos prises au champ, jamais vues) | 102 | **54,9 %** |

L'écart entre les deux est attendu : PlantVillage est photographié en laboratoire. **Seul le chiffre terrain compte** pour l'agriculteur.

Classes les mieux reconnues au champ : enroulement jaune TYLCV (83 %), septoriose (82 %), mosaïque (70 %). Les plus mal reconnues : tache bactérienne de la tomate (11 %), tomate saine (25 %).

## Seuil de confiance (test terrain)

| Seuil | Photos jugées « sûres » | Dont justes |
|---|---|---|
| 0,3 | 91 / 102 | 58 % |
| 0,5 | 51 / 102 | 61 % |
| **0,6 (retenu)** | **33 / 102** | **67 %** |
| 0,8 | 10 / 102 | 80 % |

Le modèle est **mal calibré** : sa confiance surestime ses chances d'avoir raison. D'où trois garde-fous dans le moteur :
1. sous 0,6, il ne nomme aucune maladie (« je ne suis pas sûr ») ;
2. au-dessus, le message dit « cela ressemble à… ce n'est qu'une première indication, pas un diagnostic sûr » et renvoie vers un agent agricole ;
3. si la culture est déclarée, seules ses classes sont considérées.

Limite : le test terrain ne compte que 102 photos, de 6 à 11 par classe. Les pourcentages par classe sont donc très incertains.

## Pistes pour la v1

- Fusionner avec TOM2024 + CCMT (photos d'Afrique, avec oignon, mineuse, chenilles) ;
- calibrer les probabilités (température) sur un jeu de validation **de terrain** distinct du test ;
- photos consenties des Niayes pour un vrai test local.
