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

### Remarques
- Seuls le maïs et la tomate de ces jeux figurent dans la liste provisoire des cultures du projet ; le choix final dépend de la décision du 4 nov 2026.
- Entraînement / validation / test : TODO (découpage après les exclusions de D7)
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
