<p align="center"><img src="../../docs/assets/readme/fiches.svg" alt="content/fiches/ : les fiches de TerraMind" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/fiches-23-1f4d3a?style=for-the-badge" alt="23 fiches">
  <img src="https://img.shields.io/badge/sources-ISRA%20·%20DPV%20·%20FAO-3f8f5f?style=for-the-badge" alt="Sources ISRA, DPV, FAO">
  <img src="https://img.shields.io/badge/vérifiées-3%20passes-d08a2e?style=for-the-badge" alt="Vérifiées en 3 passes">
</p>

Le savoir du bot. TerraMind ne répond **qu'à partir de ces fiches** (RAG, décision D8) : si la réponse n'y est pas, il dit qu'il ne sait pas et oriente vers un agent agricole.

<p align="center">
  <img src="../../docs/assets/captures/app/resultat.webp" width="24%" alt="Résultat du diagnostic dans l'application">
  <img src="../../docs/assets/captures/app/resultat2.webp" width="24%" alt="La fiche expliquée en 4 temps">
</p>
<p align="center"><sub>Une fiche telle que l'agriculteur la voit, après le diagnostic d'une photo.</sub></p>

## Les 23 fiches

| Type | Fiches |
|---|---|
| Maladies (9) | alternariose, cladosporiose, flétrissement bactérien, fusariose, mildiou, septoriose, tache bactérienne, tache cible, viroses de la tomate |
| Ravageurs (6) | acariose bronzée, chenilles de l'oignon, mineuse de la tomate, noctuelle, teigne du chou, autres ravageurs (nématodes, thrips) |
| Accidents (2) | coup de soleil, nécrose apicale (cul noir) |
| Cultures (5) | tomate, oignon, chou, pomme de terre, poivron et carotte |
| Sol (1) | sol, sel et eau d'arrosage dans les Niayes |

## Comment une fiche est écrite

- **Chaque phrase porte sa source** entre crochets, par exemple `[DPV p. 89]`. Les abréviations sont expliquées dans [`_SOURCES.md`](_SOURCES.md).
- Les maladies et les ravageurs sont expliqués **en 4 temps**, comme chez le médecin : « Ce que c'est », « Comment la reconnaître », « Pourquoi c'est arrivé », « Que faire maintenant », « Pour que ça ne revienne pas ».
- **Jamais de nom de produit ni de dose** : pour un traitement, la fiche renvoie vers un agent agricole.
- Des mots simples : pas de noms latins ni de critères techniques dans « Pourquoi c'est arrivé ».

## Vérification

Un vérificateur indépendant relit chaque fiche contre ses sources. Premier passage : 129 affirmations, 21 corrigées. Deuxième passage (septoriose, tache cible) : 44 affirmations, 5 corrigées. Les fiches mineuse et teigne, réécrites en 4 temps le 14 nov 2026, attendent leur vérification.

## Ajouter une fiche

1. Écrire `type-nom.md` avec l'en-tête (`id`, `titre`, `cultures`, `type`, `statut`) et les sections ci-dessus.
2. Ajouter les nouvelles sources à `_SOURCES.md`.
3. Si le modèle photo reconnaît ce problème, relier son étiquette à la fiche dans `FICHES_ETIQUETTES` ([`engine/app/routes/v1.py`](../../engine/app/routes/v1.py)).
4. Faire vérifier la fiche, puis lancer les tests du moteur.
