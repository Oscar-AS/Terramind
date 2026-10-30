# Fiche du modèle : Diagnostic

> Squelette. À compléter au fil du projet ; version finale le 17 nov 2026.

## Résumé
TODO

## Cultures couvertes
Liste fermée, fixée le 4 nov 2026 (voir [docs/decisions.md](../docs/decisions.md)).
Liste finale : TODO_LISTE_CULTURES

## Données
Jeux publics téléchargés le 2026-10-30 (provenance : [data/README.md](../data/README.md)). Les images restent hors Git, dans `data_local/raw/`.

### TOM2024 (Burkina Faso) : candidat
- Hugging Face `Project-AgML/TOM2024_disease_classification`, configuration `raw`, split `train`, commit `ce3661e` ; CC BY 4.0, attribution requise.
- 12 082 images, 24 classes : maïs 4 589, oignon 3 044, tomate 4 449.
- Contrôles : aucune ligne vide ; 0 image illisible sur un échantillon de 200.
- Limites : classes très petites (aphids-p 4, alternaria-mite-d 8, fusarium-d chez la tomate 18, tuta-absoluta-p 19, bulb-blight-d 30) ; les étiquettes mêlent maladies, ravageurs, stress et fruits, pas seulement des feuilles.

### CCMT (Ghana) : candidat
- Raw Data uniquement (jamais la version augmentée) ; Mendeley Data DOI 10.17632/bwh3zbpkpv.1, téléchargé via Kaggle `irakozekelly/crop-pest-and-disease-dataset` ; CC BY 4.0, attribution requise.
- 25 220 images, 22 classes ; après nettoyage (décision D7) : 24 071 images, soit cajou 6 548, manioc 7 376, maïs 4 822, tomate 5 325.
- Contrôles : les 25 220 images ont été ouvertes ; empreintes de `Tomato/healthy` identiques à celles publiées par Mendeley.
- Limites : images déjà réduites à 400×400 px ; étiquettes peu fiables entre leaf blight, leaf spot et streak virus chez le maïs (voir D7).

### Base fusionnée terramind_v1 (décision D8)
`data_local/processed/terramind_v1/` : `images/<culture>/<classe>/`, `manifest.csv` (une ligne par image, avec sa source et son étiquette d'origine), `classes.csv`, `exclusions.csv`. Reconstruction : `python ml/training/build_merged_dataset.py`.

35 206 images, 37 classes (classes de 114 à 2 294 images) :

| Culture | Sain | Maladie | Ravageur | Abiotique | Total |
|---|---|---|---|---|---|
| Cajou | 1 368 | 3 802 | 1 378 | – | 6 548 |
| Manioc | 1 193 | 5 169 | 1 014 | – | 7 376 |
| Maïs | 754 | 5 290 | 3 046 | – | 9 090 |
| Oignon | 660 | 1 416 | 758 | – | 2 834 |
| Tomate | 1 745 | 6 872 | 627 | 114 | 9 358 |
| **Total** | **5 720** | **22 549** | **6 823** | **114** | **35 206** |

Détail par classe : `classes.csv`. Correspondance des étiquettes : [data/label_mapping.csv](../data/label_mapping.csv).

### Remarques
- Seuls le maïs et la tomate de ces jeux figurent dans la liste provisoire des cultures du projet ; le choix final dépend de la décision du 4 nov 2026.
- **Biais de source** : la plupart des classes ne viennent que d'un seul jeu (toutes les images CCMT font 400×400 px, celles de TOM2024 ont des tailles variables). Le modèle pourrait apprendre à reconnaître le jeu plutôt que la maladie : redimensionner toutes les images à l'entraînement et mesurer les résultats par source.
- Absents de la base faute d'images : mildiou de la tomate, Tuta absoluta, rouille du maïs (voir D8).
- La tomate contient deux classes de fruits (`healthy_fruit`, `blossom_end_rot`) : à exclure si le diagnostic se limite aux feuilles.
- Entraînement / validation / test : TODO (découpage sur terramind_v1)
- Photos de terrain : TODO

## Méthode
- Architecture : TODO
- Entraînement : TODO
- Confiance et seuil « incertain » : TODO

## Métriques
| Jeu | Métrique | Valeur | Date |
|---|---|---|---|
| | | | |

## Limites
TODO

## Usage prévu et hors périmètre
TODO
