# Stratégie pour les données manquantes

Rédigé le 4 nov 2026, après les sessions de recherche 1 à 4 ([journal](sources/journal-recherche-agronomique.md)).

**Principe** : un manque de données ne doit jamais devenir une réponse inventée. Pour chaque manque, on prévoit trois choses :
1. **combler** : où trouver la donnée, qui s'en charge, pour quand ;
2. **contourner** : comment le bot reste utile sans elle ;
3. **apprendre en marchant** : comment l'usage réel du bot produit la donnée qui manque, avec le consentement des agriculteurs.

Ce qui ne change pas ([D6](decisions.md)) : aucune donnée inventée, aucune image générée présentée comme réelle, aucune image augmentée (rotation, bruit…) dans les jeux de test.

## Vue d'ensemble

| # | Manque | Gravité | Combler | Contourner en attendant | Qui | Quand |
|---|---|---|---|---|---|---|
| 1 | Photos de la **teigne du chou** (0) et de la **mineuse de la tomate** (17) | Haute | Jeux ouverts à vérifier (voir § 1) ; photos de terrain pendant les tests | Ces ravageurs passent par **l'alerte météo et 3 questions** au lieu de la photo | Oscar, Rama | 10-17 nov |
| 2 | Classes d'images trop petites : mildiou de la tomate (72), chou mildiou (28) et pourriture noire (37) | Moyenne | Photos de terrain ; jeux ouverts | Seuil « incertain » plus strict pour ces classes ; résultats publiés par classe | Oscar | 17 nov |
| 3 | Images prises hors du Sénégal (laboratoire, Ghana, Burkina Faso) | Moyenne | Petit jeu de test **local**, même avec peu d'images | Évaluer par source ; ne jamais annoncer une précision mesurée seulement sur PlantVillage | Oscar, Rama | 17 nov |
| 4 | Lexique wolof : 51 mots à valider, 14 à trouver | Haute pour la voix | Rama + 2 locuteurs | Un mot non validé **bloque la voix en direct** : la réponse part en réponse type enregistrée (déjà codé) | Rama | 10 nov |
| 5 | Aucune observation datée pour **valider les alertes** météo | Haute | Retours des agriculteurs après chaque alerte | Alertes formulées « conditions favorables », seulement si la culture est déclarée | Salam (bot), Rama (tests) | dès J2 |
| 6 | **Plafond de température** pour la règle du mildiou | Moyenne | Littérature sur *Phytophthora infestans* (température de sporulation) | Pas d'alerte mildiou hors culture déclarée ; texte prudent | Claude, recherche | 10 nov |
| 7 | **Salinité** au champ (aucune carte) | Moyenne | — | 2 questions à l'agriculteur + tableau de tolérance du guide 1987 | Rama (formulation), Salam | J2 |
| 8 | **Rendements réels** des petits producteurs | Basse | Microdonnées ANADS (bonus D7) | Ne jamais promettre de rendement ; les chiffres de station restent dans les fiches comme repères | — | bonus |
| 9 | Fiches ISRA 2022 ; documents sénégalais récents pour tomate, poivron, piment | Basse | Formulaire de contact de isracdh.sn | Guide 1987 + manuel DPV + CNRADA, signalés (règle des zones analogues) | Salam (courriel) | cette semaine |
| 10 | Jeu de 30 questions en wolof pour choisir le modèle qui écrit le wolof ([D9](decisions.md)) | Haute pour le wolof | Rama, avec des agriculteurs | Réponses types en wolof en attendant | Rama | 10 nov |
| 11 | Licences non indiquées (voix Kiriku, voix GalsenAI) | Moyenne | Demander aux auteurs (onglet « Community » de la page Hugging Face) | Usage limité au prototype et à la démo ; ne rien redistribuer | Salam | cette semaine |
| 12 | ~~Recensement horticole des Niayes~~ | — | **Fait le 4 nov** : instruction des exploitants (71 % sans aucun niveau) et contraintes de production extraites | — | — | fait |

## 1. Images pour le diagnostic

**Le constat.** Les jeux ouverts couvrent bien les maladies des feuilles de la tomate, de la pomme de terre et du poivron. Ils couvrent peu le chou et presque pas les ravageurs, qui sont pourtant le premier problème des Niayes (enquête agricole 2022-2023 : insecticides sur 99 % des parcelles de chou).

**Stratégie en trois volets :**

1. **Ne pas tout demander à la photo.** Pour la teigne du chou et la mineuse de la tomate, le bot n'essaie pas de reconnaître la photo. Il combine :
   - l'**alerte météo** : générations comptées depuis le repiquage ([seuils § 5 bis](sources/seuils-meteo-maladies-ravageurs.md)) ;
   - **trois questions simples** tirées du manuel de la DPV : « Vois-tu des galeries claires dans les feuilles ? », « De petites chenilles vertes qui se tortillent et tombent quand on les touche ? », « Des trous dans les feuilles du chou ? ».

   La réponse renvoie à la fiche du ravageur et à un agent agricole. C'est honnête et ça marche dès le 10 novembre.
2. **Chercher encore dans les jeux ouverts**, avec licence lisible et images d'origine uniquement. Pistes à vérifier : jeux publiés sur la mineuse de la tomate en Afrique de l'Est (Tanzanie, Kenya) et jeux de ravageurs des crucifères. Chaque jeu retenu entre au [registre](../data/README.md) avec son empreinte.
3. **Photos de terrain pendant les tests (10-17 nov).** Protocole court pour Rama :
   - consentement écrit ([research/consentement.md](../research/consentement.md)) ;
   - 3 photos par plante (feuille entière, gros plan, plante) ;
   - étiquette confirmée par un agent agricole ou l'agriculteur, sinon « non confirmé » ;
   - **jamais dans Git**, seulement les comptes par classe.

   Même 20 à 30 photos locales par classe suffisent à **tester** le modèle dans les vraies conditions, pas à l'entraîner.

**Entraînement.** On peut utiliser l'augmentation d'images (rotations, luminosité) pour l'entraînement seulement, et le dire dans la fiche du modèle ([ml/MODEL_CARD.md](../ml/MODEL_CARD.md)). L'évaluation se fait sur des images d'origine, par source, avec une matrice de confusion publiée.

## 2. Voix et langue wolof

- **Lexique** : chaque mot est soit validé, soit bloquant. La chaîne de secours de [voix-wolof.md](voix-wolof.md) garantit que le bot ne lit jamais un mot qu'il prononcerait mal : il envoie à la place une réponse type enregistrée.
- **Validation** : Rama et 2 locuteurs remplissent la colonne « comment on le dit » dans un tableur partagé. Les mots validés par 2 personnes passent au statut `valide`.
- **Modèles** téléchargés en local (`modeles/`, script `scripts/outils/telecharger_modeles.py`) : reconnaissance (M-Kiriku, dofbi) et voix (Kiriku-Wolof-TTS, SpeechT5 en secours). Le test d'écoute ([voix-wolof.md § 6](voix-wolof.md)) départage les voix.

## 3. Alertes de prévention : apprendre en marchant

Aucune donnée ne dit, parcelle par parcelle, quand une maladie est apparue. Le bot peut produire cette donnée lui-même :
1. **Avant** : l'agriculteur déclare sa culture et sa date de repiquage. Sans culture déclarée, pas d'alerte.
2. **Pendant** : l'alerte dit « les conditions sont favorables à… : surveille ceci », jamais « ta culture est malade ».
3. **Après** (3 à 7 jours plus tard) : une question courte, « As-tu vu ces signes ? oui / non / je ne sais pas ».
4. Les réponses, anonymisées et agrégées par zone, servent à mesurer combien d'alertes étaient utiles et à ajuster les seuils. Elles s'affichent dans le [tableau de bord](../dashboard/).

C'est la seule manière réaliste de valider ces modèles au Sénégal dans le temps du concours. Même peu nombreuses, ces réponses seront de vraies données de terrain.

## 4. Ce qu'on ne fera pas

- Générer des images de maladies ou des réponses d'agriculteurs pour « remplir » un jeu.
- Utiliser une information d'une zone sèche (Niger, Kaédi) pour un risque de maladie lié à l'humidité.
- Présenter une précision de laboratoire comme une précision de terrain.
- Publier une photo, une voix ou une position d'agriculteur.
