# Itinéraires techniques par culture, à partir des documents publics

Rédigé le 2 nov 2026. Remplace, faute de mieux, les fiches ISRA-CDH de 2022 :
- elles ne sont plus téléchargeables (marcheagricole.sn est fermé, et la Wayback Machine n'a jamais archivé les pages de téléchargement) ;
- le site du CDH, isracdh.sn, annonce que ses fiches seront « publiées prochainement ».

Les documents sont téléchargés par `python3 scripts/donnees/telecharger_sources.py fiches` dans `data/raw/documents/fiches/` (exclu de Git, empreintes dans `data/raw/MANIFESTE.csv`).

**Règle d'usage pour les fiches de Rama** :
- On recopie des faits sourcés (document + page), jamais de noms de pesticides ni de doses de produits (règle du projet).
- Les engrais organiques et minéraux de base (fumier, NPK) peuvent être cités tels que les sources les donnent, avec leur source. Ils restent à relire par un agronome si on en trouve un (bonus D7).

## 1. Quelles zones peuvent remplacer les Niayes quand le Sénégal ne dit rien ?

On compare **le climat et le sol**, pas seulement le climat. Script : `python3 -I scripts/donnees/comparer_zones.py`. Résultat complet : `data/extraits/zones_analogues_comparaison.csv`.

**Données utilisées pour chaque zone :**
- **Climat** (NASA POWER, moyennes de long terme) : température annuelle, température et humidité de la saison sèche fraîche (novembre à mars), pluie annuelle.
- **Sol** (iSDAsoil, 0-20 cm, moyenne d'un carré d'environ 630 m) : sable, argile, pH, carbone organique, capacité d'échange (CEC).

**Méthode :**
- Chaque écart à la moyenne des 4 points pilotes est divisé par une « différence notable » : 2 °C, 10 points d'humidité, 150 mm de pluie, 15 points de sable, 10 points d'argile, 0,5 de pH, 3 g/kg de carbone, 5 cmol/kg de CEC.
- Les écarts sont ensuite moyennés : 0 = identique aux Niayes ; 1 = en moyenne une différence notable sur chaque critère.
- **La salinité et la profondeur de la nappe ne sont pas comptées** : aucune carte ouverte ne les donne.

| Zone | Écart climat | Écart sol | Total | Sable | Argile | pH | Humidité saison fraîche | Pluie/an |
|---|---|---|---|---|---|---|---|---|
| Tivaouane (Niayes) | 0,06 | 0,35 | 0,20 | 80 % | 11 % | 6,5 | 51 % | 533 mm |
| Thiès (Niayes) | 0,30 | 0,20 | 0,25 | 73 % | 16 % | 6,4 | 48 % | 558 mm |
| Kébémer (Niayes) | 0,72 | 0,44 | 0,58 | 83 % | 10 % | 6,8 | 36 % | 478 mm |
| Gandiol (nord des Niayes) | 0,60 | 0,90 | 0,75 | 58 % | 27 % | 6,6 | 42 % | 380 mm |
| Rufisque (Niayes) | 0,90 | 0,71 | 0,80 | 61 % | 22 % | 6,9 | 74 % | 515 mm |
| Maradi (Niger) | 1,25 | 0,60 | 0,93 | 58 % | 22 % | 6,9 | 19 % | 551 mm |
| Nouakchott (Mauritanie, littoral) | 1,42 | 0,47 | 0,94 | 65 % | 20 % | 6,8 | 59 % | 150 mm |
| Dosso (Niger) | 1,63 | 0,38 | 1,00 | 63 % | 15 % | 6,2 | 20 % | 610 mm |
| Kaédi (station du CNRADA, vallée) | 1,70 | 0,51 | 1,10 | 61 % | 22 % | 6,5 | 22 % | 376 mm |
| Rosso (Mauritanie, vallée) | 1,26 | 0,94 | 1,10 | 50 % | 30 % | 6,7 | 30 % | 318 mm |
| Podor (Sénégal, vallée) | 1,53 | 0,77 | 1,15 | 54 % | 27 % | 6,8 | 26 % | 296 mm |

**Ce que ça montre :**
- **Les Niayes elles-mêmes varient** (écart total de 0,2 à 0,8) : Rufisque est plus argileuse et plus humide que Tivaouane ou Kébémer. Une zone étrangère autour de 1 est donc « un peu plus loin que les Niayes ne le sont d'elles-mêmes ».
- **Aucune zone étrangère n'est proche à la fois par le climat et par le sol.**
  - Le **Niger (Dosso)** a un sol très proche (sablo-limoneux, pH 6,2), mais un air beaucoup plus sec (20 % d'humidité contre 52 %).
  - **Nouakchott** a un sol et des températures proches, mais trois fois moins de pluie.
  - **Kaédi**, où le CNRADA a établi ses fiches, est plus chaud et plus sec que les Niayes.
- **Le pH ne départage pas les zones** : toutes sont entre 6,2 et 6,9, donc proches de la neutralité.

**Règle retenue : on choisit la zone de référence selon le type d'information.**

| Type d'information | Dépend surtout de | Où la prendre si le Sénégal ne dit rien |
|---|---|---|
| Écartements, profondeur de plantation, durée de pépinière, ordre des opérations | La plante elle-même | N'importe quelle fiche sourcée, en le signalant |
| Fumure de fond, fréquence d'arrosage, travail du sol | **Le sol** (sableux, pauvre en carbone) | Dosso ou Nouakchott (sols proches), en le signalant |
| Dates de semis, longueur du cycle, variétés selon la saison | **Le climat** (température) | Nouakchott (températures proches), à présenter comme un repère |
| Risque de maladies favorisées par l'humidité (mildiou, alternariose) | **L'humidité de l'air** | **Jamais** d'une zone sèche (Niger, Kaédi) : uniquement le Sénégal ou des modèles météo calculés sur nos données |
| Tolérance au sel | Le sel et la nappe, absents des cartes | Uniquement le guide ISRA 1987 et les études sur les Niayes |

Les informations des fiches du CNRADA (Kaédi) et du Niger restent signalées dans les fiches : « d'après une fiche de Mauritanie / du Niger ».

## 2. Par culture

### Oignon
- **Sources :** livret PIESAN, Ministère de l'Agriculture, *Bonnes pratiques de production d'oignon dans les Niayes*, 2022, en français et en wolof (cité **LIV** ; pages du PDF) ; fiche PADEN (ISRA-CDH) ; CNRADA ; FAO.
- **Variétés selon la période de semis (LIV p. 3) :**
  - octobre, primeur : Violet de Galmi, Texas Early Grano, Noflaye, Goldor, Gandiol F1, Orient F1, Red Passion, Goudamy ;
  - novembre et décembre, saison : les mêmes, plus Mercedes, Safari, Belami ;
  - janvier et février, arrière-saison : Red Creole, Yakar, Rouge d'Amposta, Jaune espagnol, Gao, Violet de Galmi, Orient F1, Gandiol F1.
- **Sol :** sableux à limono-sableux. Éviter les sols lourds et humides, et les précédents ail, oignon, persil (LIV p. 4-5).
- **Pépinière :**
  - planches de 5 × 1 m ; 2 à 3 kg/m² de fumure organique bien décomposée ; 4 à 6 g de graines par m² en lignes espacées de 10 cm ;
  - arrosage 5 à 6 L/m² par jour ;
  - plants arrachés à 5-6 feuilles, soit 45 à 50 jours (LIV p. 7-13).
- **Repiquage :** 10 cm sur la ligne, 20 cm entre lignes, tôt le matin ou en fin d'après-midi (LIV p. 18).
- **Entretien :** biner 4 à 5 fois ; arroser 5 à 6 L/m² par jour jusqu'à la formation du bulbe. Le livret souligne : « ne jamais utiliser d'urée en culture d'oignon » (LIV p. 17, 20-22).
- **Récolte :**
  - arrêter l'irrigation quand 30 % des feuilles jaunies sont couchées ;
  - récolter 10 à 15 jours après, soit un cycle de 70 à 120 jours selon la variété ;
  - sécher 1 à 2 jours au champ, puis stocker dans un endroit sec, frais et aéré (LIV p. 24-29).
- **Mauritanie (CNRADA) :** rendements de 35 à 50 t/ha pour le Violet de Galmi en station. Semis de novembre-décembre : les semis précoces allongent le cycle, les semis tardifs (après le 15 décembre) font baisser le rendement.
- **Ravageurs :** thrips (guide 1987) ; voir aussi les taches pourpres dans `docs/sources/seuils-meteo-maladies-ravageurs.md`.

### Tomate
- **Sources :** FAO/RADHORT/ISRA-CDH, *Techniques de production de semences de tomate au Sénégal* (cité **RAD**) ; CNRADA ; guide 1987.
- **Saison :** les meilleurs rendements s'obtiennent en saison sèche, avec des semis d'octobre à mars (RAD p. 6). CNRADA : semis en octobre-novembre, jusqu'en janvier en zone océanique.
- **Variétés du CDH (RAD p. 11-13) :**

| Variété | Caractéristiques | Rendement |
|---|---|---|
| Xina | Tolérante à la chaleur ; résiste au flétrissement fusarien et aux nématodes à galles | 30 à 60 t/ha |
| Xina Gros Fruits | Fruits plus gros que Xina | 20 à 40 t/ha |
| Romitel | Résiste aux nématodes et au flétrissement ; pour le concentré et le frais | — |
| AVRDC L-19 | Tolérante à la chaleur, très sensible aux nématodes | 30 à 60 t/ha |
| Tropiva 3 | Résiste aux nématodes | 25 à 50 t/ha |

- **Cycle :** 120 à 150 jours du semis à la fin de la récolte. La récolte commence 105 à 120 jours après le semis (RAD p. 11).
- **Seuils d'intervention en % de feuilles atteintes** (RAD p. 18, tableau de Production et Protection Intégrées) : par exemple 2 % pour l'alternariose à 14 jours après repiquage, puis un seuil qui augmente avec l'âge de la culture. Utile pour dire « surveillez », sans produit.
- **Écartement au Niger (Maradi), à titre indicatif :** 80 × 60 cm, tuteurage.

### Chou pommé
- **Sources :** **livret PADEN « Bonnes pratiques de production du chou pommé dans les Niayes »** (mars 2016, en français et en wolof, cité **PCH**) ; STDF/AUMN, rapport du projet PG 302 dans les Niayes (cité **STDF**) ; CNRADA ; Niger.
- **Variétés selon la période de repiquage (PCH p. 3)** : le chou pommé est une culture de contre-saison sèche.

| Variété | Repiquage | Jours jusqu'au début de récolte | Jours jusqu'à la fin |
|---|---|---|---|
| KK Cross F1 | octobre à juillet | 60 | 75 |
| Tropica Cross F1 | octobre à juillet | 65 | 90 |
| Santa F1 | octobre à avril | 68 | 95 |
| Tropicana F1 | illisible dans l'extraction, à relire sur le PDF | 75 | 108 |
| Marché de Copenhague | octobre à mars | 63 | 75 |
| Africa Cross F1 | avril à juillet | 78 | 100 |

Les colonnes de jours sont lues dans l'ordre du tableau ; leur sens exact (après repiquage ?) est à relire sur le PDF avant d'écrire la fiche.
- **Niayes (STDF p. 5) :** **février est la période de forte infestation** de la teigne et du borer du chou. Les rendements des essais vont de 17 t/ha (parcelles témoins) à 24 t/ha avec une protection biologique.
- **Saison des pluies (STDF p. 6-9) :** variété Tropica Cross, adaptée à l'hivernage, semée de mai à août. Il faut 200 m² de pépinière pour 1 ha ; repiquage environ 29 jours après le semis.
- **Mauritanie (CNRADA) :**
  - saison froide : Marché de Copenhague, Acre d'Or, 15 à 25 t/ha, semis de septembre à avril ;
  - hivernage en zone côtière : Summer H-50, Fabula H, Green Express, 10 à 15 t/ha, semis de mai à juillet.
  - La fiche écrit « 300 t/ha d'engrais minéral », une coquille évidente (sans doute 300 kg/ha) : à ne pas recopier.
- **Niger :** le chou tolère mal la salinité ; il demande beaucoup d'eau.

### Pomme de terre
- **Sources :** **fiche PADEN de production intensive de la pomme de terre** (A. Seck, janvier 2014, cité **PPT**) et livret PADEN pomme de terre (2016, en français et en wolof) ; CNRADA ; guide 1987 ; Niger (Dosso).
- **Niayes (PPT p. 2)** :
  - sol léger, riche en matière organique, pH neutre ;
  - éviter les précédents solanacées (tomate, aubergine, jaxatu, piment) ;
  - les fortes températures nuisent à la formation des tubercules, d'où la saison fraîche ;
  - plus de 20 variétés conseillées par l'ISRA ; variétés courantes : Sahel, Claustar, O'sirène, Alpha…
- **Trois périodes de culture (PPT p. 2)** : hâtive (octobre-novembre), pleine saison (novembre-février), tardive (mars-avril).
- **Densité (PPT p. 4)** : environ 66 700 plants par hectare, avec des tubercules entiers de 30 g ou des moitiés de tubercules de 50 g.
- **Sol :** léger, sableux ou sablo-limoneux, riche en matière organique bien décomposée (CNRADA).
- **Plantation :** première quinzaine de novembre pour une récolte en février. En zone océanique, on peut planter jusqu'en février pour récolter en mai.
- **Écartement :** 30 × 60 cm, soit environ 56 000 plants par hectare.
- **Cycle :** au plus 100 jours de la plantation à la fin de la récolte.
- **Variétés citées en Mauritanie :** Lola, Claustar (30 à 40 t/ha), Sahel (25 à 40 t/ha), Thalassa (25 à 45 t/ha), Spunta, Désirée…

### Poivron
- **Sources :** CNRADA ; Niger (Dosso) ; guide 1987.
- **Variétés et rendements (Mauritanie) :** Yolo Wonder et Tambell-2 (10 à 25 t/ha selon la période), Bombay F1 (15 à 25 t/ha).
- **Écartement :** 50 × 50 cm.
- **Récolte :** dès 2 mois après la plantation, deux fois par semaine pendant environ 2 mois.
- **Pépinière :** à protéger sous moustiquaire à cause des nombreux ravageurs (CNRADA). Cela rejoint le conseil de la fiche KCOA pour la tomate.

### Piment
- **Source :** CNRADA.
- **Saison :** toute l'année ; meilleurs résultats en saison sèche froide (décembre à février).
- **Écartement :** 0,4 × 0,6 m.
- **Arrosage :** le sol doit rester humide sans excès, sinon les fleurs tombent.

### Jaxatu (aubergine amère)
- **Source :** CNRADA.
- **Variétés :** Soxna (CDH), 15 à 20 t/ha ; Bobo Dioulasso, 15 à 18 t/ha ; Ouagadougou, 18 t/ha.
- **Saison :** toute l'année, meilleure en saison sèche et fraîche.
- **Pépinière :** 30 à 40 jours.
- **Écartement :** 50 × 60 cm.
- **Ravageurs :** nématodes à galles en sol sableux ; une petite cicadelle verte qui pique les feuilles (nécroses brunes, puis les feuilles jaunissent et tombent).

### Carotte
- **Source :** CNRADA.
- **Cycle :** 90 à 110 jours ; il faut des températures basses.
- **Variétés :** Chantenay, Nantaise améliorée, Touchon, 20 à 40 t/ha.
- **Ravageurs et maladies :** nématodes ; alternariose, importante en saison chaude et humide.

## 3. Ce qui manque encore

- **Fiches ISRA-CDH 2022** : à demander au CDH par le formulaire de contact de isracdh.sn ou au CDH de Cambérène. Bonus.
- ~~Fiche PADEN pomme de terre (2014)~~ : **trouvée le 4 nov 2026** dans les archives du site du PADEN (Wayback Machine), avec les livrets chou, pomme de terre, oignon et carotte, et le manuel des ravageurs de la DPV.
- **Tomate, poivron, piment :** aucun livret sénégalais équivalent à ceux du PADEN (oignon, chou, pomme de terre, carotte). Les fiches CNRADA servent de remplacement, en le signalant.
- **Rendements réels des petits producteurs des Niayes** : les rendements des sources sont ceux des stations de recherche, souvent bien au-dessus du champ. Les données EAA (production par ménage) restent un ordre de grandeur.

## 4. Bonus : du wolof sourcé

Le livret PIESAN est bilingue français-wolof. Il donne des mots wolof écrits pour les maraîchers des Niayes : *soble* (oignon), *pepiñeer* (pépinière), *jëmbët* (repiquer), *tos* (fumier), *angare* (engrais), *suuxat* (arroser), *feebar* (maladie), *gunóor* (ravageurs), *tool* (champ), *goob* (récolte), *xob* (feuille), *saako* (sac), et les mois *Octoobar*, *Noovambar*, *Desambar*, *Saawiee*, *Feewiryee*. Ils sont ajoutés au lexique de prononciation avec le statut « à valider par un locuteur ».

## Sources

- Livret PIESAN oignon (2022) : <https://agriculture.gouv.sn/wp-content/uploads/2022/06/Livret-oignon-francais-wolof.pdf>
- Fiche PADEN oignon : <https://duddal.org/files/original/39a30d91086dcdf5d3705b8973c518d6be6d6356.pdf>
- Guide pratique du maraîchage au Sénégal (1987) : <https://open-library.cirad.fr/files/4/751__Guide_pratique_du_maraichage_au_Senegal.pdf>
- FAO/RADHORT, semences de tomate au Sénégal : <http://www.fao.org/3/az783f/az783f.pdf> (copie <https://duddal.org/files/original/3b6754ae5981f3846f3b1cdf425dd647eaf5498c.pdf>)
- FAO, production précoce de l'oignon : <https://openknowledge.fao.org/server/api/core/bitstreams/87539e9a-3717-4361-8937-06ad2c7a17af/content>
- STDF/AUMN, chou dans les Niayes : <https://www.standardsfacility.org/sites/default/files/PG_302_ProjectActivities_Report.pdf>
- CNRADA, fiches techniques maraîchères : <https://cnrada.org/fiches-techniques/cultures-maraicheres/>
- Niger : chou <https://duddal.org/files/original/42982ad5f9b03fb4a86fbc3a9d146a07de108252.pdf>, tomate Maradi <https://duddal.org/files/original/e7629bcc5033ce35fe07dc456a3bae3091d7f291.pdf>, poivron Dosso <https://reca-niger.org/IMG/pdf/FT_Poivron_CRADosso_V1.pdf>, pomme de terre Dosso <https://reca-niger.org/IMG/pdf/FTE_pommeDterre_Dosso_Mai2017.pdf>
- ISRA-CDH, site officiel : <https://isracdh.sn/fiches-techniques.php>
- PADEN (Programme d'aménagement et de développement économique des Niayes), documents archivés : <https://web.archive.org/web/2017/http://www.paden-senegal.org/Documents-et-outils,25.html> ; liste et adresses exactes dans `scripts/donnees/telecharger_sources.py` (source `paden`)
