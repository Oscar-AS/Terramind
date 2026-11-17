<p align="center"><img src="../../docs/assets/readme/mobile.svg" alt="channels/mobile/ : l'application mobile" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/Expo-SDK%2058-1f4d3a?logo=expo&logoColor=white" alt="Expo SDK 58">
  <img src="https://img.shields.io/badge/React%20Native-0.88-3f8f5f?logo=react&logoColor=white" alt="React Native 0.88">
  <img src="https://img.shields.io/badge/cibles-Android%20·%20web-d08a2e" alt="Android et web">
</p>

## En une phrase

L'application TerraMind, pensée pour des maraîchers **peu habitués aux écrans** : une action par écran, de grandes icônes, la voix à terme, et chaque conseil avec sa source.

## L'application en images

<p align="center">
  <img src="../../docs/assets/captures/app/bienvenue.webp" width="13.5%" alt="Bienvenue"> <img src="../../docs/assets/captures/app/langue.webp" width="13.5%" alt="Wolof ou français"> <img src="../../docs/assets/captures/app/accueil.webp" width="13.5%" alt="Accueil"> <img src="../../docs/assets/captures/app/resultat.webp" width="13.5%" alt="Diagnostic : Mildiou, 93 %"> <img src="../../docs/assets/captures/app/resultat2.webp" width="13.5%" alt="Expliqué en 4 temps"> <img src="../../docs/assets/captures/app/plan.webp" width="13.5%" alt="Que planter ce mois-ci"> <img src="../../docs/assets/captures/app/alertes.webp" width="13.5%" alt="Alertes météo de la semaine">
</p>

<sub>Vraies captures de l'application branchée sur le moteur (écran d'iPhone 16, 393 × 852 points), 15 nov 2026. Bienvenue → langue → accueil → diagnostic → explication → plan → alertes. Photo du diagnostic : jeu de test de TOM2024 (CC BY 4.0), jamais vue à l'entraînement. Le visage des écrans de bienvenue et d'accueil est une image générée par IA.</sub>

## Le parcours

```mermaid
flowchart TD
    B["Bienvenue<br/>photo plein écran"] --> L["Langue<br/>wolof ou français"]
    L --> P["Position du champ<br/>GPS, ou zone pilote si refus"]
    P --> C["Ton champ<br/>eau salée ? bas-fond ?"]
    C --> A{"Accueil"}
    A -->|"grande carte photo"| D["Diagnostic<br/>appareil photo ou galerie"]
    D --> R["Résultat<br/>maladie, confiance, que faire"]
    A --> PL["Que planter ?<br/>sol + saison"]
    A --> Q["Question<br/>réponse tirée des fiches"]
    A --> MC["Mes cultures<br/>culture + date de repiquage"]
    A --> AL["Alertes de la semaine<br/>j'ai vu / rien vu"]
```

Les 3 écrans de première ouverture ne s'affichent qu'une fois. Ensuite, l'application s'ouvre directement sur l'accueil.

## Les choix de conception (et d'où ils viennent)

| Choix | Pourquoi | Source |
|---|---|---|
| Accueil centré sur l'appareil photo | Le geste le plus utile doit être le plus visible | Plantix, PictureThis ([références d'écrans](../../docs/maquettes/references-ecrans.md)) |
| Une action par écran, pas de menus imbriqués | Les utilisateurs peu lettrés évitent la navigation hiérarchique | Microsoft Research, interfaces sans texte |
| Icônes + couleur + mot sur chaque badge | Ne jamais compter sur la couleur seule | Règles d'accessibilité |
| Position demandée **après** une explication, avec une liste de zones si refus | La fenêtre système brute fait refuser | Analyse de parcours (screensdesign) |
| Résultat « je ne suis pas sûr » assumé | Mieux vaut orienter vers un agent qu'inventer | Règle du projet (D6, D8) |

**Identité visuelle « Terre des Niayes »** : sable, vert forêt et terre cuite (contrastes vérifiés), polices Bricolage Grotesque et Figtree, icônes Phosphor bicolores, apparitions douces et boutons « à ressort ». Le tout est défini dans [`src/theme.ts`](src/theme.ts) et [`src/components/ui.tsx`](src/components/ui.tsx).

## Organisation du code

| Chemin | Contenu |
|---|---|
| [`src/app/`](src/app/) | Un fichier par écran (Expo Router) : `bienvenue/`, `accueil`, `plan`, `cultures`, `diagnostic/`, `alertes`, `question` |
| [`src/api.ts`](src/api.ts) | Appels au moteur (`/v1/plan`, `/v1/alert`, `/v1/diagnose`, `/v1/chat`, `/v1/feedback`) |
| [`src/profil.ts`](src/profil.ts) | Ce que l'agriculteur a indiqué, gardé **sur le téléphone seulement** ; zones pilotes et cultures |
| [`src/components/`](src/components/) | Cadre d'écran, boutons, cartes, chargement animé, sources, feuille glissante |
| [`src/format.ts`](src/format.ts) | Nombres et dates à la française |
| [`assets/illustrations/`](assets/illustrations/) | Photo d'accueil (générée par IA et signalée comme telle : [CREDITS.md](assets/illustrations/CREDITS.md)) |

## Lancer et tester

```bash
cd channels/mobile
npm install
echo "EXPO_PUBLIC_ENGINE_URL=http://<ip-du-mac>:8000" > .env.local   # adresse du moteur
npx expo start --port 8090        # scanner le QR code avec Expo Go (Android), ou « w » pour le web
npx tsc --noEmit && npx expo lint # vérifications
```

Sans `EXPO_PUBLIC_ENGINE_URL`, l'application appelle `http://localhost:8000` (le moteur lancé sur le même ordinateur, utile pour la version web).

**Distribution sans store** :
- **Android** : APK fabriqué avec EAS Build, partagé par lien ou QR code. Le profil `apk` de [`eas.json`](eas.json) produit un APK (pas un AAB) qui appelle le moteur en ligne (`https://terramind-moteur.onrender.com`) :
  ```bash
  npx eas-cli@latest login                              # compte Expo de Salam (pas de compte d’équipe)
  npx eas-cli@latest build -p android --profile apk     # compilation dans le cloud, lien de téléchargement à la fin
  ```
  Le moteur gratuit de Render s'endort après une période sans visite : la première requête peut prendre environ une minute.
- **iPhone** : la version web, à ajouter à l'écran d'accueil. Apple n'autorise pas l'installation libre d'une application sans compte développeur payant.

## Limites actuelles

- Le bouton « Écouter » est en place, mais la voix wolof n'est pas encore branchée. L'application le dit sur l'écran de langue.
- Les retours « j'ai vu / rien vu » sont envoyés au moteur, qui ne les stocke pas encore.
- Les alertes s'affichent dans l'application. Pas encore de notifications : l'écran qui les demandait a été retiré (16 nov) tant qu'aucune n'est réellement envoyée.

## Responsable

**Salam**.
