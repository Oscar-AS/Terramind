# Plan de tâches

Document de suivi partagé : TODO_LIEN_DOC

> Les tâches et échéances viennent du plan d'équipe. Les dépendances (« attend » / « alimente ») ont été déduites de ce plan et **restent à valider en équipe**.

Jalons : **J1** 3 nov · **J2** 10 nov · **J3** 17 nov (gel des fonctionnalités) · **J4** 22 nov (fin de construction) · **J5** 25 nov (revue du jury).
Décision d'équipe le **4 nov** : liste fermée des cultures du diagnostic et zone.

---

## Oscar (IA et données)

| Échéance | Tâche | Attend | Alimente |
|---|---|---|---|
| 30 oct | Dépôt GitHub créé et accès ouverts | — | Toute l'équipe |
| 30 oct | PlantVillage téléchargé, classes listées, jeux séparés | — | Oscar : modèle de base (3 nov) ; équipe : décision cultures (4 nov) |
| 31 oct | Licence de vision tranchée | — | Oscar : modèle de base (3 nov) |
| 2 nov | Contrat d'API validé | Salam : contrat d'API figé (2 nov) | Salam : moteur en ligne (3 nov) |
| 3 nov | Modèle de base avec confiance et seuil « incertain », test d'accès NASA POWER | Oscar : PlantVillage (30 oct), licence (31 oct) | Oscar : modules (10 nov) |
| 6 nov | Cartes de sol et fonction sol(lat, lon) | — | Oscar : Planification (10 nov) ; Rama : table sol → culture (6 nov) |
| 10 nov | Modules Prévention, Planification, livraison des 3 modules à Salam | Oscar : NASA POWER (3 nov), sol (6 nov) ; Rama : table sol → culture, fiches de maladies (6 nov) | Salam : branchement des vrais modules (10 nov) |
| 13 nov | Évaluation sur photos de terrain | Rama : 50 photos de terrain (12 nov) | Oscar : MODEL_CARD final (17 nov) ; risque « précision faible » (14 nov) |
| 14 nov | Test optionnel ASR wolof | Rama : locuteur wolof (30 oct) | Risque « ASR wolof inutilisable » (14 nov) |
| 17 nov | MODEL_CARD final | Oscar : évaluation terrain (13 nov) | Oscar : fiche technique (22 nov) ; Rama : deck v1 (17 nov) |
| 22 nov | Fiche technique | Oscar : MODEL_CARD final (17 nov) | Rama : deck final (22 nov) |
| 24 nov | Réponses techniques au jury | Oscar : fiche technique (22 nov) | Revue du jury (25 nov) |

## Salam (chef de projet, moteur, canaux, dashboard)

| Échéance | Tâche | Attend | Alimente |
|---|---|---|---|
| 30 oct | Questions aux organisateurs | — | Équipe : décision cultures et zone (4 nov) |
| 31 oct | Compte Meta et vérification | — | Salam : bot en écho (3 nov), bot WhatsApp complet (10 nov) |
| 2 nov | Contrat d'API figé | Oscar : contrat d'API validé (2 nov) | Salam : moteur en ligne (3 nov) ; Oscar : modules (10 nov) |
| 3 nov | Moteur en ligne (réponses factices marquées `mock: true`) et bot en écho | Salam : contrat figé (2 nov), compte Meta (31 oct) | Salam : PWA v1 et bot complet (10 nov) |
| 10 nov | PWA v1, branchement des vrais modules, bot WhatsApp complet | Oscar : 3 modules (10 nov) ; Rama : maquettes PWA (6 nov), gabarits FR/wolof (10 nov) | Rama : tests utilisateurs (16 nov) |
| 13 nov | Audios intégrés et slide marché | Rama : audios wolof (12 nov), squelette du deck (13 nov) | Rama : tests utilisateurs (16 nov), deck v1 (17 nov) |
| 14 nov | Dashboard v0 | Salam : moteur (3 nov) | Rama : deck v1 (17 nov) |
| 17 nov | Robustesse | Rama : tests utilisateurs (16 nov) | Salam : version finale (22 nov) |
| 22 nov | Version finale | Salam : robustesse (17 nov) | Rama : vidéo de secours (22 nov) ; Salam : répétition technique (24 nov) |
| 24 nov | Répétition technique | Salam : version finale (22 nov) ; Oscar : réponses techniques (24 nov) | Revue du jury (25 nov) |

## Rama (contenu agronomique, gabarits, tests, pitch)

| Échéance | Tâche | Attend | Alimente |
|---|---|---|---|
| 30 oct | Identifier agriculteurs, agronome, locuteur wolof | — | Rama : entretiens (3 nov), audios (12 nov), tests (16 nov) ; Oscar : ASR wolof (14 nov) |
| 1 nov | Guide d'entretien et consentement | — | Rama : entretiens (3 nov), photos de terrain (12 nov) |
| 3 nov | 3 entretiens | Rama : contacts (30 oct), guide et consentement (1 nov) | Équipe : décision cultures (4 nov) ; Rama : maquettes PWA (6 nov) |
| 6 nov | Maquettes PWA, table sol → culture, fiches de maladies sans dosage | Équipe : cultures fixées (4 nov) ; Oscar : sol(lat, lon) (6 nov) | Salam : PWA v1 (10 nov) ; Oscar : Planification et Prévention (10 nov) |
| 10 nov | Gabarits FR/wolof, protocole de test | Rama : fiches (6 nov) ; contrat d'API (2 nov) | Salam : bot complet (10 nov) ; Rama : audios (12 nov), tests (16 nov) |
| 12 nov | Audios wolof, 50 photos de terrain | Rama : gabarits (10 nov), locuteur wolof (30 oct), consentement (1 nov) | Salam : audios intégrés (13 nov) ; Oscar : évaluation terrain (13 nov) |
| 13 nov | Squelette du deck | — | Salam : slide marché (13 nov) ; Rama : deck v1 (17 nov) |
| 16 nov | Tests utilisateurs (min. 8) | Rama : protocole (10 nov) ; Salam : PWA v1 et bot (10 nov), audios intégrés (13 nov) | Salam : robustesse (17 nov) ; Rama : deck v1 (17 nov) |
| 17 nov | Deck v1 | Rama : tests (16 nov) ; Oscar : MODEL_CARD final (17 nov) | Rama : script du pitch (19 nov) |
| 19 nov | Script du pitch | Rama : deck v1 (17 nov) | Rama : répétitions (23-24 nov) |
| 22 nov | Deck final et vidéo de secours | Salam : version finale (22 nov) ; Oscar : fiche technique (22 nov) | Rama : répétitions (23-24 nov) |
| 23-24 nov | Répétitions | Rama : deck final et script | Revue du jury (25 nov) |
