# TerraMind Afrique

> Assistant agronomique sur WhatsApp et sur le web qui aide les petits maraîchers du Sénégal à choisir quoi semer et quand, à anticiper les maladies et à identifier une maladie à partir d'une photo de feuille.

Projet présenté au **PAS Challenge 2026 (SALTIS)**.

## Architecture : un moteur, deux façades

```
   Agriculteur                      Agriculteur                 Équipe / partenaires
       |                                 |                               |
       v                                 v                               v
+---------------+               +------------------+            +-----------------+
| Bot WhatsApp  |               | Appli web (PWA)  |            | Tableau de bord |
| channels/     |               | channels/pwa     |            | dashboard/      |
| whatsapp      |               | (plan B)         |            |                 |
+-------+-------+               +--------+---------+            +--------+--------+
        |        HTTP (docs/api.md)      |                               |
        +----------------+---------------+-------------------------------+
                         v
        +---------------------------------------------------+
        |         Moteur Python / FastAPI (engine/)         |
        |                                                   |
        |  Planification   GPS -> sol -> cultures + semis   |
        |  Prévention      météo -> risque de mildiou       |
        |  Diagnostic      photo -> culture, maladie,       |
        |                  confiance ou « incertain »       |
        |                                                   |
        |  Réponses : RAG sur fiches validées, FR et wolof  |
        |  (wolof en vocal) ; réponses types en secours    |
        +---------------------------------------------------+
```

Le système est **général** : la culture est un paramètre partout. Seule la liste des cultures prises en charge par le diagnostic est fermée ; elle est fixée le 4 novembre 2026 (voir [docs/decisions.md](docs/decisions.md)).

## Structure du dépôt

```
engine/              Moteur FastAPI
  app/routes/        Points d'entrée HTTP
  app/modules/       planification/, prevention/, diagnostic/
  app/responses/     Réponses : RAG sur les fiches + réponses types
  tests/
channels/
  whatsapp/          Bot WhatsApp (webhook)
  pwa/               Appli web installable
dashboard/           Tableau de bord
content/
  fiches/            Fiches agronomiques (maladies, cultures)
  templates/         Réponses types FR / wolof (envoyées mot pour mot)
  audio/wo/          Audios wolof pré-enregistrés
ml/
  notebooks/ training/ eval/
  MODEL_CARD.md      Fiche du modèle de diagnostic
data/
  README.md          Registre de provenance des données
  sample/            Petits échantillons publics uniquement
research/
  protocole_test.md  Protocole des tests utilisateurs
  consentement.md    Formulaire de consentement
  retours/           Retours terrain (seuls les retours anonymisés sont commités)
docs/
  architecture.md api.md decisions.md risques.md TACHES.md
  rapports-hebdo/    Rapports hebdomadaires
scripts/             Scripts d'organisation (GitHub)
```

## Qui fait quoi

| Membre | Rôle | Périmètre dans le dépôt |
|---|---|---|
| Salam | Chef de projet, moteur, canaux, tableau de bord | `engine/`, `channels/`, `dashboard/` |
| Oscar | IA et données, propriétaire du dépôt | `ml/`, `data/`, `engine/app/modules/` |
| Rama | Contenu agronomique (fiches pour le RAG), réponses types FR/wolof, tests utilisateurs, pitch | `content/`, `research/` |

Plan de tâches détaillé : [docs/TACHES.md](docs/TACHES.md). Document de suivi partagé : TODO_LIEN_DOC

## Jalons 2026

| Date | Jalon |
|---|---|
| 3 nov | J1 |
| 10 nov | J2 |
| 17 nov | J3 : gel des fonctionnalités |
| 22 nov | J4 : fin de construction |
| 25 nov | J5 : revue du jury |

## Règles du concours

- Pas de maquette cliquable, pas de démo factice : ce qui est montré fonctionne réellement.
- Pas de données inventées.
- Provenance, méthode et résultats documentés (voir [data/README.md](data/README.md) et [ml/MODEL_CARD.md](ml/MODEL_CARD.md)).

## Données personnelles et secrets

> **Les photos et positions GPS de vrais agriculteurs ne sont JAMAIS commitées, même dans un dépôt privé.**
>
> Les secrets (jetons, clés) ne sont jamais commités non plus : utiliser un fichier `.env` local (voir [.env.example](.env.example)).

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

[MIT](LICENSE)
