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

## Session 2 · 30 octobre 2026 · Recherche sur X (Twitter) pour les points en suspens

**Qui** : Salam, avec un agent IA ayant accès à X (Grok), puis vérification des pistes par un assistant IA (Claude, d'Anthropic) par recherche web.

**Pourquoi** : trois points restaient sans source après la session 1 : 1) signalements de mildiou au Sénégal (dont celui de Notto Gouye Diama, févr. 2026) ; 2) maïs : maladies des feuilles et chenille légionnaire d'automne ; 3) fiches techniques ISRA réactualisées en 2022.

**Outils** : recherche sur X par l'agent (français, anglais, période 2018 à 2026), puis recherche web pour remonter des posts aux documents d'origine. Les posts X n'ont pas pu être ouverts directement (accès refusé sans compte) : leur texte vient du rapport de l'agent et reste à vérifier.

### Requêtes effectuées

| # | Requête (résumé) | Résultat principal |
|---|---|---|
| 1 | X : mildiou / late blight / *Phytophthora infestans* + Sénégal, Niayes, Rufisque, Notto | Rien |
| 2 | X : ISRA, DPV, ANCAR, CDH, FAO + mildiou | Rien |
| 3 | X : maladies foliaires du maïs (helminthosporiose, rouille, striure) + Sénégal | Rien |
| 4 | X : chenille légionnaire d'automne / *Spodoptera frugiperda* + Sénégal | Posts 2018-2019 (FAO Sénégal, presse, revue scientifique) |
| 5 | X : *Tuta absoluta* + Sénégal | Un fil d'un agronome (2024), une note de marché (2020) |
| 6 | X : fiches techniques ISRA / USAID 2022 | Rien |
| 7 | Web : « First records of the fall armyworm… in Senegal » | Article confirmé (Brévault et al., 2018) |
| 8 | Web : FAMEWS FAO DPV Sénégal 2019 | Rien sur le Sénégal (seulement Togo, Bénin, Guinée) |
| 9 | Web : « Biological management options against the fall armyworm… Senegal » | Article confirmé (Sarr et al., 2023) |

### Sources consultées

| Source | Producteur, année | Accès le 30/10/2026 | Statut | Ce que nous en avons tiré |
|---|---|---|---|---|
| [First records of the fall armyworm, *Spodoptera frugiperda*, in Senegal](https://agritrop.cirad.fr/588026/) (DOI 10.1127/entomologia/2018/0553) | Brévault, Ndiaye, Badiane, Bal, Sembène, Silvie, Haran ; *Entomologia Generalis* 37(2), p. 129-142, 2018 | Résumé lu ; texte complet réservé (copie à demander sur Agritrop) | **Via résumé** | Premiers signalements de la chenille légionnaire d'automne au Sénégal, sur maïs ; souches « riz » et « maïs » identifiées. Repéré grâce à un post X de la revue (6 juil. 2018) |
| [Biological management options against the fall armyworm… in Senegal](https://www.documentation.ird.fr/hor/PAR00026735) (DOI 10.1007/s12600-023-01109-3) | Sarr, Bal, Gauthier ; *Phytoparasitica* 51, p. 975-992, 2023 | Résumé lu (IRD Horizon) | **Via résumé** | Essai au champ en 2018 et 2019 dans le nord-ouest du Sénégal : sans traitement, 1 à 25 % de la surface foliaire et 3 à 44 % des épis abîmés. Trouvé pendant la vérification, pas via X. Les produits testés ne sont pas repris (règle du projet) |
| [Post @FAOSenegal](https://x.com/FAOSenegal/status/1095344462899773440) | FAO Sénégal, 12 févr. 2019 | Non ouvert (X demande un compte) | **À vérifier** | Selon l'agent : formation FAO + DPV à l'application FAMEWS pour surveiller la chenille légionnaire. Pas confirmé par le web |
| [Post @dakaractu](https://x.com/dakaractu/status/950717500567715840) | Dakaractu, 9 janv. 2018 | Non ouvert | **À vérifier** | Selon l'agent : formation contre la chenille légionnaire à Kaolack (projet Naatal Mbay avec la DPV) |
| [Post @JonathanBobMas1](https://x.com/JonathanBobMas1/status/1807782340581556703) | Particulier se présentant comme agronome, 1er juil. 2024 | Non ouvert | **Lue, non utilisée** | Selon l'agent : *Tuta absoluta*, « menace majeure » pour la tomate au Sénégal. Avis personnel, pas une source ; nos sources sur *Tuta* sont déjà meilleures (session 1) |
| Posts @Pressafrik (2018), @acdivoca (2019), @TridgeGlobal (2020) | Presse, ONG, entreprise | Non ouverts | **Lue, non utilisée** | Contexte général à l'échelle de l'Afrique, rien de propre au Sénégal |

### Ce que nous n'avons pas trouvé

- **Aucun signalement de mildiou au Sénégal sur X**, ni de suite donnée au signalement de Notto Gouye Diama (Thiesinfo, 17 févr. 2026). Le point reste non confirmé.
- **Aucune maladie des feuilles du maïs** signalée au Sénégal sur X.
- **Aucune trace des fiches ISRA 2022** sur X (annonce, partage ou lien).
- Aucun compte X actif de l'ISRA ou du CDH Cambérène n'a été identifié.

### Limites

- X sert à trouver des pistes, pas des preuves : seuls les documents vers lesquels mènent les posts (articles, rapports) peuvent être cités.
- Le texte des posts vient du rapport de l'agent et n'a pas pu être vérifié directement.
- Pas de recherche en wolof sur X.

### Ce qui a été produit

- Cette session uniquement. Rien n'a été ajouté à la base de travail ni à la table.

### Suites à donner

- Maïs : utiliser la chenille légionnaire d'automne (ravageur) comme problème principal sourcé, à discuter le 4 nov. Le diagnostic photo PlantVillage ne couvre que des maladies du maïs qui n'ont pas de source sénégalaise.
- Demander une copie de Brévault et al. (2018) sur Agritrop et lire Sarr et al. (2023) en entier avant d'en citer les chiffres.
- Mildiou et fiches ISRA 2022 : X n'apporte rien, passer par l'agronome, le CDH Cambérène ou les organisateurs.
- Contacts possibles : FAO Sénégal (@FAOSenegal) et DPV (compte X à confirmer).

---

## Session 3 · 2 novembre 2026 · Données ouvertes, seuils météo, documents publics à la place des fiches ISRA

**Qui** : Salam, avec un assistant IA (Claude, d'Anthropic) qui a fait les recherches web et les téléchargements par script.

**Pourquoi** : rassembler avant le développement toutes les données encore manquantes (consigne D7) :
- photos pour le diagnostic ;
- règles météo pour la Prévention ;
- vérification des sols iSDAsoil ;
- contenu des fiches ISRA-CDH introuvables ;
- salinité ;
- accès aux modèles wolof.

**Outils** : recherche web, API de Hugging Face, de GitHub, de la Wayback Machine et de NASA POWER ; scripts du dépôt (`telecharger_sources.py`, `telecharger_images.py`, `extraire_rapports.py`, `comparer_zones.py`).

### Requêtes effectuées

| # | Requête (résumé) | Résultat principal |
|---|---|---|
| 1 | API Hugging Face : Kiriku, galsenai, whosper, dofbi, speecht5, Kallaama | Accès et licences relevés (voir `docs/voix-wolof.md` § 7 bis) ; nouvelle voix `AIHubSN/Kiriku-Wolof-TTS` |
| 2 | Licences de PlantVillage et PlantDoc (Hugging Face, GitHub) | CC BY-SA 3.0 et CC BY 4.0 ; aucune classe oignon ni chou |
| 3 | iSDAsoil : règle de l'azote total, légende des textures | Règle `exp(x/100)-1` (catalogue Earth Engine) ; légende USDA publiée avec la carte |
| 4 | TOMCAST / FAST (alternariose) | Tableau des notes (UC IPM), Madden et al. 1978 |
| 5 | Critères Hutton et période de Smith (mildiou) | AHDB 2017 |
| 6 | Humectation estimée par l'humidité relative | Sentelhas et al. 2008 (seuil de 90 %) |
| 7 | *Alternaria porri*, DOWNCAST (maladies de l'oignon) | Suheri et Price 2000 ; Jesperson et Sutton 1987 |
| 8 | Degrés-jours : *Tuta absoluta*, *Plutella xylostella*, *Bemisia tabaci* | Seuils et constantes (voir le document des seuils) |
| 9 | Salinité des sols des Niayes | 4 études (IJBCS 2012, ACSJ 2015, ESJ 2022, Mboltime) |
| 10 | Wayback Machine : marcheagricole.sn | Pages des fiches ISRA-CDH jamais archivées |
| 11 | Fiches ISRA / PADEN / ministère / FAO / ANCAR (oignon, tomate, chou, pomme de terre, poivron) | Livret PIESAN oignon 2022 (FR/wolof), fiche PADEN oignon, FAO/RADHORT tomate, STDF/AUMN chou |
| 12 | isracdh.sn (site du CDH) | Fiches « publiées prochainement », prix pas encore publiés |
| 13 | Fiches de zones voisines : CNRADA (Mauritanie), RECA et chambres d'agriculture (Niger) | 11 fiches CNRADA, 4 documents nigériens |
| 14 | NASA POWER horaire, déc. 2025 à févr. 2026, Tivaouane | Test des critères Hutton sur l'épisode de Notto Gouye Diama |
| 15 | NASA POWER + iSDAsoil sur 11 zones | Comparaison climat et sol des zones analogues |

### Sources consultées

Les sources et leur usage sont détaillés dans :
- [seuils-meteo-maladies-ravageurs.md](seuils-meteo-maladies-ravageurs.md) (règles météo, salinité) ;
- [research/itineraires-par-culture.md](../../research/itineraires-par-culture.md) (documents agronomiques par culture, zones analogues) ;
- [data/README.md](../../data/README.md) et [data/CATALOGUE.md](../../data/CATALOGUE.md) (jeux de données).

Chaque fichier téléchargé est inscrit dans `data/raw/MANIFESTE.csv` (URL, date, empreinte SHA-256).

### Ce que nous n'avons pas trouvé

- **Les fiches ISRA-CDH de 2022** : site fermé, pages jamais archivées, site du CDH sans fiches.
- **Une carte ouverte de la salinité** à l'échelle du champ.
- **Des photos d'oignon et de chou malades** dans les jeux ouverts.
- **Des documents sénégalais récents** pour la tomate, le chou, le poivron et la pomme de terre, équivalents au livret oignon.
- **Une validation au Sénégal** de l'un des modèles météo.

### Limites

- Les modèles météo viennent d'autres pays.
- La météo vient d'une grille d'environ 50 km.
- L'humectation des feuilles est estimée par l'humidité.
- Les fiches de Mauritanie et du Niger ne valent que dans la mesure où leurs zones ressemblent aux Niayes (voir la comparaison climat et sol).
- Les rendements cités sont des rendements de station.

### Ce qui a été produit

- Corrections et extensions des scripts de données : azote, textures, images, documents, zones.
- Nouveaux tableaux dans `data/extraits/` : EAA 2022-2023, inventaire des images, comparaison des zones.
- Documents `docs/sources/seuils-meteo-maladies-ravageurs.md` et `research/itineraires-par-culture.md`.
- Décision D11.
- 22 mots wolof sourcés ajoutés au lexique (livret PIESAN).

### Suites à donner

- Demander les fiches au CDH (formulaire de isracdh.sn).
- Chercher des photos d'oignon et de chou malades sous une licence lisible.
- Faire valider le lexique par un locuteur.
- Tester les autres modèles sur les données EAA et NASA POWER.

---

## Session 4 · 4 novembre 2026 · Chou, documents du PADEN, test du calendrier des règles

**Qui** : Salam, avec un assistant IA (Claude, d'Anthropic).

**Pourquoi** : combler les manques listés à la fin de la session 3 :
- photos de chou malade ;
- fiche PADEN pomme de terre d'origine ;
- lexique wolof ;
- test des règles de Prévention sur d'autres épisodes.

### Requêtes effectuées

| # | Requête (résumé) | Résultat principal |
|---|---|---|
| 1 | Jeux d'images de maladies du chou, licence ouverte (Mendeley, Zenodo, Kaggle) | Mendeley `sjmgzhwrxv` (Ghana, CC BY 4.0) retenu ; jeux Kaggle agrégés écartés (licences mêlées) |
| 2 | Fiche PADEN « production intensive de la pomme de terre » | Site paden-senegal.org fermé ; liste complète des PDF dans la Wayback Machine |
| 3 | Index Wayback de paden-senegal.org | 67 PDF archivés ; 14 retenus (fiches, livrets FR/wolof, manuel DPV des ravageurs, recensement horticole) ; manuel sur les pesticides écarté |
| 4 | Manuel DPV : conditions climatiques des maladies | Alternariose 20-25 °C avec alternance humide/ensoleillé (p. 80) ; mildiou décrit dans les Niayes (p. 88) |
| 5 | Règles de Prévention sur NASA POWER horaire 2020-2025 (4 points) | Calendrier comparé aux saisons documentées (voir le document des seuils, § 5 bis) |

### Ce qui a été produit

- **Images de chou :** 203 images d'origine (`data/raw/images/chou_mendeley/`, empreinte vérifiée).
- **Documents du PADEN :** 14 documents (`data/raw/documents/paden/`, source `paden`).
- **Lexique wolof :** 13 mots ajoutés depuis les livrets PADEN (chou, pomme de terre, carotte, mois de mars à septembre, hectare, saisons) et variantes d'écriture des mois. 51 mots sont à valider, 14 restent à remplir.
- **Test des règles :** `scripts/donnees/tester_modeles_prevention.py` et `data/extraits/prevention_calendrier_2020-2025.csv`.
- **Itinéraires :** chou et pomme de terre complétés avec les documents du PADEN.

### Ce que nous n'avons pas trouvé

- Des images de la teigne du chou.
- Une source pour un plafond de température dans la règle du mildiou.
- Des observations datées par parcelle pour valider les alertes.

### Suites à donner

- Intégrer au module Prévention les conséquences du test (alerte seulement si la culture est déclarée ; générations depuis le repiquage).
- Faire valider le lexique par un locuteur.

---

## Session 5 · 5 novembre 2026 · Plafond du mildiou, questions wolof (Kallaama), contrôle de la voix

**Qui** : Salam, avec un assistant IA (Claude, d'Anthropic).

**Pourquoi** : appliquer la consigne « le terrain est un complément » ([strategie-donnees-manquantes.md](../strategie-donnees-manquantes.md)) :
- trouver le plafond de température du mildiou ;
- préparer les 30 questions de test D9 sans agriculteur ;
- contrôler la voix wolof sans locuteur.

### Requêtes effectuées

| # | Requête (résumé) | Résultat principal |
|---|---|---|
| 1 | Température de sporulation de *Phytophthora infestans* | Optimum 15-20 °C ; quasi nulle à 28 °C (*Plant Disease* 2005) ; pas de germination à 27 °C (*Plant Disease* 2009) ; Crosier 1934 : 3-26 °C |
| 2 | Modèle de Wallin / Blitecast, bornes de température | 7,2 à 26,6 °C (tableau UC IPM, Wallin 1951 et 1962) |
| 3 | Corpus Kallaama : licence, contenu, téléchargement du texte seul | CC BY 4.0 ; transcriptions validées, lexique de prononciation de 48 793 formes et corpus écrit sur GitHub, sans les 5,4 Go d'audio |
| 4 | Questions dans les transcriptions validées (mots interrogatifs × thèmes agricoles) | 76 candidates, 30 retenues à la main, mot pour mot |
| 5 | Mots du lexique TerraMind dans le lexique Kallaama | 42 sur 51 attestés ; 6 variantes d'orthographe trouvées |

### Ce qui a été produit

- **Plafond :** variante « Hutton plafonné » dans `tester_modeles_prevention.py`.
- **Questions D9 :** `research/questions_test_d9_wolof.csv`.
- **Contrôle de la voix :** `scripts/outils/controle_voix.py` et `content/voix/controle_voix.csv`. Les mots « à risque » bloquent la voix en direct.
- **Lexique :** colonnes `atteste_kallaama` et `variante_kallaama`.

### Ce que nous n'avons pas trouvé

- Des questions sur le maraîchage dans Kallaama : les émissions parlent surtout de mil, d'arachide, de maïs, de météo et de semences.
- Les mots *suppome* (chou) et *pepiñeer* (pépinière), absents du lexique Kallaama : ils restent sourcés par les livrets officiels.

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
