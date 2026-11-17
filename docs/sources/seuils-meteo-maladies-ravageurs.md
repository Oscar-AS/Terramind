# Seuils météo des maladies et ravageurs (module Prévention)

Recherche du 2 nov 2026. Complète le § 5 de [research/base-de-travail-agronomique.md](../../research/base-de-travail-agronomique.md).

**Avertissement commun** : aucun de ces modèles n'a été validé au Sénégal. Ils viennent d'Europe, d'Amérique du Nord ou d'Amérique du Sud. Le bot doit parler de « conditions favorables à… », jamais d'un diagnostic, et proposer des gestes de prévention sans produit. Les données météo disponibles (NASA POWER, maille d'environ 50 km) ne mesurent pas l'humidité sous le feuillage : c'est une approximation.

## 1. Ce qu'on peut calculer avec nos données

NASA POWER donne, heure par heure, la température (`T2M`) et l'humidité relative (`RH2M`). Il n'y a pas de capteur d'humectation des feuilles : on l'estime par **le nombre d'heures où l'humidité relative est ≥ 90 %**. C'est la méthode la plus simple qui ait été évaluée, avec 87 à 92 % d'estimations correctes selon les sites (Sentelhas et al. 2008). Mais elle a été testée avec des stations au champ, pas avec des données en grille.

## 2. Maladies

| Maladie (cultures) | Règle | Données | Source |
|---|---|---|---|
| **Mildiou** (*Phytophthora infestans* ; tomate, pomme de terre) | **Critères Hutton** : 2 jours de suite avec une température minimale ≥ 10 °C **et** au moins 6 h d'humidité ≥ 90 % chaque jour. L'ancienne « période de Smith » demandait 11 h. | T2M, RH2M horaires | AHDB / James Hutton Institute, Dancey, Skelsey et Cooke 2017 |
| **Alternariose** (*Alternaria solani* ; tomate, pomme de terre) | **TOMCAST** : chaque jour, une note de 0 à 4 selon les heures d'humectation et la température moyenne pendant ce temps (tableau ci-dessous). On cumule les notes ; une alerte à partir de 15 à 20 points cumulés. | Heures RH ≥ 90 %, T2M | Madden, Pennypacker et MacNab 1978 (FAST) ; tableau TOMCAST de UC IPM |
| **Taches pourpres** (*Alternaria porri* ; oignon) | Conditions favorables : 21 à 30 °C (optimum vers 25 °C) avec de longues rosées. Infection à partir d'environ 8 à 16 h d'humectation ; presque pas d'infection sous 13 °C. Les dégâts de thrips l'aggravent. | Heures RH ≥ 90 %, T2M | Suheri et Price 2000 (*Plant Pathology*) ; fiches de vulgarisation. Seuils exacts à relire dans l'article |
| **Mildiou de l'oignon** (*Peronospora destructor*) | **DOWNCAST** (sporulation la nuit) : température moyenne de 8 h à 20 h la veille < 24 °C, nuit (20 h - 6 h) entre 4 et 24 °C en moyenne, humidité > 95 % de 2 h à 6 h, pas de pluie après 1 h. Freinée au-dessus de 27,5 °C. **En service depuis le 14 nov 2026.** Pluie : nuit écartée si plus de 1 mm de 23 h à 4 h (seuil chiffré de la version du Queensland, AUSVEG VG97024 p. 3 et VG402 p. 10-11 ; l'original dit « pas de pluie après 1 h »), avec PRECTOTCORR horaire de NASA POWER (mm/h). Limite : cette pluie de modèle contient de la bruine et des valeurs aberrantes au point pilote (238 mm le 29 mars 2025 contre 0 mm pour ERA5) ; les nuits écartées pour la pluie sont comptées dans la réponse. | T2M, RH2M horaires | Jesperson et Sutton 1987 (*Crop Protection* 6:95-103) ; critères détaillés dans AUSVEG VG203 et VG402, et *Agronomy* 10:738 (2020) ; Hildebrand et Sutton 1982 ; UC IPM |
| **Alternariose de la carotte** (*Alternaria dauci* ; aussi *Cercospora carotae*) | **TOMCAST**, alerte à **15** points cumulés : seuil validé au champ sur carotte (Michigan, 3 systèmes de production). **En service depuis le 14 nov 2026.** | Heures RH ≥ 90 %, T2M | *Plant Disease* 90:264 (2006) ; *Plant Disease* 93:402 (2009, seuils 10, 15, 20) ; Cornell, *Carrot Leaf Blight Diseases and their Management in New York* |

Tableau TOMCAST (note du jour selon les heures d'humectation et la température moyenne pendant l'humectation, d'après UC IPM) :

| Température moyenne | Note 0 | Note 1 | Note 2 | Note 3 | Note 4 |
|---|---|---|---|---|---|
| 13–17 °C | 0–6 h | 7–15 h | 16–20 h | 21 h et plus | — |
| 18–20 °C | 0–3 h | 4–8 h | 9–15 h | 16–22 h | 23 h et plus |
| 21–25 °C | 0–2 h | 3–5 h | 6–12 h | 13–20 h | 21 h et plus |
| 26–29 °C | 0–3 h | 4–8 h | 9–15 h | 16–22 h | 23 h et plus |

## 3. Ravageurs (modèles en degrés-jours)

Principe : chaque jour, l'insecte « gagne » (température moyenne − seuil bas) degrés. Une génération est bouclée quand la somme atteint la constante thermique. Cela sert à dire « une nouvelle génération est attendue vers telle date : surveillez ».

| Ravageur (cultures) | Seuil bas | Degrés-jours œuf → adulte | Source |
|---|---|---|---|
| **Mineuse de la tomate** (*Tuta absoluta*) | ≈ 8 °C (7,8 à 8,1 °C selon les analyses) | ≈ 417 à 454 | Barrientos et al. 1998 ; Krechemer et Foerster 2015 ; fiche USDA CAPS |
| **Teigne du chou** (*Plutella xylostella*) | ≈ 7 °C (6,3 à 7,8 °C) | ≈ 260 à 312 au laboratoire ; 283 à 353 au champ | Golizadeh et al. 2007 ; Marchioro et Foerster 2011 ; UC IPM |
| **Noctuelle des fruits** (*Helicoverpa armigera* ; poivron, piment, jaxatu, tomate) | 10,7 °C | 521 (œuf 43 + larve 287 + nymphe 191) ; **en service depuis le 15 nov 2026** | Jung et al. 2023, *J. Econ. Entomol.* 116:1689, doi 10.1093/jee/toad133 (laboratoire, validation en semi-champ, Corée) |
| **Aleurode**, vecteur du virus TYLCV (*Bemisia tabaci* ; tomate) | ≈ 8,5 à 10 °C sur tomate | ≈ 285 sur tomate, cité de seconde main ; 300 à 370 sur d'autres plantes | Études de laboratoire (biotypes B et Q) ; valeur tomate à confirmer |

Dans les Niayes, la température moyenne dépasse presque toujours ces seuils. Les générations s'enchaînent donc toute l'année : 2 à 4 semaines par génération selon la saison. L'intérêt du modèle est surtout de **dater les pics** pour rappeler de surveiller, pas de déclencher une alerte unique.

## 4. Ce que disent les données sénégalaises sur le besoin

D'après l'EAA 2022-2023 (DAPSA), extraits dans `data/extraits/` :
- **Ravageurs :** 43,9 % des ménages agricoles de Louga et 20,6 % de ceux de Thiès ont subi un « taux élevé et inhabituel de ravageurs » (15,3 % au niveau national). Les Niayes sont donc particulièrement touchées.
- **Traitements :** des insecticides sont utilisés sur 99 % des parcelles de chou, 97 % de la tomate cerise et 78 % de l'oignon. Les fongicides le sont sur 57 %, 30 % et 15 %.

**Conséquence proposée pour le module Prévention :** ne pas s'en tenir au mildiou. Ajouter au moins la mineuse de la tomate et la teigne du chou (degrés-jours) et l'alternariose (TOMCAST). Décision à prendre en équipe.

## 5. Premier test : l'épisode de février 2026 (Notto Gouye Diama, département de Tivaouane)

Calcul fait le 2 nov 2026 avec NASA POWER horaire au centroïde du département de Tivaouane (15,088 N ; −16,652 E), du 1ᵉʳ déc 2025 au 28 févr 2026, en heure locale :
- **Critères Hutton remplis** les 3 au 6 janvier, 3 au 6 février, 12 février et 27-28 février 2026. Les symptômes rapportés par la presse datent du **17 février 2026**, soit 5 à 14 jours après les déclenchements de février. C'est cohérent avec le délai d'incubation et de visibilité.
- **Période de Smith** (11 h) : seulement les 3 au 5 janvier.
- **Le facteur limitant est l'humidité, pas la température :** la minimale moyenne était de 16,8 à 17,3 °C, avec en moyenne 0,7 h par jour à 90 % d'humidité en décembre, 2,2 h en janvier et 2,9 h en février.

**Limites :** un seul épisode, non confirmé par un diagnostic. Le point de grille est différent du champ, et on ne connaît pas de « faux positif » (les alertes de janvier n'ont pas été suivies d'un signalement connu). Il ne faut donc pas présenter ce résultat comme une validation.

## 5 bis. Deuxième test : le calendrier des règles sur 2020-2025 (4 nov 2026)

Script : `python3 -I scripts/donnees/tester_modeles_prevention.py`. Résultat : `data/extraits/prevention_calendrier_2020-2025.csv`.

Les règles tournent sur la météo heure par heure de NASA POWER (2020 à 2025, 4 points pilotes), puis on compare leur calendrier aux saisons d'attaque documentées dans les Niayes. Ce n'est pas une validation au champ : aucune observation par parcelle n'existe.

**Saisons documentées :**
- mineuse de la tomate : de février à mai (thèse de S. Sylla) ;
- teigne du chou : pic en février (rapport STDF/AUMN) ;
- alternariose : 20 à 25 °C avec alternance de périodes humides et ensoleillées (manuel de la DPV, p. 80) ;
- mildiou : signalé dans les Niayes par la DPV (p. 88) ; épisode de février 2026 à Notto Gouye Diama.

| Règle | Ce que donne le calcul | Concordance avec le terrain |
|---|---|---|
| **Mildiou** (Hutton), jours d'alerte par mois | Saison fraîche (novembre à février) : 0,3 à 4 jours. **Hivernage** (août à octobre), à l'intérieur : **15 à 26 jours**. Rufisque (côte) : pic de **mars à mai** (8 à 16 jours) | Partielle. La règle se déclenche surtout en hivernage, quand on cultive peu de tomates et de pommes de terre. Elle a été conçue pour le Royaume-Uni et n'a **pas de plafond de température**, alors que le mildiou ralentit par forte chaleur |
| **Alternariose** (TOMCAST), notes cumulées par mois | Maximum en hivernage (40 à 60) ; 1 à 14 en décembre-février ; pic de mars à mai à Rufisque | Cohérent avec le CNRADA (« dégâts importants en saison chaude et humide »). Même limite : la culture doit être en place |
| **Mineuse**, durée d'une génération | 21 à 34 jours toute l'année : plus longue de décembre à mars, plus courte de juin à octobre | Les degrés-jours **seuls n'expliquent pas** le pic de février à mai. En revanche, une tomate repiquée début décembre en est à 2 à 6 générations entre février et mai : **la population s'accumule pendant la culture** |
| **Teigne du chou**, durée d'une génération | 13 à 21 jours toute l'année | Un chou repiqué mi-novembre en est à environ 5 générations mi-février, ce qui concorde avec le pic de février |

**Conséquences pour la conception des alertes (à intégrer au module Prévention) :**
1. **Aucune alerte sans culture déclarée.** L'alerte mildiou ou alternariose ne part que si l'agriculteur a déclaré une tomate ou une pomme de terre en place. Sinon, en hivernage, elle partirait presque tous les jours, et les agriculteurs cesseraient de lire les alertes.
2. **Ravageurs : compter les générations depuis le repiquage** (date demandée à l'agriculteur), et rappeler de surveiller à partir de la 3e génération. Une alerte selon la seule saison serait trop vague.
3. **Mildiou : plafond de température trouvé (5 nov 2026).** Le modèle de Wallin, base de Blitecast, ne compte les heures humides que si leur température moyenne est comprise entre **7,2 et 26,6 °C** (Wallin 1951, 1962 ; tableau UC IPM). La littérature concorde : formation des spores optimale vers 15 à 20 °C ; quasi nulle à 28 °C (*Plant Disease* 2005, tomate et pétunia) ; aucune germination à 27 °C (*Plant Disease* 2009, souches brésiliennes).
   - Ajouté au test sous le nom « Hutton plafonné » : une heure humide ne compte que si la température est ≤ 26,6 °C.
   - **Effet faible** : à l'intérieur des terres, en hivernage, les heures humides tombent la nuit, sous 26,6 °C. Le mildiou y est donc réellement favorisé (Thiès en septembre : 25,7 jours d'alerte sans plafond, 20,5 avec). Le plafond ne supprime que les alertes d'hivernage de Rufisque et une partie de celles de Thiès.
   - **Conclusion :** le plafond s'ajoute à la règle, mais le filtre principal reste la culture déclarée.
4. **Rufisque se comporte différemment** (humidité marine de mars à mai) : garder un calcul par point, pas une moyenne de la zone.

## 6. Salinité (module Planification)

Aucune carte ouverte ne donne la salinité des sols des Niayes à l'échelle du champ. Les études publiées confirment pourtant que c'est un vrai problème :
- **Causes :** salinisation de la nappe par le déficit de pluie, la surexploitation de la nappe et l'intrusion d'eau de mer.
- **Où :** dans les **bas-fonds et cuvettes** proches de la nappe, et davantage au nord (Gandiolais) et dans le sud près des lacs. Les hauts de dune sont en général non salins.
- **Exemples chiffrés :** eau d'arrosage « extrêmement saline » à Keur Saer et Deggu (CE de 4 414 à 5 843 µS/cm) ; abandon de terres autour du lac Wouye (92 ha) et du lac Tanma.

**Conséquence :** l'application **demande à l'agriculteur** si l'eau de son puits est salée et si son champ est en bas-fond. Elle croise ensuite sa réponse avec le tableau de tolérance des cultures à la salinité du guide ISRA de 1987 (tableau 1, p. 5).

Études :
- Ndiaye et al. 2012, *Caractérisation des sols de la zone des Niayes de Pikine et de Saint-Louis*, IJBCS. <https://www.ajol.info/index.php/ijbcs/article/view/80522>
- Diallo et al. 2015, *Étude comparative de la salinité de l'eau et des sols dans la zone nord des Niayes*, African Crop Science Journal 23(2):101-111. <https://www.ajol.info/index.php/acsj/article/download/117728/107356>
- *Les Niayes du littoral nord du Sénégal : processus de mise en place, salinisation des eaux souterraines et des sols*, European Scientific Journal, 2022. <https://eujournal.org/index.php/esj/article/view/16099>
- *Caractérisation agropédologique des sols de Mboltime (Niayes)*. <https://www.researchgate.net/publication/279204557>

## Sources (seuils)

- AHDB, critères Hutton : <https://potatoes.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria> ; fiche IPM Decisions : <https://www.ipmdecisions.net/documents/factsheet-hutton-criteria-late-blight-model/>
- TOMCAST, tableau des notes : UC IPM <https://ipm.ucanr.edu/DISEASE/DATABASE/dsvtable.html> ; Madden et al. 1978, *Phytopathology* 68:1354 <https://www.apsnet.org/publications/phytopathology/backissues/Documents/1978Articles/Phyto68n09_1354.pdf>
- Humectation estimée par l'humidité : Sentelhas et al. 2008, *Agric. For. Meteorol.* 148:392-400 <http://www.leb.esalq.usp.br/agmfacil/artigos/artigos_sentelhas_2008/2008-A&FMeteor_148(2-4)_392-400_LWD-RH.pdf>
- *Alternaria porri* : Suheri et Price 2000, *Plant Pathology* <https://bsppjournals.onlinelibrary.wiley.com/doi/10.1046/j.1365-3059.2000.00458.x>
- DOWNCAST : Jesperson et Sutton 1987, *Crop Protection* 6:95-103 ; synthèse dans *Agronomy* 2020, 10(5):738 <https://doi.org/10.3390/agronomy10050738> ; UC IPM <https://ipm.ucanr.edu/agriculture/onion-and-garlic/downy-mildew/>
- *Tuta absoluta* : fiche USDA CAPS <https://caps.ceris.purdue.edu/wp-content/uploads/2025/07/Phthorimaea-absoluta-CAPS-datasheet-20250328.pdf> ; Krechemer et Foerster 2015, *Eur. J. Entomol.* <https://www.eje.cz/pdfs/eje/2015/04/11.pdf>
- *Plutella xylostella* : Marchioro et Foerster, *Neotropical Entomology* <https://www.scielo.br/j/ne/a/9V8C8KkhNKGzVNJfYdx6hDB/?lang=en> ; Golizadeh et al. 2007 <https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1744-7917.2007.00157.x> ; UC IPM <https://ipm.ucanr.edu/PHENOLOGY/ma-diamondback_moth.html>
- Plafond de température du mildiou : modèle de Wallin, UC IPM <https://ipm.ucanr.edu/DISEASE/DATABASE/potatolateblight.html> ; *Plant Disease* 89:975 (2005) <https://apsjournals.apsnet.org/doi/pdf/10.1094/PD-89-0975> ; *Plant Disease* 93:459 (2009) <https://apsjournals.apsnet.org/doi/pdf/10.1094/PDIS-93-5-0459>
- Manuel de la DPV (Direction de la Protection des Végétaux), *Principaux ravageurs et maladies des cultures maraîchères dans la zone des Niayes*, M. Ndiaye, diffusé par le PADEN (copie Wayback) : alternariose p. 80, mildiou p. 88, mineuse p. 28, teigne p. 18
- *Bemisia tabaci* : synthèses de laboratoire <https://www.researchgate.net/publication/227697488_Modelling_temperature-dependent_bionomics_of_Bemisia_tabaci_Q-biotype> ; <https://akjournals.com/downloadpdf/journals/038/49/2/article-p289.pdf>

## 7. Poivron, piment, jaxatu : recherche du 15 nov 2026

- Règle en service : noctuelle des fruits (tableau des ravageurs). Sans date de plantation, le moteur répond « date requise » au lieu de se taire.
- Pistes sourcées mais non mises en service (valeurs de laboratoire, à décider) : mouches des fruits *Bactrocera dorsalis* (≈ 9 °C, ≈ 376 degrés-jours, Rwomushana et al. 2008) et *Ceratitis capitata* (9,1-9,6 °C, 328-350, *J. Insect Sci.* 12:33, 2012) ; acarien *Polyphagotarsonemus latus* (10 °C, 66,7, Luypaert et al. 2014, sur azalée) ; anthracnose du piment (Kang, Yun et Park 2010, *Plant Pathol. J.* 26:17, demande un capteur d'humectation et la pluie horaire, validé en Corée).
- Écartées faute de modèle publié : oïdium (*Leveillula taurica*), *Phytophthora capsici*, galle bactérienne, cercosporiose, alternariose du jaxatu, cicadelle *Jacobiasca lybica*, thrips locaux, virus.
