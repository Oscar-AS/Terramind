# API du moteur

> **Statut : proposition v0.1 du 5 nov 2026**, rédigée pour Salam, **à valider par Oscar**. Elle s'appuie sur les décisions D3, D6, D8 à D11 ([decisions.md](decisions.md)), sur les étiquettes de la base d'images d'Oscar (`data/label_mapping.csv`, branche `ml/dataset-merge`) et sur les règles testées du module Prévention ([sources/seuils-meteo-maladies-ravageurs.md](sources/seuils-meteo-maladies-ravageurs.md)).
>
> Pour changer un point, modifier ce fichier dans une PR et noter la nouvelle version en bas.

Le moteur est le seul endroit où vit la logique agricole. WhatsApp, l'appli web et le tableau de bord ne font qu'appeler ces points d'entrée et afficher la réponse.

## 1. Conventions communes

### Requêtes
- **Format :** JSON en UTF-8, sauf pour l'envoi de photo ou d'audio (`multipart/form-data`).
- **Adresse de base :** variable `ENGINE_URL`. Préfixe de version : `/v1` (ex. `POST /v1/plan`).
- **Champs communs** de toute requête :

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `utilisateur` | texte | oui | Identifiant **pseudonymisé** : empreinte SHA-256 du numéro, calculée par la façade. Jamais le numéro en clair |
| `canal` | `whatsapp` \| `telegram` \| `mobile` \| `pwa` \| `dashboard` | oui | Façade d'origine |
| `langue` | `fr` \| `wo` | oui | Langue de la réponse attendue |

### Réponses : une enveloppe identique pour tous les points d'entrée

```json
{
  "version": "0.1",
  "mock": false,
  "statut": "ok",
  "langue": "wo",
  "message": {
    "texte": "…",
    "texte_fr": "…",
    "audio_url": "https://…/reponse.ogg",
    "reponse_type": null
  },
  "sources": [{"document": "Guide pratique du maraîchage au Sénégal (ISRA, 1987)", "page": "139"}],
  "donnees": {}
}
```

| Champ | Description |
|---|---|
| `mock` | `true` tant que la réponse est factice (jalon J1). Une façade ne doit **jamais** présenter une réponse `mock: true` comme un conseil réel |
| `statut` | `ok` ; `incertain` (le module n'est pas assez sûr) ; `je_ne_sais_pas` (aucune source ne répond, D8) ; `culture_requise` (il manque la culture déclarée) ; `erreur` |
| `message.texte` | Texte à montrer, dans la langue demandée |
| `message.texte_fr` | Toujours rempli quand `langue = wo` : le texte écrit accompagne la note vocale (D10) |
| `message.audio_url` | Note vocale en wolof (OGG/Opus), ou `null` si la voix de synthèse est bloquée par la normalisation (mot à risque, chiffre non traité…). Dans ce cas, la façade envoie la réponse type enregistrée ou le texte |
| `message.reponse_type` | Identifiant de la réponse type utilisée (`content/templates/`), sinon `null` |
| `sources` | Documents et pages d'où vient le contenu. **Jamais vide quand `statut = ok`** (D6, D8) |
| `donnees` | Résultat propre à chaque point d'entrée (sections 2 à 5) |

### Valeurs partagées
- **Cultures :** identifiants anglais en `snake_case` (D3), les mêmes que la base d'images. Le libellé français vient du moteur :

  | Identifiant | Culture |
  |---|---|
  | `tomato` | tomate |
  | `onion` | oignon |
  | `cabbage` | chou pommé |
  | `potato` | pomme de terre |
  | `pepper` | poivron |
  | `chili` | piment |
  | `bitter_eggplant` | jaxatu |
  | `carrot` | carotte |
  | `maize` | maïs |

  La liste des cultures prises en charge sort de la décision d'équipe sur les cultures.
- **Position :** `lat`, `lon` en degrés décimaux (WGS84). Le moteur arrondit à 0,01° (environ 1 km) **avant** toute journalisation.
- **Dates :** ISO 8601 (`2026-11-05`).
- **Aucun produit chimique ni aucune dose** dans un message (règle du projet) ; tout traitement passe par l'orientation vers un agent agricole.

## 2. `POST /v1/diagnose` : photo d'une feuille

**Requête** (`multipart/form-data`) : `photo` (JPEG ou PNG, 10 Mo au plus) **ou** `media_id` (identifiant WhatsApp), plus `culture_declaree` (facultatif) et les champs communs.

**`donnees` de la réponse :**

```json
{
  "predictions": [
    {"culture": "tomato", "etiquette": "late_blight", "categorie": "maladie", "libelle": "Mildiou", "confiance": 0.81},
    {"culture": "tomato", "etiquette": "alternaria", "categorie": "maladie", "libelle": "Alternariose", "confiance": 0.11}
  ],
  "seuil_incertain": 0.6,
  "fiche": "tomate-mildiou",
  "questions_suivi": []
}
```

- **Contenu :**
  - `predictions` : les 3 classes les plus probables ;
  - `etiquette` et `categorie` (`maladie`, `ravageur`, `sain`, `abiotique`, `mixte`) reprennent `data/label_mapping.csv` ;
  - `seuil_incertain` est fixé par Oscar après évaluation, et peut être plus strict pour les petites classes.
- **Sous le seuil :** `statut = incertain` avec la réponse type « je ne suis pas sûr, voici un agent agricole ». Aucune maladie n'est annoncée.
- **Ravageurs que la photo ne reconnaît pas** (mineuse de la tomate, teigne du chou, D11 et stratégie § 1) : `questions_suivi` contient les questions oui/non du manuel de la DPV, que la façade pose ensuite à l'agriculteur.

## 3. `POST /v1/plan` : que planter ici, et quand

**Requête :**

```json
{"lat": 14.76, "lon": -17.21, "date": "2026-11-05",
 "eau_puits_salee": "non", "champ_en_bas_fond": "oui",
 "utilisateur": "…", "canal": "whatsapp", "langue": "fr"}
```

`eau_puits_salee` et `champ_en_bas_fond` valent `oui`, `non` ou `ne_sait_pas`. Ces deux questions remplacent la salinité, qu'aucune carte ne fournit (stratégie § 8).

**`donnees` de la réponse :**

```json
{
  "sol": {"texture": "Sandy Clay Loam", "sable_pct": 59, "argile_pct": 22, "ph": 6.8,
          "source": "iSDAsoil 30 m, 0-20 cm"},
  "cultures": [
    {"culture": "onion", "adaptation": "conseillee", "periode_semis": "octobre à février",
     "cycle_jours": [70, 120], "raisons": ["sol sablo-argileux adapté", "saison fraîche"],
     "avertissements": ["très sensible au sel : à éviter si l'eau du puits est salée"]}
  ]
}
```

- **Valeurs de `adaptation` :** `conseillee`, `possible`, `deconseillee`.
- **Tri des cultures :** la saison en cours, le sol (texture, pH), la tolérance au sel et les zones analogues ([research/itineraires-par-culture.md](../research/itineraires-par-culture.md)).
- **Pas de rendement promis** à l'agriculteur.

## 4. `POST /v1/alert` : risques météo de la semaine

**Requête :**

```json
{"lat": 15.09, "lon": -16.65, "culture": "tomato", "date_repiquage": "2026-12-01",
 "date": "2027-02-10", "utilisateur": "…", "canal": "whatsapp", "langue": "wo"}
```

`culture` est **obligatoire**. Sans elle, la réponse est `statut = culture_requise` et aucune alerte n'est calculée (seuils § 5 bis : sans ce filtre, l'hivernage déclencherait des alertes presque chaque jour). `date_repiquage` est nécessaire pour les ravageurs.

**`donnees` de la réponse :**

```json
{
  "alertes": [
    {"id": "a-2027-02-10-…", "risque": "late_blight", "niveau": "favorable", "regle": "hutton_plafonne",
     "detail": {"jours_conditions_remplies": 2, "plafond_c": 26.6},
     "conseil": "Les conditions sont favorables au mildiou cette semaine : surveille le dessous des feuilles."},
    {"id": "a-…", "risque": "tuta_absoluta", "niveau": "surveiller", "regle": "degres_jours",
     "detail": {"generations_depuis_repiquage": 2.6, "seuil_c": 8.0, "degres_jours_par_generation": 440},
     "conseil": "Une nouvelle génération de mineuse est probable : regarde s'il y a des galeries claires dans les feuilles."}
  ],
  "meteo": {"source": "NASA POWER horaire", "periode": ["2027-02-03", "2027-02-10"]}
}
```

| `risque` | Cultures | `regle` |
|---|---|---|
| `late_blight` (mildiou) | tomato, potato | `hutton_plafonne` : 2 jours avec Tmin ≥ 10 °C et ≥ 6 h à humidité ≥ 90 %, heures comptées seulement à ≤ 26,6 °C |
| `alternaria` (alternariose) | tomato, potato | `tomcast` : notes cumulées |
| `tuta_absoluta` (mineuse) | tomato | `degres_jours` : seuil 8 °C, 440 degrés-jours par génération ; « surveiller » à partir de la 3e génération depuis le repiquage |
| `plutella_xylostella` (teigne) | cabbage | `degres_jours` : seuil 7,3 °C, 290 degrés-jours par génération ; idem |

- **Valeurs de `niveau` :** `aucun`, `surveiller`, `favorable`.
- **Formulation :** le texte dit toujours « conditions favorables » ou « surveille », jamais « ta culture est malade ».

## 5. `POST /v1/chat` : question libre (RAG)

**Requête :** `texte` **ou** `audio` (note vocale, `multipart`) **ou** `media_id`, plus les champs communs.

**`donnees` de la réponse :**

```json
{"transcription": "…", "passages": [{"fiche": "tomate-alternariose", "extrait": "…"}]}
```

- **Fonctionnement :** le moteur cherche dans `content/fiches/`, puis rédige **uniquement** à partir des passages trouvés (D8).
- **Sans passage pertinent :** `statut = je_ne_sais_pas`, avec la réponse type d'orientation vers un agent agricole.
- **En wolof :** la transcription vient de la reconnaissance vocale (M-Kiriku-ASR). La réponse part en note vocale **et** en texte français (D10).

## 6. `POST /v1/feedback` : retour après une alerte (complément)

```json
{"alerte_id": "a-…", "vu": "oui", "utilisateur": "…", "canal": "whatsapp", "langue": "wo"}
```

`vu` vaut `oui`, `non` ou `ne_sait_pas`. Les réponses, anonymisées et regroupées par zone, alimentent le tableau de bord (stratégie § 3). Le module Prévention fonctionne sans elles.

## 7. Points d'entrée techniques

| Point d'entrée | Rôle | État |
|---|---|---|
| `GET /sante` | Le service répond | ✅ fait (J1) |
| `GET /webhook/whatsapp` | Vérification de l'adresse par Meta | 🗄️ archivé (D12) : `archives/whatsapp/` |
| `POST /webhook/whatsapp` | Messages WhatsApp entrants. Signature `X-Hub-Signature-256` obligatoire ; sans secret configuré, refus (503) | 🗄️ archivé (D12) : `archives/whatsapp/` |
| `POST /webhook/telegram` | Messages du bot Telegram. En-tête `X-Telegram-Bot-Api-Secret-Token` obligatoire ; sans jeton ni secret configurés, refus (503) | ✅ fait (13 nov) |

### État des points d'entrée métier (13 nov 2026)

| Point d'entrée | État |
|---|---|
| `POST /v1/plan` | ✅ réel : sol iSDAsoil lu au point (15 à 30 s la première fois, puis en cache), 6 cultures, règles du guide ISRA 1987 |
| `POST /v1/alert` | ✅ réel : NASA POWER (la semaine analysée s'arrête 3 jours avant la date, délai de publication de NASA) |
| `POST /v1/diagnose` | ✅ modèle v0 (tomate, pomme de terre, poivron) ; voir `ml/eval/diagnostic_v0.json` |
| `POST /v1/chat` | ⏳ répond toujours `je_ne_sais_pas` : `content/fiches/` est vide et aucun modèle de langage n'est configuré |
| `POST /v1/feedback` | ⏳ accepté et journalisé, pas encore enregistré (`enregistre: false`, base de données non configurée) |
| Langue `wo` | ⏳ le moteur répond en français et l'indique (`langue: "fr"`, `audio_url: null`) |

## 8. Erreurs

| Code HTTP | Quand | `statut` |
|---|---|---|
| 200 | Réponse rendue, y compris `incertain`, `je_ne_sais_pas` et `culture_requise` | voir ci-dessus |
| 400 | Requête mal formée, ou photo illisible | `erreur` + `message.texte` explicite |
| 422 | Champ manquant ou valeur hors liste (validation automatique de FastAPI, corps d'erreur standard) | — |
| 401 / 403 | Signature ou jeton invalides (webhook) | — |
| 413 | Photo ou audio trop lourds | `erreur` |
| 503 | Dépendance indisponible (météo, modèle, secret non configuré). La façade répond par la réponse type « service momentanément indisponible » | `erreur` |

« Incertain » et « je ne sais pas » ne sont **pas** des erreurs : ce sont des réponses honnêtes, rendues avec le code 200.

## 9. Qui fait quoi

| Point d'entrée | Logique | Branchement |
|---|---|---|
| `/v1/diagnose` | Oscar (modèle, seuil) | Salam |
| `/v1/plan` | Oscar (sol(lat, lon)), Rama (table sol → culture) | Salam |
| `/v1/alert` | Oscar (règles testées par `scripts/donnees/tester_modeles_prevention.py`) | Salam |
| `/v1/chat` | Salam (RAG), Rama (fiches, réponses types), voix (normalisation, contrôle aller-retour) | Salam |

## Historique

| Version | Date | Changement | Validé par |
|---|---|---|---|
| 0.1 | 5 nov 2026 | Première proposition | Salam ; **Oscar : à valider** |
- **v0.2 (13 nov 2026)** : canaux `telegram` et `mobile` (D12), webhook Telegram, code 422, état réel des points d'entrée.
