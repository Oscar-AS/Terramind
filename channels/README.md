<p align="center"><img src="../docs/assets/readme/channels.svg" alt="channels/ : les façades de TerraMind" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/app%20mobile-Expo%20·%20Android%20et%20web-3f8f5f?style=for-the-badge" alt="Application mobile Expo">
  <img src="https://img.shields.io/badge/Telegram-@TerraMindAfriqueBot-1f4d3a?logo=telegram&logoColor=white&style=for-the-badge" alt="Bot Telegram">
  <img src="https://img.shields.io/badge/WhatsApp-archivé-d08a2e?style=for-the-badge" alt="WhatsApp archivé">
</p>

## En une phrase

Les façades sont les portes d'entrée de l'agriculteur. Elles transmettent sa demande au [moteur](../engine/) et affichent la réponse, **sans aucune logique agronomique** : tout le savoir est dans le moteur.

## L'application en images

<p align="center">
  <img src="../docs/assets/captures/app/bienvenue.webp" width="13.5%" alt="Wolof ou français"> <img src="../docs/assets/captures/app/accueil.webp" width="13.5%" alt="La conversation"> <img src="../docs/assets/captures/app/resultat.webp" width="13.5%" alt="Diagnostic : Mildiou, 93 %"> <img src="../docs/assets/captures/app/resultat2.webp" width="13.5%" alt="Expliqué en 4 temps"> <img src="../docs/assets/captures/app/plan.webp" width="13.5%" alt="Que planter ce mois-ci"> <img src="../docs/assets/captures/app/alertes.webp" width="13.5%" alt="Alertes météo de la semaine">
</p>

<sub>Vraies captures de l'application branchée sur le moteur en ligne (393 × 852 points), 21 nov 2026 : choix de la langue, puis tout se passe dans la conversation (diagnostic, explication, plan, alertes). Photo du diagnostic : jeu de test de TOM2024 (CC BY 4.0), jamais vue à l'entraînement.</sub>

## Le bot Telegram en images

<p align="center">
  <img src="../docs/assets/captures/telegram/01-langue.webp" width="13.5%" alt="Choix de la langue"> <img src="../docs/assets/captures/telegram/02-accueil.webp" width="13.5%" alt="Accueil du bot"> <img src="../docs/assets/captures/telegram/02b-accueil-suite.webp" width="13.5%" alt="Accueil : la suite"> <img src="../docs/assets/captures/telegram/03-position-test.webp" width="13.5%" alt="Position test (Niayes)"> <img src="../docs/assets/captures/telegram/04-questions-eau-bas-fond.webp" width="13.5%" alt="Eau salée, bas-fond"> <img src="../docs/assets/captures/telegram/05a-plan-sol.webp" width="13.5%" alt="Ton sol"> <img src="../docs/assets/captures/telegram/05b-plan-cultures-sources.webp" width="13.5%" alt="Que planter, sources"> <img src="../docs/assets/captures/telegram/06a-meteo-choix-culture.webp" width="13.5%" alt="Choix de la culture"> <img src="../docs/assets/captures/telegram/06b-meteo-date.webp" width="13.5%" alt="Météo de ces derniers jours"> <img src="../docs/assets/captures/telegram/06c-meteo-resultat-suite.webp" width="13.5%" alt="Météo : la suite"> <img src="../docs/assets/captures/telegram/07a-consigne.webp" width="13.5%" alt="Consigne photo"> <img src="../docs/assets/captures/telegram/07a-photo-envoyee.webp" width="13.5%" alt="Photo envoyée"> <img src="../docs/assets/captures/telegram/07b-diagnostic-resultat.webp" width="13.5%" alt="Diagnostic : Mildiou, 95 %"> <img src="../docs/assets/captures/telegram/07c-pourquoi.webp" width="13.5%" alt="Pourquoi c'est arrivé"> <img src="../docs/assets/captures/telegram/07d-que-faire-eviter.webp" width="13.5%" alt="Que faire, éviter"> <img src="../docs/assets/captures/telegram/07e-ensuite-sources.webp" width="13.5%" alt="Ensuite, sources"> <img src="../docs/assets/captures/telegram/08a-question.webp" width="13.5%" alt="Question libre"> <img src="../docs/assets/captures/telegram/08b-reponse-sources.webp" width="13.5%" alt="Réponse sourcée">
</p>

<sub>Le parcours complet, dans l'ordre : langue → accueil → position → eau et bas-fond → plan → météo → photo → diagnostic en 4 temps → question libre. Vraies captures du bot @TerraMindAfriqueBot sur un iPhone, branché sur le moteur en ligne (Render), 15 et 16 nov 2026. Position : bouton « Envoyer une position test » (Rufisque, zone pilote des Niayes), pas la position d'un agriculteur. Photo du diagnostic : jeu de test de TOM2024 (CC BY 4.0), jamais vue à l'entraînement. Le mode wolof (notes vocales) sera ajouté après la relecture des traductions.</sub>

## Les façades

| Façade | Pour qui | Comment on l'obtient | État |
|---|---|---|---|
| [**Application mobile**](mobile/) | Les agriculteurs | APK Android à télécharger par lien ou QR code ; version web à ajouter à l'écran d'accueil (iPhone compris), sans passer par les stores | ✅ Écrans branchés sur le moteur |
| **Bot Telegram** **@TerraMindAfriqueBot** | Les agriculteurs, et le jury pour la démonstration | Ouvrir Telegram et chercher le bot | ✅ Prêt. Code dans [engine/app/routes/telegram.py](../engine/app/routes/telegram.py), parce que c'est un webhook du moteur |
| [**Site vitrine**](site/) | Le public, le jury, les partenaires | Page web (hébergement Vercel), en français et en anglais | 🛠️ En cours de refonte, avec de vraies captures de l'application |
| Bot WhatsApp | La cible à terme | — | 🗄️ Archivé : [archives/whatsapp/](../archives/whatsapp/) |
| [`pwa/`](pwa/) | — | — | Remplacée par la version web de l'application mobile |

## Ce qu'il se passe quand l'agriculteur envoie une photo

```mermaid
sequenceDiagram
    autonumber
    actor A as Agriculteur
    participant F as Application ou Telegram
    participant M as Moteur
    participant D as Modèle de diagnostic
    participant K as Fiches sourcées
    A->>F: Photo d'une feuille de tomate
    F->>M: POST /v1/diagnose
    M->>D: Image 224 x 224
    D-->>M: Probabilités calibrées
    alt confiance au moins 0,6
        M->>K: Prévention de la maladie
        K-->>M: Gestes sans produit + sources
        M-->>F: « Cela ressemble à… » + que faire + sources
    else confiance sous 0,6
        M-->>F: « Je ne suis pas sûr » + agent agricole
    end
    F-->>A: Réponse à l'écran
```

## Pourquoi WhatsApp à terme, et Telegram pour la démonstration

Les maraîchers des Niayes utilisent WhatsApp tous les jours, y compris pour les notes vocales. C'était notre premier choix, et le webhook a fonctionné avec Meta. Mais l'envoi des réponses a été bloqué (erreur 131031, compte restreint, entreprise non vérifiée), sans délai garanti avant la livraison. La démonstration passe donc par l'application et Telegram, qui ne demande ni vérification d'entreprise ni paiement. Récit complet : [docs/difficultes.md](../docs/difficultes.md) ; décision : [D12](../docs/decisions.md).

## Sécurité

- Les jetons (`TELEGRAM_BOT_TOKEN`…) sont dans `.env`, **jamais dans le code ni dans Git** (modèle : [.env.example](../.env.example)).
- Le webhook Telegram refuse toute requête sans le bon secret (`TELEGRAM_WEBHOOK_SECRET`).
- L'application garde le profil de l'agriculteur **sur son téléphone seulement**, sans compte ni numéro.
- Aucune photo ni position GPS d'agriculteur n'est publiée ([research/consentement.md](../research/consentement.md)).

## Responsable

**Salam**. Voir [docs/TACHES.md](../docs/TACHES.md).
