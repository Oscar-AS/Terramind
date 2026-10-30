# Journal de recherche des sources agronomiques

Ce journal explique **comment nous avons cherché, trouvé, vérifié et utilisé** les sources agronomiques du projet : ce qui a été consulté, ce qui a été retenu, ce qui a été écarté, et ce que nous n'avons pas trouvé. Il complète le registre de provenance des données ([data/README.md](../../data/README.md)).

Règle : toute nouvelle recherche ajoute une session datée en bas de ce fichier (modèle en fin de document). On ne réécrit pas une session passée.

---

## Méthode commune

**Ordre de priorité des sources**

1. Institutions sénégalaises : ISRA (dont le CDH de Cambérène), ANCAR, DPV, ANACIM, ANSD.
2. Organisations internationales et recherche publiée : FAO, CIRAD, IRD, articles relus par des pairs.
3. Fiches techniques d'ONG ou de projets, à condition qu'elles citent leurs sources.
4. Presse : uniquement pour des faits datés (un signalement, un événement), jamais pour une donnée agronomique.

**Règles de vérification**

- Chaque information retenue est reliée à une source précise (document, page ou section).
- Quand le document est un scan, le texte extrait automatiquement est vérifié sur l'image de la page avant d'être repris. Ce qui reste douteux est marqué « à vérifier ».
- Les dosages et les noms de pesticides ne sont **jamais** repris, même quand la source en donne (règle du projet : pas de dosage sans source validée par un agronome).
- Une connaissance générale qui n'a pas encore de source précise est marquée « à sourcer » et n'est pas utilisée dans le produit.
- Rien n'entre dans le produit (gabarits, table de règles) sans relecture par Rama et validation par l'agronome.

---

## Session 1 · 30 octobre 2026 · Sources pour la table sol → culture, les fiches maladies et le module Prévention

**Qui** : Salam, avec un assistant IA (Claude, d'Anthropic) qui a fait les recherches web, téléchargé les documents publics et extrait leur contenu. Les résultats sont à relire par Rama et à faire valider par l'agronome.

**Pourquoi** : le plan de tâches notait qu'« aucune fiche ISRA ou ANCAR n'a été trouvée en téléchargement ». Le but était de donner à Rama une base sourcée pour la table sol → culture et les fiches maladies (échéance du 6 nov), et de documenter le risque de mildiou pour le module Prévention.

**Point de départ** : le dossier de projet (12 oct 2026), qui citait déjà ISRA, ANCAR, SoilGrids, NASA POWER, CHIRPS, ANACIM et PlantVillage.

**Outils** : moteur de recherche web ; téléchargement direct des PDF publics ; extraction du texte avec `pdftotext` (Poppler) ; lecture de l'image des pages pour corriger les erreurs de reconnaissance du scan.

### Requêtes effectuées

| # | Requête (résumé) | Résultat principal |
|---|---|---|
| 1 | ISRA CDH Cambérène maraîchage Niayes fiche technique tomate | Guide pratique du maraîchage (ISRA/FAO, 1987) ; fiches ISRA-CDH sur marcheagricole.sn |
| 2 | Niayes sols dior deck pH texture maraîchage | Typologie des sols (ministère) ; De Bon et al. 2019 ; études Mboltime et Niayes nord |
| 3 | DPV Sénégal maladies tomate pomme de terre mildiou Niayes | Article Thiesinfo (signalement de mildiou) ; plans de gestion des pestes |
| 4 | Calendrier cultural maraîcher Sénégal contre-saison froide | ANSD RGPH-5 ; FAO/RADHORT ; guide 1987 |
| 5 | Plantwise / CABI fiche Sénégal tomate mildiou alternariose | Pas de fiche Plantwise Sénégal ; fiche KCOA 2025 ; Ephytia (INRAE) |
| 6 | *Phytophthora infestans* Senegal late blight Niayes | Aucune étude sénégalaise |
| 7 | *Tuta absoluta* Sénégal Niayes | Premier signalement 2012 ; thèse UCAD/CIRAD |
| 8 | Late blight risk model Smith period Hutton criteria (AHDB) | Critères Hutton (AHDB, 2017) |
| 9 | « mildiou » pomme de terre Sénégal Niayes 2024-2026 | Confirmation et date de l'article Thiesinfo (17 févr. 2026) |
| 10 | ANCAR Sénégal fiches techniques maraîchage | Aucune fiche ANCAR en ligne |
| 11 | Maïs Sénégal maladies, chenille légionnaire | Projet ISRA KAFACI ; rien sur les maladies foliaires |
| 12 | ISRA fiche technique pomme de terre oignon Niayes 2020 | Annonce ISRA de la réactualisation des fiches (2022) |
| 13 | Maladies foliaires du maïs au Sénégal (rouille, helminthosporiose) | Aucune source sénégalaise |
| 14 | NASA POWER API hourly RH2M T2M | Données horaires disponibles (communauté AG) |
| 15 | TYLCV Sénégal aleurode Niayes | Enquête 2012-2014 dans les Niayes ; essai variétal |
### Sources consultées

Statuts : **Utilisée** (reprise dans le brouillon) · **Lue, non utilisée** · **Inaccessible** · **Via résumé** (seul un extrait ou un résumé a pu être lu, le document complet reste à relire).

| Source | Producteur, année | Accès le 30/10/2026 | Statut | Ce que nous en avons tiré |
|---|---|---|---|---|
| [Guide pratique du maraîchage au Sénégal](https://open-library.cirad.fr/files/4/751__Guide_pratique_du_maraichage_au_Senegal.pdf) | J. Beniest et al., ISRA / FAO, CDH Cambérène, 1987 (147 pages) | PDF téléchargé (libre accès, bibliothèque ouverte du CIRAD) | **Utilisée** | Tolérance des cultures au pH (Tableau 3, p. 11), à la salinité (Tableau 1, p. 5), fiches de 8 cultures (sols, périodes, cycles), symptômes des maladies |
| [Annonce de la réactualisation des fiches techniques](https://isra.sn/2022/03/20/lisra-et-lusaid-sengagent-pour-la-reactualisation-des-fiches-techniques-des-principales-cultures-maraicheres-au-senegal/) | ISRA, 20 mars 2022 | Page lue | **Utilisée** | 20 cultures réactualisées en 2022 avec l'USAID ; aucun lien de téléchargement |
| Fiches ISRA-CDH (tomate, pomme de terre, oignon…) sur marcheagricole.sn | ISRA-CDH | **Inaccessible** (le nom de domaine ne répondait pas) | Inaccessible | À réessayer, ou à demander directement au CDH |
| Catalogue ISRA (intranet.isra.sn, document IS0305526) | ISRA | **Inaccessible** (délai de connexion dépassé) | Inaccessible | À réessayer |
| [Fiche production biologique de la tomate au Sénégal](https://kcoa-africa.org/wp-content/uploads/2025/10/Fiche-technique_production-biologique-Tomate-2.pdf) | KCOA-Africa, 2025 | PDF téléchargé | **Utilisée** | Gestes de prévention sans produit (ne pas arroser le feuillage, goutte-à-goutte, pépinière sous moustiquaire) |
| [Techniques de production de semences de tomate au Sénégal](https://openknowledge.fao.org/server/api/core/bitstreams/f65c83bb-f7f5-42cb-b3ae-e14b49e7abfb/content) | FAO / RADHORT / ISRA-CDH, 2012 | Téléchargement refusé (HTTP 403) | **Via résumé** | Principaux problèmes de la tomate en saison fraîche : mineuse, noctuelle, acariose bronzée, alternariose, TYLCV |
| [Rendements et pratiques… en agriculture biologique](https://www.cahiersagricultures.fr/articles/cagri/full_html/2019/01/cagri180073/cagri180073.html) | De Bon et al., *Cahiers Agricultures*, 2019 | Via résumé | **Via résumé** | Sols dior des Niayes : 90 à 95 % de sables, pH 5,5 à 6,5 ; Niayes = environ 60 % de la production maraîchère |
| [Typologie des sols dior / dior-deck](https://edepot.wur.nl/487348) | Ministère de l'Agriculture du Sénégal | Via résumé | **Via résumé** | Définition des sols dior et dior-deck (texture, argile, pH) |
| Études sur les sols de Mboltime et des Niayes nord (ResearchGate) | Plusieurs auteurs | Via résumé | **Via résumé** | pH très acide et salinité dans certaines cuvettes |
| [RGPH-5, chapitre Agriculture](https://www.ansd.sn/sites/default/files/recensements/rapport/Chapitre%2010%20-%20AGRICULTURE-Rapport-Provisoire-RGPH5_juillet2024.pdf) | ANSD, juillet 2024 | Via résumé | **Via résumé** | Définition des contre-saisons ; cultures les plus répandues |
| [Article sur la maladie dans les Niayes](https://www.thiesinfo.com/Zone-des-Niayes-des-maraichers-alertent-sur-une-maladie-qui-menace-leurs-recoltes_a13075.html) | Thiesinfo, 17 févr. 2026 | Page lue | **Utilisée** (fait daté) | Symptômes « qui ressemblent au mildiou » à Notto Gouye Diama, sans diagnostic officiel |
| [Tomate, mildiou](https://ephytia.inrae.fr/fr/C/5086/Tomate-Mildiou-Phytophthora-infestans) | Ephytia, INRAE | Via résumé | **Via résumé** | Description des symptômes du mildiou ; différence avec l'alternariose |
| [First Record of *Tuta absoluta* in Senegal](https://bioone.org/journals/florida-entomologist/volume-96/issue-2/024.096.0241/First-Record-of-Tuta-absoluta-Lepidoptera-Gelechiidae-in-Senegal/10.1653/024.096.0241.full) | Pfeiffer et al., *Florida Entomologist*, 2013 | Via résumé | **Via résumé** | Premier signalement au Sénégal en 2012 |
| [Thèse sur la mineuse de la tomate](https://agritrop.cirad.fr/590299/1/Th%C3%A8se_Serigne_VF.pdf) | S. Sylla, UCAD / CIRAD | Via résumé | **Via résumé** | Jusqu'à 60 % d'infestation dans les Niayes ; pics de février à mai |
| [Arthropod pest complex… in field-grown tomato in Senegal](https://www.researchgate.net/publication/326608949_Arthropod_pest_complex_and_associated_damage_in_field-grown_tomato_in_Senegal) | Article scientifique (98 champs, 2012-2014) | Extrait seulement | **Via résumé** | Aleurode et TYLCV présents dans les Niayes ; chiffres à relire |
| [Projet KAFACI-FAW](https://isra.sn/2024/09/18/lutte-contre-la-chenille-legionnaire-dautomne-cla-le-projet-kafaci-faw-pour-une-gestion-integree-de-la-riposte/) | ISRA, 18 sept. 2024 | Via résumé | **Via résumé** | Chenille légionnaire d'automne sur le maïs, travaux de l'ISRA/CDH depuis 2020 |
| [Critères Hutton](https://potatoes.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria) | AHDB / James Hutton Institute, 2017 | Via résumé | **Via résumé** | Seuils de risque de mildiou (10 °C, 90 % d'humidité pendant 6 h, deux jours de suite) ; validés au Royaume-Uni seulement |
| [API horaire NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/) | NASA | Via résumé | **Via résumé** | `T2M` et `RH2M` disponibles heure par heure |
| Fiches agroécologiques de la vallée du fleuve (CERAI, rim-rural.org) | CERAI | Repérée, non ouverte (PDF de 55 Mo) | Lue, non utilisée | Hors zone pilote ; à garder pour plus tard |
| Guide maraîchage ISRA-CDH / KOPIA, 2015 (Agritrop) | ISRA-CDH, KOPIA | Réservé au personnel du CIRAD | Inaccessible | À demander à l'ISRA |

### Ce que nous n'avons pas trouvé

- **Aucune fiche technique ANCAR** téléchargeable.
- **Aucune étude sénégalaise sur le mildiou** (*Phytophthora infestans*). Le guide ISRA de 1987 ne le cite pas parmi les maladies de la tomate et de la pomme de terre.
- **Aucune source sénégalaise sur les maladies des feuilles du maïs** couvertes par PlantVillage (rouille commune, helminthosporiose du nord, tache grise).
- **Aucune source sénégalaise sur la tache cible de la tomate** (*Corynespora cassiicola*) ni sur le virus de la mosaïque de la tomate.
- **Aucun seuil de risque de mildiou validé en Afrique de l'Ouest.**

### Limites

- Le guide de 1987 est ancien : variétés et calendriers sont à confirmer avec les fiches réactualisées de 2022 et avec l'agronome.
- Plusieurs sources n'ont été lues qu'à travers un résumé ou un extrait : les chiffres qui en viennent sont signalés et doivent être vérifiés dans le document complet avant d'être présentés.
- La recherche s'est faite en français et en anglais seulement.

### Ce qui a été produit

- [research/base-de-travail-agronomique.md](../../research/base-de-travail-agronomique.md) : base de travail pour Rama, avec la mention « brouillon, non validé ».
- [research/brouillon_table_sol_culture.csv](../../research/brouillon_table_sol_culture.csv) : brouillon de table sol → culture pour 8 cultures.
- Une ligne dans le registre [data/README.md](../../data/README.md) pour le guide de 1987, utilisé comme source de données.

### Suites à donner

- Demander au CDH Cambérène (ou à l'encadreur) les fiches techniques réactualisées en 2022.
- Réessayer marcheagricole.sn et l'intranet de l'ISRA.
- Lire en entier les sources marquées « Via résumé » avant d'en citer les chiffres dans le pitch.
- Faire valider la table et les fiches par l'agronome, puis noter la date et le nom du validateur dans ce journal.

---

## Modèle pour une nouvelle session

```markdown
## Session N · JJ mois AAAA · Objet de la recherche

**Qui** :
**Pourquoi** :
**Outils** :

### Requêtes effectuées
| # | Requête | Résultat principal |

### Sources consultées
| Source (lien) | Producteur, année | Accès (date) | Statut | Ce que nous en avons tiré |

### Ce que nous n'avons pas trouvé
### Limites
### Ce qui a été produit
### Suites à donner
```
