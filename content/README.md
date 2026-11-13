<p align="center"><img src="../docs/assets/readme/content.svg" alt="content/ : le savoir du bot" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/fiches-14%20sourcées-1f4d3a" alt="14 fiches sourcées">
  <img src="https://img.shields.io/badge/vérification-118%20sur%20~150%20confirmées-3f8f5f" alt="Vérification indépendante">
  <img src="https://img.shields.io/badge/pesticides%20et%20doses-0-d08a2e" alt="Aucun pesticide ni dose">
</p>

## En une phrase

Ce dossier est **la mémoire du bot** : il ne répond qu'à partir de ce qui est écrit ici. Si une information n'est pas dans une fiche, le bot dit « je ne sais pas » au lieu d'inventer.

## Comment le bot s'en sert (RAG)

```mermaid
flowchart LR
    Q["« Ma tomate a des taches<br/>brunes en cercles »"] --> C["1 · Recherche BM25<br/>dans fiches/"]
    C -->|"score au moins 3,5"| F["Fiche Alternariose<br/>symptômes + prévention<br/>+ sources page par page"]
    C -. "score trop bas" .-> N["« Je ne sais pas,<br/>voici un agent agricole »"]
    F --> G["2 · Gemini reformule<br/>avec ces seuls passages"]
    G -. "extraits insuffisants" .-> N
    G --> R["Réponse courte<br/>+ sources"]
    F -. "sans clé Gemini" .-> R
```

C'est un **examen à livre ouvert**, avec nos fiches pour seul livre ([décision D8](../docs/decisions.md)). Le seuil de 3,5 vient d'une mesure sur 20 questions : 10 questions agricoles entre 4,0 et 11,6, 10 questions hors sujet entre 0 et 3,3 ([docs/seuils-et-parametres.md](../docs/seuils-et-parametres.md)).

> **Analogie Kuroko no Basket** : Riko prépare chaque match avec les données de l'adversaire, jamais au hasard. Le bot fait pareil : il ne « joue » qu'avec ce que les fiches contiennent. Concrètement, Gemini reçoit uniquement les passages trouvés et doit répondre « je ne sais pas » s'ils ne suffisent pas.

## Ce qu'il contient

| Dossier | Contenu | État |
|---|---|---|
| [`fiches/`](fiches/) | 14 fiches : maladies (alternariose, mildiou, cladosporiose, tache bactérienne, viroses), ravageurs (mineuse, teigne du chou, acariens, noctuelle, nématodes, thrips), cultures (tomate, oignon, chou, pomme de terre, poivron et carotte), sol et sel. Chaque phrase porte sa référence (`[G87 p. 140]`), expliquée dans [`_SOURCES.md`](fiches/_SOURCES.md). | ✅ Vérifiées |
| [`voix/lexique_wolof.csv`](voix/lexique_wolof.csv) | Carnet de prononciation pour la voix wolof : nombres, mois, unités, cultures, mots du champ | ✅ Entrées sourcées, à valider par un locuteur |
| [`voix/controle_voix.csv`](voix/controle_voix.csv) | Résultat du contrôle automatique voix → texte de chaque mot (fiable, à risque, non testé) | ✅ |
| [`templates/`](templates/) | Réponses types envoyées mot pour mot | 📅 Vide |
| [`audio/wo/`](audio/wo/) | Réponses sensibles enregistrées par une voix humaine en wolof | 📅 Vide |

## Une vérification indépendante

Les fiches ont été relues par un agent de vérification indépendant, phrase par phrase, contre les PDF sources (13 nov 2026) :
- environ **150 affirmations** ;
- **118 confirmées** ;
- **25 corrigées** : 6 erreurs de page, des formulations déformées, et deux citations du guide de 1987 placées sur des conseils qui n'y figurent pas ;
- **7 invérifiables** (pages web ou articles inaccessibles).

Les corrections sont dans l'historique Git.

## D'où vient le contenu

Uniquement des documents publics et identifiés :
- *Guide pratique du maraîchage au Sénégal* (ISRA, CDH, FAO, 1987) ;
- livrets PADEN et PIESAN des Niayes (oignon, chou, pomme de terre), en français et en wolof ;
- manuel de la DPV sur les ravageurs et maladies des Niayes ;
- documents FAO/RADHORT et KCOA, rapport STDF sur le chou ;
- fiches du CNRADA (Mauritanie) quand le Sénégal ne dit rien.

Le détail est dans [research/](../research/) et [docs/sources/](../docs/sources/).

## Les règles d'une fiche

1. **Rien d'inventé** : chaque phrase a une source (document et page).
2. **Jamais de nom de pesticide ni de dose** : pour tout traitement, le bot oriente vers un agent agricole.
3. **Une information d'un autre pays est signalée**, et seulement si la zone ressemble aux Niayes.
4. **Les désaccords entre sources sont montrés**, pas tranchés en silence (exemple : la variété Xina face aux nématodes, 1987 contre 2012).
5. **Écrite pour l'oreille** quand elle sera lue en wolof : phrases courtes, nombres en toutes lettres.

## Ajouter ou corriger une fiche

1. Créer `fiches/<type>-<sujet>.md`, avec l'en-tête `id`, `titre`, `cultures`, `type`, `statut`.
2. Une section `## …` par thème. La section « Prévention » est montrée après un diagnostic.
3. Mettre une référence entre crochets à la fin de chaque phrase, et ajouter l'abréviation dans `_SOURCES.md` si elle est nouvelle.
4. Le moteur relit les fiches à son démarrage.

## Responsables

**Rama** (contenu), avec **Salam** (RAG, voix wolof).
