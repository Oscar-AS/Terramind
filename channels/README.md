<p align="center"><img src="../docs/assets/readme/channels.svg" alt="channels/ : les façades de TerraMind" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/app%20mobile-Expo%20·%20Android%20et%20web-3f8f5f" alt="Application mobile Expo">
  <img src="https://img.shields.io/badge/Telegram-@TerraMindAfriqueBot-1f4d3a?logo=telegram&logoColor=white" alt="Bot Telegram">
  <img src="https://img.shields.io/badge/WhatsApp-archivé-d08a2e" alt="WhatsApp archivé">
</p>

## En une phrase

Les façades sont les portes d'entrée de l'agriculteur. Elles transmettent sa demande au [moteur](../engine/) et affichent la réponse, **sans aucune logique agronomique** : tout le savoir est dans le moteur.

## L'application en images

<p align="center">
  <img src="../docs/assets/captures/app/bienvenue.webp" width="13.5%" alt="Bienvenue"> <img src="../docs/assets/captures/app/langue.webp" width="13.5%" alt="Wolof ou français"> <img src="../docs/assets/captures/app/accueil.webp" width="13.5%" alt="Accueil"> <img src="../docs/assets/captures/app/resultat.webp" width="13.5%" alt="Diagnostic : Mildiou, 93 %"> <img src="../docs/assets/captures/app/resultat2.webp" width="13.5%" alt="Expliqué en 4 temps"> <img src="../docs/assets/captures/app/plan.webp" width="13.5%" alt="Que planter ce mois-ci"> <img src="../docs/assets/captures/app/alertes.webp" width="13.5%" alt="Alertes météo de la semaine">
</p>

<sub>Vraies captures de l'application branchée sur le moteur (écran d'iPhone 16, 393 × 852 points), 15 nov 2026. Bienvenue → langue → accueil → diagnostic → explication → plan → alertes. Photo du diagnostic : jeu de test de TOM2024 (CC BY 4.0), jamais vue à l'entraînement. Le visage des écrans de bienvenue et d'accueil est une image générée par IA.</sub>

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
