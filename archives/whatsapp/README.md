<p align="center"><img src="../../docs/assets/readme/whatsapp.svg" alt="archives/whatsapp/ : le bot WhatsApp archivé" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/statut-archivé%20(D12)-14261d?style=for-the-badge" alt="Archivé">
  <img src="https://img.shields.io/badge/WhatsApp-Cloud%20API-3f8f5f?style=for-the-badge" alt="WhatsApp Cloud API">
</p>

**Statut : mis de côté le 13 nov 2026 (décision D12).** La version bêta présentée au jury passe par l'**application mobile** (APK Android et version web, utilisable sur iPhone) et un **bot Telegram**. WhatsApp reste la cible à terme, parce que c'est là que sont les maraîchers des Niayes : on le réactivera si le projet continue après le concours.

Ce dossier garde tout ce qui a été construit, pour repartir de là.

## Ce qui est prêt

| Fichier | Contenu |
|---|---|
| [`engine/routes/whatsapp.py`](engine/routes/whatsapp.py) | Webhook WhatsApp Cloud API. `GET` : vérification de l'adresse par Meta. `POST` : messages entrants, avec **signature `X-Hub-Signature-256` vérifiée avant toute lecture** (refus 503 sans secret configuré). Journaux de diagnostic : champs reçus, statuts `sent`, `delivered`, `failed` avec le code d'erreur Meta, sans numéro ni contenu. Réponse actuelle : un **écho de démonstration**. |
| [`engine/tests/test_webhook_whatsapp.py`](engine/tests/test_webhook_whatsapp.py) | Tests : vérification par Meta (bon et mauvais jeton), signature valide ou invalide, refus sans secret. |
| [`engine/config_whatsapp.py`](engine/config_whatsapp.py) | Les 5 variables lues par le webhook. |
| [`env.example`](env.example) | Où trouver chaque valeur dans le tableau de bord Meta. |

Ce qui a été **vérifié en conditions réelles** (8 au 11 nov 2026) :
- moteur en ligne sur Render ;
- adresse du webhook validée par Meta ;
- messages reçus par le moteur ;
- réponses acceptées par l'API (HTTP 200).

## Pourquoi c'est en pause

Meta refusait de remettre nos réponses (erreur **131031** « Business Account locked ») : le compte Facebook du chef de projet, piraté puis récupéré, avait été restreint. L'entreprise n'est pas non plus vérifiée (code 141010). Détails, codes et démarches : [docs/difficultes.md](../../docs/difficultes.md), § 5.

## Réactiver le bot (marche à suivre)

1. **Côté Meta** : obtenir un compte sans restriction. Demander un examen dans Business Support Home en expliquant le piratage, puis faire la **vérification d'entreprise** avec des documents réels (RCCM ou NINEA). Tester l'envoi du modèle `hello_world` depuis « API Setup » avant toute autre chose.
2. **Remettre le code** :
   ```bash
   git mv archives/whatsapp/engine/routes/whatsapp.py engine/app/routes/whatsapp.py
   git mv archives/whatsapp/engine/tests/test_webhook_whatsapp.py engine/tests/
   ```
   - Recoller le contenu de `engine/config_whatsapp.py` à la fin de `engine/app/config.py`.
   - Dans `engine/app/main.py` : `from .routes import telegram, v1, whatsapp` et `app.include_router(whatsapp.router)`.
3. **Remplacer l'écho par les vrais modules.** Le plus simple est de reprendre la logique du bot Telegram ([engine/app/routes/telegram.py](../../engine/app/routes/telegram.py), fonction `traiter`), qui appelle déjà les modules :
   - position → plan ;
   - photo → diagnostic ;
   - culture et date → alertes ;
   - texte → RAG.

   Seuls changent la lecture du message (format Meta) et l'envoi (`/messages` de l'API Graph), y compris les boutons interactifs et le téléchargement des médias par `media_id`.
4. **Variables** : recopier `env.example` dans `.env` et dans Render, puis réenregistrer le webhook `https://<moteur>/webhook/whatsapp` (champ `messages`).
5. **Tests** : `.venv/bin/python -m unittest discover engine/tests`.

## À prévoir pour un vrai déploiement

- Les **conversations initiées par l'entreprise**, dont les alertes envoyées sans message préalable de l'agriculteur, exigent des **modèles de message approuvés par Meta**. Elles sont aussi facturées.
- **Notes vocales** : le format reçu est OGG/Opus. Il faut les transcrire en wolof (M-Kiriku, voir [docs/voix-wolof.md](../../docs/voix-wolof.md)).
