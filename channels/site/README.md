<p align="center"><img src="../../docs/assets/readme/site.svg" alt="channels/site/ : le site vitrine" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/HTML-un%20seul%20fichier-1f4d3a" alt="Un seul fichier HTML">
  <img src="https://img.shields.io/badge/langues-français%20·%20anglais-3f8f5f" alt="Français et anglais">
  <img src="https://img.shields.io/badge/hébergement-Vercel-d08a2e?logo=vercel&logoColor=white" alt="Vercel">
</p>

## En une phrase

La page qui présente TerraMind au public et au jury : ce que fait l'assistant, de vraies captures de l'application, les sources, la FAQ, et les liens vers le bot Telegram et l'application Android.

## Les captures de l'application

Les images de [`captures/`](captures/) sont de **vraies captures** de l'application, branchée sur le moteur, à la taille d'un écran d'iPhone 16 (393 × 852 points).

<p align="center">
  <img src="captures/accueil.webp" width="19%" alt="Accueil">
  <img src="captures/resultat.webp" width="19%" alt="Résultat du diagnostic">
  <img src="captures/resultat2.webp" width="19%" alt="Explication en 4 temps">
  <img src="captures/plan.webp" width="19%" alt="Que planter">
  <img src="captures/alertes.webp" width="19%" alt="Alertes météo">
</p>

- Profil de démonstration : Rufisque, tomate plantée le 20 octobre. Aucune donnée réelle d'agriculteur.
- Photo du diagnostic : mildiou de la tomate tirée du **jeu de test** de TOM2024 (CC BY 4.0), jamais vue par le modèle à l'entraînement. Le modèle répond « Mildiou, 93 % ».
- Le visage des écrans de bienvenue et d'accueil est une **image générée par IA** (voir [`channels/mobile/assets/illustrations/CREDITS.md`](../mobile/assets/illustrations/CREDITS.md)).

**Refaire les captures** quand l'application change : la marche à suivre est en tête de [`outils/captures.js`](outils/captures.js).

## Lancer en local

```bash
cd channels/site && python3 -m http.server 5500   # puis http://127.0.0.1:5500
```

## Mise en ligne sur Vercel

Nouveau projet Vercel relié au dépôt, **Root Directory : `channels/site`**, aucun réglage de build. Le bouton « Télécharger l'app » reste en « bientôt disponible » tant que `APK_URL` est vide dans le script de la page.

## Règles

- Rien d'inventé : pas de faux avis, pas de fausses notes, pas de compteurs. Chaque chiffre affiché vient du dépôt (23 fiches, 20 problèmes reconnus, 8 cultures).
- Pas de badge Google Play ni App Store tant que l'application n'est pas sur ces stores (règles de Google et d'Apple).
