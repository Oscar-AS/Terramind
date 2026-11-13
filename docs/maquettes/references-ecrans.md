# TerraMind – Références d'écrans (substituts à Mobbin) et notes d'adaptation

Mobbin (plan gratuit) ne donne accès qu'à 4 apps sans rapport avec le projet, et ses pages de recherche ne se chargent pas. Ce document le remplace : pour chaque étape du parcours, une app de référence, où la voir, ce qu'on en retient et comment l'adapter. Les captures d'autres apps restent en local (`docs/maquettes/inspiration/`, exclu de Git). Les notes « Adapter » sont des propositions à valider avec Rama.

## Où voir les écrans (publics, sans abonnement)

- PictureThis, vidéo décomposée écran par écran : <https://screensdesign.com/showcase/picturethis-plant-identifier>
- PictureThis, captures App Store : <https://screensdesign.com/discover/apps/picturethis-plant-identifier/> et <https://blog.reeoo.com/app-screenshot/picturethis-plant-identifier/>
- PictureThis, fiche App Store : <https://apps.apple.com/PK/app/id1252497129>
- Plantix, fiches Google Play / App Store (chercher « Plantix »), et description du fonctionnement : <https://www.plattform-lernende-systeme.de/practical-exampels.html?AID=400>
- Autres apps de plantes analysées sur screensdesign : <https://screensdesign.com/showcase/free-plant-identifier>
- Messages vocaux WhatsApp : l'app elle-même (le plus fiable pour la capture)
- Duolingo, Google Lens, app météo : non recherchés ici ; à capturer directement sur un téléphone.

Nommage des captures : `NN-etape-app.png` (ex. `03-photo-pictureThis.png`).

---

## Étape 1 – Langue, position, 2 questions sur le champ (première ouverture)

**Référence : Plantix.** Au premier lancement, l'app prend la position du téléphone, demande si la culture est en jardin ou en champ, puis propose une liste courte de cultures à choisir.

- Retenu : peu de questions, choix dans une liste fermée, position demandée tout de suite.
- Adapter : choix de langue en tout premier, deux grands boutons avec voix. Chaque question (puits salé, bas-fond) = une image + oui/non + 🔊. Pas de compte (identifiant anonyme).
- Permission GPS : l'analyse de screensdesign note qu'une app affiche la demande système brute, sans écran d'explication, et que c'est une occasion manquée. Donc : un écran d'explication avec voix wolof AVANT la fenêtre Android, et un plan B « choisir ma zone sur la carte » si refus.

## Étape 2 – Accueil : 3 grandes tuiles

**Référence : PictureThis** (barre du bas avec Identify, Diagnose, Reminders, My Garden, Me : 5 onglets).

- Retenu : le bouton appareil photo est facile à trouver.
- Adapter : 3 tuiles seulement (Que planter / Ma plante est malade / Poser une question), grandes icônes, 🔊 sur chaque tuile. Pas de barre à 5 onglets : trop de choix. Un retour à l'accueil toujours visible.

## Étape 3 – 🌱 Que planter ? (/v1/plan)

**Référence : Plantix** (conseils de saison, calendrier de culture intégré) et les cartes de plantes de PictureThis.

- Adapter : carte = photo de la culture + badge conseillée / possible / à éviter (couleur ET icône, pas la couleur seule) + période de semis + 🔊 pour les raisons et avertissements. Animation pendant l'analyse du sol.

## Étape 4 – Mes cultures (date de repiquage)

**Référence : PictureThis (Reminders / My Garden)**, tâches à venir en cartes ; une analyse relève qu'un réglage de fréquence demande plusieurs touchers.

- Adapter : choisir la culture en photo, puis un calendrier simple (jour, mois), pas de saisie de fréquence. C'est cette date qui déclenche les alertes.

## Étape 5 – 📷 Diagnostic (/v1/diagnose)

**Références : PictureThis (caméra) et Plantix (Health Check).**

- Caméra PictureThis : aperçu plein écran, bouton vert en bas, flash en haut à droite, bouton galerie en bas à gauche.
- Plantix : une seule photo suffit, envoi au serveur, résultat avec le nom du problème puis des options de traitement ; bibliothèque consultable hors ligne.
- Adapter : cadre guide (« mets une feuille dedans ») avec voix ; garder le flash ; galerie en option secondaire. Animation d'analyse accompagnée d'une phrase audio.
- Résultat confiant : nom, photo de référence, conseil audio wolof, source.
- Résultat incertain (`seuil_incertain`) : le dire clairement, proposer « reprendre la photo » ou les `questions_suivi`. Une analyse sur le sujet rappelle qu'un nom de maladie peut être un symptôme visuel plutôt qu'un diagnostic précis : l'app doit donc montrer les limites, pas inventer.

## Étape 6 – 🔔 Alertes de la semaine (/v1/alert)

**Référence : Plantix** (alertes quand une maladie se propage dans la région).

- Adapter : notification avec message vocal, puis carte avec pictogramme du risque + conseil + 🔊. Deux boutons « J'ai vu / Je n'ai pas vu » (/v1/feedback), icônes visage ou pouce, grands.

## Étape 7 – 🎤 Poser une question (/v1/chat)

**Référence : messages vocaux WhatsApp.** On garde le micro appuyé, on lâche pour envoyer ; glisser vers la gauche annule ; glisser vers le haut verrouille l'enregistrement mains libres. Sur les implémentations de référence : maintien minimal d'environ 0,5 s pour distinguer un appui d'un maintien, seuil de verrouillage plus long que celui d'annulation.

- Adapter : gros bouton micro, même geste que WhatsApp (déjà connu des utilisateurs). Prévoir l'option « toucher une fois pour démarrer / une fois pour arrêter » pour ceux qui ont du mal à maintenir. Réponse en audio, texte français en dessous.

---

## Règles transversales (sources de recherche sur interfaces sans texte)

- Icônes simples et standard, grandes, accessibles en un seul toucher (recommandation du « Voice Playbook » de Google pour nouveaux internautes).
- Découper les longs textes en phrases courtes quand ils sont lus à voix haute (même source).
- Chaque erreur doit avoir un retour vocal, et l'état visuel doit correspondre à l'état audio ; éviter de griser des éléments, mieux vaut les faire disparaître quand ils ne servent pas (retour d'expérience sur une app vocale pour utilisateurs peu lettrés au Nigéria).
- Les écrans apparaissent au rythme de la voix (affichage progressif synchronisé avec l'audio).
- Les utilisateurs peu lettrés évitent les fonctions complexes et la navigation hiérarchique (recherches Microsoft sur les interfaces sans texte) : pas de menus imbriqués.
- Hors ligne : garder le dernier plan et les dernières alertes consultables, message clair si le réseau est coupé (Plantix propose une bibliothèque hors ligne).

## Questions à se poser devant chaque écran

1. Un agriculteur qui ne lit pas comprend-il quoi faire ?
2. Combien de boutons ? Moins il y en a, mieux c'est.

## Sources

- Plantix, fonctionnement : plattform-lernende-systeme.de ; ICRISAT (calendrier de culture, mode hors ligne) <https://issca.icrisat.org/scalable-solutions/plant-protection-application-app-plantix> ; FAO (alertes) <https://agritechobservatory.review.fao.org/zh/plantix-crop-doctor>
- PictureThis : screensdesign.com, petapixel.com/picturethis-best-plant-identifier-app/
- WhatsApp vocal : <https://www.lilachbullock.com/?p=145864> , <https://klibs.io/project/NadeemIqbal/voice-message>
- Voice Playbook Google : <https://blog.google/technology/next-billion-users/voice-users-playbook/>
- Microsoft Research, UI pour utilisateurs peu lettrés : <https://www.microsoft.com/en-us/research/project/uis-low-literate-users/>
