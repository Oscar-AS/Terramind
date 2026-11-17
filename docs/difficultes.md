# Difficultés rencontrées et choix qui en découlent

Ce document retrace les obstacles réels du projet (30 oct au 13 nov 2026) et la façon dont chacun a orienté nos choix. Pour chaque difficulté, il donne les faits, ce que nous avons tenté et la décision prise. Les décisions numérotées (D1 à D12) sont détaillées dans [decisions.md](decisions.md).

En résumé : notre règle « aucune donnée inventée » (D6) a souvent rendu le travail plus long. Elle explique la plupart des choix ci-dessous. Quand une donnée manquait, nous avons cherché une source publiée, contourné le problème ou posé la question à l'agriculteur. Nous n'avons jamais comblé le vide par une valeur supposée.

---

## 1. Expertise agronomique

| Difficulté | Ce que nous avons fait | Choix qui en découle |
|---|---|---|
| Aucun agronome disponible pour valider le contenu dans les délais | Recherche systématique de sources publiées : guide ISRA/CDH de 1987, livrets PADEN et PIESAN bilingues, fiches CNRADA, FAO, manuel de la DPV. Les sources sont tracées dans [sources/journal-recherche-agronomique.md](sources/journal-recherche-agronomique.md) | **D7** : le travail ne dépend ni d'un agronome ni des entretiens. Tout conseil cite son document et sa page ; ce qui n'est pas sourcé est exclu. Un agronome reste un bonus, et ses 8 questions sont prêtes |
| Pas de fiches techniques sénégalaises pour la tomate, le poivron et le piment (contrairement à l'oignon, au chou, à la pomme de terre et à la carotte) | Comparaison climat + sol des Niayes avec d'autres zones (NASA POWER, iSDAsoil) pour choisir les fiches étrangères les plus proches : Mauritanie (CNRADA), Niger | Fiches CNRADA utilisées en remplacement, **en le signalant** ([research/itineraires-par-culture.md](../research/itineraires-par-culture.md)) |
| Les rendements publiés sont ceux des stations de recherche, bien au-dessus du champ | — | Le plan ne promet **aucun rendement** à l'agriculteur |
| Règles agronomiques jamais validées au Sénégal (mildiou, alternariose, ravageurs) | Test des règles sur la météo 2020-2025 des 4 points pilotes, et comparaison avec les saisons d'attaque documentées et un signalement de presse (février 2026) | Le bot dit « conditions favorables » et « surveille », jamais « ta culture est malade » ; aucun produit ni aucune dose |

## 2. Recherche de données

| Difficulté | Ce que nous avons fait | Choix qui en découle |
|---|---|---|
| **Site du PADEN fermé** : ses livrets et fiches techniques étaient introuvables | Récupération de 14 documents via les archives de la Wayback Machine : livrets chou, pomme de terre, oignon et carotte en français et en wolof, manuel DPV des ravageurs des Niayes, recensement horticole | Script de téléchargement reproductible avec empreinte de chaque fichier (`scripts/donnees/telecharger_sources.py`) |
| **Fiches ISRA-CDH 2022** jamais archivées en ligne | — | Demande à adresser au CDH de Cambérène ([sources/demandes-acces.md](sources/demandes-acces.md)) ; travail fait sans elles |
| **Aucune carte de salinité** des sols ou des puits des Niayes, alors que c'est un problème documenté (eau « extrêmement saline » mesurée à Keur Saer) | Recherche dans la littérature (Diallo et al. 2015 ; *European Scientific Journal* 2022) | L'application **pose deux questions** à l'agriculteur (« l'eau de ton puits est-elle salée ? », « ton champ est-il en bas-fond ? ») et croise ses réponses avec le tableau de tolérance au sel du guide ISRA |
| **Erreur dans les métadonnées iSDAsoil** : la formule publiée pour l'azote donnait jusqu'à 445 g/kg, une valeur impossible | Vérification croisée avec le catalogue Google Earth Engine d'iSDA ; formule corrigée et documentée | Toute donnée chargée est contrôlée pour sa plausibilité avant usage |
| iSDAsoil sans compte : fichiers de plusieurs Go ; SoilGrids souvent hors service | Lecture directe de la seule tuile utile dans les fichiers publics d'AWS (requêtes partielles), sans compte ni téléchargement complet | Le moteur lit le sol **au point exact du champ**, en quelques secondes |
| **Photos de maladies** : PlantVillage et PlantDoc ne contiennent ni oignon ni chou ; le jeu chou trouvé (203 images) ne montre pas la teigne | Inventaire des jeux ouverts et de leurs licences ([../data/README.md](../data/README.md)) | Pour la teigne et la mineuse, que la photo reconnaît mal, l'application pose les **questions oui/non du manuel DPV** au lieu de deviner |
| **PlantVillage est photographié en laboratoire**, sur fond uni : un modèle peut y dépasser 95 % de réussite et échouer au champ | Évaluation séparée sur PlantDoc (photos de terrain jamais vues à l'entraînement) | Nous publions le **score terrain** et non le score labo. Sous le seuil de confiance, l'application dit « je ne suis pas sûr » et oriente vers un agent agricole |
| **Étiquettes peu fiables** dans certains jeux (par exemple « leaf blight » du maïs et de la tomate : alternariose ou mildiou ?) | Table de correspondance des étiquettes, avec les cas douteux gardés séparés et signalés « à valider » (`data/label_mapping.csv`) | Pas de fusion d'étiquettes sans justification |
| **Collecte de terrain non garantie** (photos, locuteurs, tests) | Stratégie « base sans terrain » : chaque besoin a une solution à partir de sources publiques ([strategie-donnees-manquantes.md](strategie-donnees-manquantes.md)) | Le terrain devient un complément. Le retour de l'agriculteur après chaque alerte (« j'ai vu / je n'ai pas vu ») sert à apprendre en marchant |

## 3. Langue et voix wolof

| Difficulté | Ce que nous avons fait | Choix qui en découle |
|---|---|---|
| **71,3 % des exploitants des Niayes n'ont aucun niveau d'instruction** (recensement horticole, DHORT 2012) ; ceux qui lisent le wolof lisent aussi le français | — | **D10** : en wolof, la voix d'abord (réponse en note vocale) ; interface à grandes icônes, une action par écran |
| Les modèles de langage écrivent encore mal le wolof (AfroBench classe le wolof parmi les langues les plus faibles) | Comparaison des études publiées (AI4Wolof, AfroBench) | **D8 et D9** : réponses construites à partir des fiches (RAG) ; wolof généré seulement après un test noté par des locuteurs ; réponses types relues comme filet de sécurité |
| **Mots agricoles wolof introuvables** : une recherche sur les réseaux sociaux n'a donné que 2 mots | Mots tirés des livrets bilingues PIESAN et PADEN, avec la source de chaque entrée | Lexique de prononciation dont chaque mot reste « à valider par un locuteur » |
| **Synthèse vocale wolof imparfaite** : première lettre perdue avec les majuscules, chiffres et mots français mal lus, pauses aléatoires | Bug des majuscules trouvé et corrigé ; normalisation (nombres écrits en wolof, symboles retirés) ; contrôle automatique aller-retour voix → texte sur 30 questions et sur le lexique | Les phrases à risque sont **bloquées** et remplacées par une réponse enregistrée. On écrit « pour l'oreille » : phrases courtes, pas de symboles |
| **Méthode de contrôle faussée** : la reconnaissance vocale « hallucine » sur un mot isolé | Chaque mot testé dans la phrase la plus courte du corpus qui le contient | Résultat : 24 mots fiables, 11 à risque (voix bloquée), 16 non testés |
| **Biais d'évaluation** : M-Kiriku a été entraîné sur le corpus Kallaama | Nous ne l'évaluons pas sur Kallaama | Questions de test tirées de Kallaama seulement pour les autres usages |
| Modèles très lourds (plus de 6 Go chacun, l'un hébergé sur Google Drive) et licences pas toujours indiquées | Inventaire des modèles et de leurs licences ([voix-wolof.md](voix-wolof.md)) ; licence à demander à AIHubSN | Choix des modèles sous licence claire ; mesure du temps de réponse |

## 4. Hébergement et outils

| Difficulté | Ce que nous avons fait | Choix qui en découle |
|---|---|---|
| **Hugging Face Spaces** est devenu payant pour Docker (juillet 2026) | — | Passage à **Render**, gratuit et sans carte bancaire |
| Dépôt GitHub de l'équipe privé : Render gratuit ne peut pas le lire | Image Docker du moteur publiée sur GitHub Packages, vérifiée sans secret | Déploiement depuis une image publique, reproductible |
| Le **wifi de l'école bloque les services de Meta** (erreur réseau QUIC) | Travail sur une autre connexion | Les manipulations Meta se font hors du réseau de l'école |
| Jetons d'accès Meta **temporaires** (expirent en 24 h) | Création d'un utilisateur système avec un jeton permanent | Aucun secret dans le code ; tout dans `.env`, exclu de Git |
| Version de l'API WhatsApp (v21.0) dépréciée en cours de projet | Passage à la v27.0 | Version configurable dans `.env` |
| **Mobbin** (bibliothèque d'écrans) inutilisable en version gratuite | Références d'écrans tirées de sources publiques (PictureThis, Plantix, messages vocaux WhatsApp) et de recherches sur les interfaces pour personnes peu lettrées ([maquettes/references-ecrans.md](maquettes/references-ecrans.md)) | Parcours de l'application fondé sur ces recherches (Google, Microsoft Research) |

## 5. WhatsApp bloqué par Meta : passage à Telegram et à une application mobile

**Ce qui marchait.** Le moteur était en ligne sur Render (8 nov). Meta avait validé l'adresse du webhook, et les messages des agriculteurs arrivaient au moteur. Nos réponses étaient acceptées par l'API de Meta (HTTP 200).

**Ce qui bloquait.** Meta refusait ensuite de remettre nos messages : statut `failed`, code **131031 « Business Account locked »** (9 nov 2026). L'API Health Status de Meta indiquait plusieurs blocages successifs :

| Date | Niveau | Code Meta | Signification | Action menée | Résultat |
|---|---|---|---|---|---|
| 9 nov | Entreprise | 131000 | Profil d'entreprise incomplet (nom légal, pays, site) | Profil complété | Levé |
| 9 nov | Compte WhatsApp | 141006 | Aucun moyen de paiement | Carte ajoutée (11 nov) | Levé |
| 9 nov | Entreprise | 141010 | Entreprise non vérifiée | Exige des documents officiels (RCCM, NINEA) | Toujours présent le 13 nov |
| 11 nov | Compte WhatsApp | — | « Compte restreint » dans Qualité du compte, aucun problème listé | Demande d'examen à déposer | Envois toujours en échec (13 nov) |

**Cause probable.** La documentation de Meta décrit 131031 comme un compte restreint « pour violation d'une règle de la plateforme ». Le compte Facebook personnel du chef de projet avait été piraté peu de temps avant, puis utilisé par un tiers pour des envois massifs. Il a été récupéré depuis. Un autre compte publicitaire rattaché au même profil est lui aussi restreint. Notre recherche (documentation Meta, forums de développeurs) indique que ces restrictions peuvent s'étendre aux comptes liés au même profil, et que les recours prennent de quelques jours à plusieurs semaines, sans garantie.

**Ce que nous avons écarté.** Recréer un compte Meta au nom d'une autre personne. Meta relie les comptes par profil, appareil, adresse IP et carte bancaire. Cela risquait d'être traité comme un contournement et d'étendre la sanction. Nous n'avons trouvé aucun cas documenté où cette voie avait réussi.

**Décision (D12, 13 nov).** La démonstration passe par un **bot Telegram** et une **application mobile** (APK Android, et version web prévue pour l'iPhone, sans passer par les stores). Telegram ne demande ni vérification d'entreprise ni moyen de paiement. WhatsApp reste la cible à terme, parce que c'est là que sont les maraîchers : le travail est fait (webhook vérifié, signature des messages, journaux de diagnostic) et reprendra dès que Meta lèvera la restriction.

**Ce que ça montre.** Le moteur ne dépend d'aucune messagerie (D1). Changer de façade n'a demandé **aucune modification de la logique agricole** : l'application, Telegram et WhatsApp appellent les mêmes points d'entrée.

## 6. Organisation

| Difficulté | Ce que nous avons fait | Choix qui en découle |
|---|---|---|
| Choix des cultures et de la zone pilote difficile à figer sans données | Méthode : choisir selon les données disponibles et la demande réelle (recensement RGPH-5, enquêtes agricoles DAPSA) plutôt qu'une liste fixée d'avance | Zone pilote des Niayes ; cultures en paramètre du système (D3) |
| Licence AGPL de YOLOv8 incompatible avec une diffusion libre du code | — | **D5** : pas de YOLOv8 tant que la licence n'est pas tranchée ; modèle MobileNet (licence BSD) |
| Données personnelles des agriculteurs (photos, positions, numéros) | — | Identifiant pseudonymisé ; position arrondie à environ 1 km avant tout enregistrement ; rien de personnel dans Git |
