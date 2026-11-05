# Stratégie pour les données manquantes

Rédigé le 4 nov 2026, après les sessions de recherche 1 à 4 ([journal](sources/journal-recherche-agronomique.md)).

**Principe 1 : rien d'inventé.** Un manque de données ne devient jamais une réponse inventée ([D6](decisions.md)). Concrètement :
- aucune image générée présentée comme réelle ;
- aucune image augmentée (rotation, bruit…) dans les jeux de test.

**Principe 2 : le terrain est un complément, jamais la base** ([D7](decisions.md)). Les tests avec des agriculteurs, les photos de terrain et l'avis de locuteurs ou d'agronomes ne sont pas garantis dans le temps du concours. Pour chaque manque, la colonne « base » suffit à livrer un bot honnête : sources publiques, documents officiels, contrôles automatiques et choix de conception. Le terrain, s'il a lieu, sert seulement à **confirmer ou améliorer**.

## Vue d'ensemble

| # | Manque | Base : ce qui suffit pour livrer, sans terrain | Complément si le terrain a lieu | Qui | Quand |
|---|---|---|---|---|---|
| 1 | Photos de la **teigne du chou** (0) et de la **mineuse de la tomate** (17) | Le bot **ne reconnaît pas ces ravageurs sur photo**. Il combine l'alerte météo (générations depuis le repiquage) et 3 questions tirées du manuel de la DPV. Recherche continue de jeux ouverts | Photos consenties pour un futur entraînement | Oscar | 10 nov |
| 2 | Classes d'images trop petites : mildiou de la tomate (72), chou mildiou (28), pourriture noire (37) | Seuil « incertain » plus strict pour ces classes ; résultats publiés par classe ; recherche d'autres jeux ouverts | Photos de terrain pour tester | Oscar | 17 nov |
| 3 | Pas de jeu de test **sénégalais** | Test sur des photos **de champ ouest-africaines** déjà en main : TOM2024 (Burkina Faso), CCMT (Ghana), PlantDoc. Résultats par source ; jamais de précision de laboratoire présentée comme une précision de terrain | Petit jeu de test local | Oscar | 17 nov |
| 4 | Lexique wolof : 51 mots à confirmer, 14 à trouver | Les 51 mots viennent de **documents officiels écrits en wolof** (livrets du ministère et du PADEN). **Contrôle automatique** : la voix lit le mot, le modèle de reconnaissance le retranscrit, on compare (§ 2). Un mot qui échoue ou reste sans source **bloque la voix en direct** (déjà codé) | Écoute par Rama ou des locuteurs | Claude (contrôle auto), Salam | 10 nov |
| 5 | 30 questions en wolof pour choisir le modèle qui écrit le wolof ([D9](decisions.md)) | **Faites le 5 nov** : 30 vraies questions tirées des transcriptions validées de Kallaama, mot pour mot (`research/questions_test_d9_wolof.csv`). Limite : surtout des cultures pluviales et la météo, peu de maraîchage | Relecture par des locuteurs ; questions réelles venues du bot | — | fait |
| 6 | Pas d'observation datée pour **valider les alertes** | **Cohérence avec les saisons documentées** (fait : seuils § 5 bis), épisodes publiés (presse, DPV), littérature. Alertes formulées « conditions favorables », seulement si la culture est déclarée | Question « as-tu vu ces signes ? » après chaque alerte, si des agriculteurs utilisent le bot | Claude, Salam | J2 |
| 7 | ~~Plafond de température du mildiou~~ | **Trouvé le 5 nov** : 26,6 °C (modèle de Wallin), cohérent avec la littérature ; effet faible, la culture déclarée reste le filtre principal | — | — | fait |
| 8 | **Salinité** au champ (aucune carte) | Le bot pose 2 questions (« l'eau du puits est-elle salée ? », « ton champ est-il en bas-fond ? ») et applique le tableau de tolérance du guide 1987. Le recensement 2012 montre que 44 % des sites sont en bas-fonds | — | Salam, Rama (formulation) | J2 |
| 9 | **Rendements réels** des petits producteurs | Ordres de grandeur de l'enquête agricole (DAPSA) ; aucun rendement promis à l'agriculteur | Microdonnées ANADS si elles arrivent | — | bonus |
| 10 | Fiches ISRA 2022 ; documents sénégalais récents pour tomate, poivron, piment | Guide 1987, manuel DPV, livrets PADEN, fiches CNRADA signalées (règle des zones analogues) | Réponse du CDH (formulaire de isracdh.sn) | Salam | cette semaine |
| 11 | Licences non indiquées (voix Kiriku, voix GalsenAI) | Usage limité au prototype et à la démo ; rien n'est redistribué ; question posée aux auteurs (onglet « Community » de Hugging Face) | — | Salam | cette semaine |
| 12 | ~~Recensement horticole des Niayes~~ | **Fait le 4 nov** : 71 % des exploitants sans aucun niveau d'instruction ; contraintes de production | — | — | fait |

## 1. Images pour le diagnostic

**Le constat.** Les jeux ouverts couvrent bien les maladies des feuilles de la tomate, de la pomme de terre et du poivron. Ils couvrent peu le chou et presque pas les ravageurs, qui sont pourtant le premier problème des Niayes (enquête agricole 2022-2023 : insecticides sur 99 % des parcelles de chou).

**Base.**
1. **Ne pas tout demander à la photo.** Pour la teigne du chou et la mineuse de la tomate, le bot combine :
   - l'**alerte météo** : générations comptées depuis le repiquage ([seuils § 5 bis](sources/seuils-meteo-maladies-ravageurs.md)) ;
   - **trois questions** tirées du manuel de la DPV : « Vois-tu des galeries claires dans les feuilles ? », « De petites chenilles vertes qui se tortillent et tombent quand on les touche ? », « Des trous dans les feuilles du chou ? ».

   La réponse renvoie à la fiche du ravageur et à un agent agricole. Ça fonctionne sans aucune photo.
2. **Tester sur des photos de champ déjà disponibles** : TOM2024 (Burkina Faso), CCMT (Ghana) et PlantDoc sont des photos de champ ouest-africaines ou réelles, plus proches des Niayes que PlantVillage (laboratoire). Résultats publiés par source et par classe.
3. **Continuer à chercher des jeux ouverts**, avec une licence lisible et les images d'origine seulement. Pistes : mineuse de la tomate en Afrique de l'Est, ravageurs des crucifères. Chaque jeu retenu entre au [registre](../data/README.md) avec son empreinte.
4. **Entraînement** : l'augmentation d'images (rotations, luminosité) sert à l'entraînement seulement, et c'est écrit dans la [fiche du modèle](../ml/MODEL_CARD.md). L'évaluation se fait sur des images d'origine.

**Complément terrain** (si des tests ont lieu) :
- photos prises avec un consentement écrit ([research/consentement.md](../research/consentement.md)) ;
- étiquettes confirmées par un agent agricole ;
- jamais dans Git.

Elles servent à **vérifier** le modèle, pas à l'entraîner.

## 2. Voix et langue wolof

**Base : des sources écrites officielles et un contrôle automatique.**
- **Lexique.** Les mots viennent de documents écrits en wolof par des organismes publics :
  - livret PIESAN, ministère de l'Agriculture, 2022 ;
  - livrets PADEN, 2016 ;
  - pour les nombres, jangawolof.org et l'université de Boston.

  Un mot sans source reste bloquant.
- **Contrôle automatique « aller-retour ».** Pour chaque mot et chaque phrase type :
  1. la voix Kiriku-Wolof-TTS lit le texte ;
  2. le modèle de reconnaissance M-Kiriku-ASR retranscrit l'audio ;
  3. on compare les deux textes (taux d'erreur sur les caractères).

  Au-delà d'un seuil, le mot ou la phrase est marqué « à risque » et ne passe pas en voix de synthèse : le bot utilise la réponse type enregistrée ou le texte. Les deux modèles sont déjà en local (`modeles/`). Ce contrôle ne garantit pas qu'un agriculteur comprendra, mais il attrape automatiquement les mots que la voix déforme.

  **Premier essai (4 nov)** : CER de 0,06 à 0,18 sur 5 phrases officielles ; le contrôle a déjà repéré un mot à risque, « sople », entendu « sopp » ([voix-wolof.md § 7 ter](voix-wolof.md)).
- **Choix du modèle qui écrit le wolof (D9).** Les questions de test viennent du corpus **Kallaama** (enregistrements de conversations agricoles en wolof, transcrites, publiées en libre accès) et des livrets bilingues. Les réponses des modèles candidats sont notées automatiquement : comparaison avec les passages wolof officiels, contrôle aller-retour par la voix.

**Complément** (si des locuteurs sont disponibles) : écoute par Rama ou d'autres locuteurs, notée de 1 à 5 ([voix-wolof.md § 6](voix-wolof.md)). Leur avis prime sur le contrôle automatique quand il existe.

## 3. Alertes de prévention

**Base : la cohérence avec ce qui est publié.**
- Les règles ont été testées sur la météo 2020-2025 et comparées aux saisons d'attaque documentées : DPV, thèse de S. Sylla, rapport STDF, presse. Le calendrier concorde pour les ravageurs quand on compte les générations depuis le repiquage ; pour le mildiou, il oblige à ne prévenir que si la culture est déclarée ([seuils § 5 bis](sources/seuils-meteo-maladies-ravageurs.md)).
- Le texte d'une alerte reste prudent : « les conditions sont favorables à… : surveille ceci », jamais « ta culture est malade ».
- La littérature sert à fixer ce qui manque (plafond de température du mildiou).

**Complément** (si des agriculteurs utilisent le bot) :
- quelques jours après une alerte, le bot demande : « As-tu vu ces signes ? oui / non / je ne sais pas » ;
- les réponses, anonymisées et regroupées par zone, s'affichent dans le [tableau de bord](../dashboard/) ;
- elles serviraient à ajuster les seuils, sans que le module en dépende pour fonctionner.

## 4. Ce qu'on ne fera pas

- Générer des images de maladies, des phrases en wolof ou des réponses d'agriculteurs pour « remplir » un jeu.
- Utiliser une information d'une zone sèche (Niger, Kaédi) pour un risque de maladie lié à l'humidité.
- Présenter une précision de laboratoire comme une précision de terrain.
- Publier une photo, une voix ou une position d'agriculteur.
