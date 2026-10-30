# Base de travail agronomique (BROUILLON)

> **⚠️ BROUILLON, NON VALIDÉ PAR UN AGRONOME. Ce n'est pas du contenu final.**
>
> Pour Rama : ce document te donne seulement une **base de départ** pour la table sol → culture et les fiches maladies (échéance du 6 nov). Il rassemble ce que disent des sources publiques, chaque information avec sa source et sa page. Rien ici ne doit aller tel quel dans les gabarits ou le produit : tout reste à relire, corriger, compléter et faire valider par l'agronome.
>
> Préparé le 30 oct 2026 par Salam, avec une recherche assistée par IA (Claude). Méthode, requêtes et sources consultées : [docs/sources/journal-recherche-agronomique.md](../docs/sources/journal-recherche-agronomique.md).

**Conventions**

- **[G87 p. X]** = *Guide pratique du maraîchage au Sénégal*, J. Beniest et al., ISRA / FAO, Centre pour le Développement de l'Horticulture (CDH), Cambérène, 1987. C'est la source principale : la seule source institutionnelle sénégalaise complète que nous ayons pu lire en entier. Le numéro de page est celui imprimé dans le livre.
- **À vérifier** : le texte du guide est un scan. Quand la lecture est douteuse, c'est signalé.
- **À sourcer** : connaissance générale que nous n'avons pas encore rattachée à une source précise. Ne pas utiliser avant d'avoir la source.
- **Aucun dosage, aucun produit chimique** n'est repris ici, même quand la source en donne (règle du projet). Le guide de 1987 cite des pesticides dont certains sont aujourd'hui interdits ; ils ont été volontairement écartés.

---

## 1. Ce qu'il faut savoir avant de commencer

1. **Les fiches officielles les plus récentes existent, mais nous ne les avons pas.** L'ISRA a réactualisé en 2022, avec deux projets USAID, les itinéraires techniques de 20 cultures maraîchères (tomate, oignon, pomme de terre, chou, poivron, piments, aubergine, carotte, etc.). Aucun lien de téléchargement n'est publié sur la page de l'ISRA. Le site qui hébergeait des fiches ISRA-CDH (marcheagricole.sn) était inaccessible le 30 oct 2026. **Action : demander ces fiches 2022 au CDH Cambérène ou par l'encadreur.** Elles remplaceraient avantageusement le guide de 1987.
2. **Aucune fiche ANCAR téléchargeable n'a été trouvée** (confirme ce que disait le plan de tâches).
3. **Le mildiou n'apparaît pas dans le guide de 1987**, ni pour la tomate ni pour la pomme de terre, et nous n'avons trouvé aucune étude scientifique sur le mildiou au Sénégal. Par contre, un article de presse du **17 février 2026** signale des symptômes « qui ressemblent au mildiou » sur pomme de terre et tomate à **Notto Gouye Diama** (département de Tivaouane, Niayes), sans diagnostic officiel. Voir § 5 : c'est un point à discuter en équipe, car le module Prévention est construit autour du mildiou.
4. **Le maïs n'est pas couvert par le guide maraîcher**, et nous n'avons trouvé aucune source sénégalaise sur ses maladies des feuilles (celles de PlantVillage). Le problème majeur documenté au Sénégal sur le maïs est un insecte, la chenille légionnaire d'automne, que PlantVillage ne couvre pas. À peser dans la décision du 4 nov.

---

## 2. Zone pilote : les Niayes

**Géographie et saisons**

- Bande côtière de 15 à 20 km de large le long de l'Atlantique, au nord de Dakar. De novembre à mai-juin, l'alizé maritime y maintient des températures relativement fraîches, favorables aux légumes « de type européen » (pomme de terre, oignon, tomate, chou, carotte) [G87 p. VII].
- Calendrier officiel du recensement (ANSD, RGPH-5, 2024) : **contre-saison froide** d'octobre à mars, **contre-saison chaude** d'avril à juin, puis **hivernage** (saison des pluies). En contre-saison froide, les cultures les plus répandues sont l'oignon (44,2 %), la tomate (43,5 %) et le piment (41,5 %) (*base de calcul de ces pourcentages à relire dans le rapport*).
- Les Niayes fournissent environ 60 % de la production maraîchère nationale (SONED 2013, cité par De Bon et al., *Cahiers Agricultures*, 2019).

**Sols** (à confronter avec la sortie de `sol(lat, lon)` d'Oscar)

| Type local | Texture (40 premiers cm) | pH observé | Source |
|---|---|---|---|
| **Dior** (dunes) | sableuse ou sablo-limoneuse, moins de 10 % d'argile | 5 à 6 dans les profils décrits | Ministère de l'Agriculture, typologie des sols (dépôt WUR) |
| **Dior** des Niayes | 90 à 95 % de sables, très peu de carbone | 5,5 à 6,5 (légèrement acide) | De Bon et al., 2019 |
| **Dior-deck** | sablo-limoneuse (plus de 10 % d'argile) ou limon très sableux | environ 6,5 en surface, 5,6 à 5,7 en profondeur | Ministère de l'Agriculture, typologie des sols |
| **Cuvettes / bas-fonds** (Niayes nord) | riches en matière organique | peut être très acide (3,8 à 4,3 à Potou) ; salinisation côté littoral | Études Mboltime et Niayes nord (ResearchGate) |

Conséquences pratiques tirées du guide :

- **pH idéal pour le maraîchage : 6 à 7.** Un sol acide se corrige par chaulage, après analyse [G87 p. 9 et 11].
- **Salinité** : les légumes la supportent mal, dans le sol comme dans l'eau d'arrosage. Certains puits des Niayes deviennent salés avec le temps (conseiller ANCAR cité dans un rapport CIRAD de 2016). En cas de doute : analyse de l'eau et du sol [G87 p. 5 et 11].
- **Sols trop humides** (bas-fonds, bords de lacs) : à éviter, surtout pour l'oignon et la pomme de terre [G87 p. 11].
- Les sols sableux retiennent mal l'eau et les éléments nutritifs : arroser plus souvent mais avec des doses plus petites ; la matière organique améliore la rétention [G87 p. 5 et 9].

---

## 3. Brouillon de table sol → culture (8 cultures candidates)

Version tableur : [brouillon_table_sol_culture.csv](brouillon_table_sol_culture.csv) (mêmes données, une ligne par culture).

**Deux tableaux officiels du guide servent de base :**

*Tolérance au pH du sol* [G87 p. 11, Tableau 3] :
- **craignent l'acidité** (préférence pH 6 à 6,8) : chou cabus, chou-fleur, laitue, melon, **oignon**, poireau, épinard, betterave ;
- **tolérantes** (pH 5,5 à 6,8) : **aubergine, carotte, poivron, tomate**, ail, concombre, courgette, haricot, navet, persil, pois, radis ;
- **très tolérantes** (pH 5 à 6,8) : **pomme de terre**, patate douce, pastèque, échalote, chicorée, oseille.

*Sensibilité à la salinité de l'eau d'irrigation et du sol* [G87 p. 5, Tableau 1] :
- **très sensibles** : **carotte, oignon**, haricot, radis, laitue, fraise, céleri, petit pois, et **les semis et jeunes repiquages de toutes les cultures** ;
- **moins sensibles** : **piment, pomme de terre, chou, tomate, aubergine, jaxatu**, patate douce, melon, concombre, courge, gombo, pastèque, manioc, bissap ;
- **peu sensibles** : betterave, chou-rave, asperge, épinard.

**Tableau par culture** (tout vient du guide de 1987, sauf mention)

| Culture | Sols préférés | pH | Salinité | Semis | Plantation | Durée au champ | Meilleure saison | Pages |
|---|---|---|---|---|---|---|---|---|
| **Tomate** | pas trop lourds, profonds, meubles, riches en éléments nutritifs et en matière organique | 5,5 à 6,8 | moins sensible | sept. à avril en pépinière (25 à 40 j) ; toute l'année pour les variétés d'hivernage | oct. à mai | 110 à 150 j ; 1re récolte 60 à 80 j après plantation | saison fraîche et sèche (déc. à juillet) ; hivernage possible avec rendements plus faibles | 139-141 |
| **Pomme de terre** | plutôt légers, pas trop humides, assez riches, matière organique bien décomposée | 5 à 6,8 | moins sensible | pas de semis : tubercules prégermés | zones favorables : oct.-nov. (hâtive), déc.-janv. (pleine saison), févr.-mars (tardive) ; zones moins favorables : nov.-déc. | 75 à 100 j | saison fraîche | 133-135 |
| **Oignon** | pas trop lourds, ni gorgés d'eau, assez riches, matière organique bien décomposée | 6 à 6,8 (craint l'acidité) | **très sensible** (sol et eau) | nov. à janv. en pépinière (40 à 55 j) ; bulbilles : semis fin mars-avril | repiquage déc. à mars ; bulbilles : oct.-nov. | 110 à 150 j (repiquage) ; 90 à 100 j (bulbilles) | saison fraîche et sèche | 119-120 |
| **Chou** | riches en matière organique, bonne humidité du sol et de l'air ; exigeant en azote | 6 à 6,8 (chou cabus craint l'acidité) | moins sensible | sept. à avril (saison fraîche) ; mai à juillet (variétés d'hivernage) ; pépinière 25 à 35 j | après la pépinière | 80 à 100 j après plantation (60 j en hivernage) | saison sèche et fraîche | 89-90 |
| **Poivron** | ni trop lourds, ni trop légers, profonds, bien drainés, riches | 5,5 à 6,8 | non indiqué dans le Tableau 1 | sept.-oct. à févr. en pépinière (30 à 45 j) | oct. à mars | 120 à 180 j | saison sèche et fraîche (la chaleur fait chuter fleurs et fruits) | 129-130 |
| **Piment** | pas trop légers mais bien drainés, riches | non indiqué dans le Tableau 3 | moins sensible | toute l'année en pépinière (45 à 60 j) | toute l'année | 6 à 8 mois, dont 3 à 4 de récolte (*à vérifier*, p. 128) | hivernage et zones chaudes ; le froid de déc.-févr. freine la croissance | 127-128 |
| **Aubergine** | ni trop lourd ni trop léger, profond, meuble, bien drainé, riche en matière organique | 5,5 à 6,8 | moins sensible | toute l'année en pépinière (30 à 50 j) | toute l'année | *à vérifier* (p. 80) | supporte la chaleur ; meilleurs résultats en saison fraîche | 79-80 |
| **Carotte** | sableux, bien ameublis, assez profonds, sans obstacle pour la racine | 5,5 à 6,8 | **très sensible** (sol et eau) | semis direct, oct.-nov. à mars-avril | (semis direct) | environ 100 à 120 j (*à vérifier*, p. 86) | saison sèche fraîche (la chaleur donne des racines courtes et fibreuses) | 85-86 |

**Pour aller du texte aux règles** (proposition à valider avec Oscar et l'agronome, pas une donnée sourcée) :

- `sol(lat, lon)` d'Oscar renverra une texture et un pH. On peut traduire les mots du guide en trois classes simples : *léger* (sableux = dior), *moyen* (sablo-limoneux = dior-deck), *lourd* (argileux). Par exemple, la carotte demande un sol léger, la pomme de terre un sol plutôt léger, le poivron et l'aubergine un sol moyen.
- Règle d'exclusion simple : si le pH est en dessous du minimum du Tableau 3, la culture est déconseillée ou conseillée avec un renvoi vers un agent (chaulage). Si la zone est signalée salée, l'oignon et la carotte sont exclus.
- Le mois courant filtre les cultures selon leur période de semis ou de plantation.
- **Attention** : SoilGrids ne mesure pas la salinité, et ses résultats ne reproduisent pas les petites variations entre dunes et cuvettes. La salinité devra être une question posée à l'agriculteur (« ton eau de puits est-elle salée ? »), pas une donnée calculée.

---

## 4. Brouillon des fiches maladies (cultures du diagnostic, liste provisoire)

Les fiches suivent les classes de **PlantVillage**, car le modèle d'Oscar ne reconnaîtra que celles-là (liste exacte à confirmer avec Oscar et le fichier `data/README.md`). Pour chacune : ce que disent les sources, ce qui manque, et des **gestes de prévention simples, sans produit**.

### 4.1 Tomate et pomme de terre

**1. Alternariose** (*Alternaria solani*), tomate et pomme de terre. Classes PlantVillage : *Tomato Early blight*, *Potato Early blight*.
- Symptômes : sur les feuilles, taches brunes arrondies avec des cercles concentriques, puis jaunissement, brunissement et dessèchement du feuillage ; sur les fruits de tomate, taches brunes qui débutent au niveau du calice [G87 p. 134 et 140]. Les taches sont souvent entourées d'un halo jaune (FAO/RADHORT, *Techniques de production de semences de tomate au Sénégal*, 2012).
- Présence au Sénégal : citée parmi les principaux problèmes de la tomate en saison fraîche (FAO/RADHORT 2012). Figure aussi dans le guide de 1987 pour la tomate et la pomme de terre.
- Prévention (sans produit) : retirer les parties brunes atteintes en portant des gants, ne pas arroser le feuillage et préférer le goutte-à-goutte (fiche KCOA, *Production biologique de la tomate au Sénégal*, 2025) ; arroser tôt le matin [G87 p. 5].

**2. Mildiou** (*Phytophthora infestans*), tomate et pomme de terre. Classes : *Tomato Late blight*, *Potato Late blight*.
- Symptômes : taches d'aspect huileux qui brunissent, parfois un duvet blanc sous la feuille ; dessèchement très rapide du feuillage (Ephytia, INRAE ; article Thiesinfo du 17 févr. 2026). L'alternariose et le mildiou se ressemblent : l'alternariose donne des taches sèches à cercles concentriques, le mildiou des taches huileuses qui s'étendent vite.
- Présence au Sénégal : **absente du guide de 1987** ; **aucune étude sénégalaise trouvée**. Signalement de presse non confirmé à Notto Gouye Diama en février 2026 ; un épisode semblable s'y serait produit « il y a plus de cinq ans » (même article).
- Prévention (sans produit) : ne pas mouiller le feuillage, arroser le matin, arracher et éloigner du champ les plants très atteints, contacter un agent agricole dès les premiers symptômes (*à faire valider par l'agronome*).

**3. Cladosporiose** (*Passalora fulva*, ancien nom *Cladosporium fulvum*), tomate. Classe : *Tomato Leaf Mold*.
- Symptômes : taches vert pâle à jaunâtres sur le dessus des feuilles, avec en dessous un duvet velouté brun verdâtre à violet [G87 p. 140].
- Prévention : aérer la culture ; pour les variétés à croissance indéterminée, le guide conseille de retirer une partie du feuillage du bas pour une meilleure aération [G87 p. 139].

**4. Septoriose** (*Septoria lycopersici*), tomate. Classe : *Tomato Septoria leaf spot*.
- Le guide la montre en photo [G87 p. 138, fig. 311] mais nous n'avons pas pu lire sa description dans le scan. **Symptômes à sourcer.**

**5. Galle bactérienne / tache bactérienne** (*Xanthomonas* spp.), tomate et poivron. Classes : *Tomato Bacterial spot*, *Pepper bell Bacterial spot*.
- Symptômes : surtout en hivernage ; petites taches d'aspect mouillé qui noircissent sur les feuilles, puis jaunissement et dessèchement rapide du feuillage ; taches sur les fruits [G87 p. 140 ; p. 130 pour le poivron].
- Prévention : *à sourcer* (le guide ne donne qu'un traitement chimique).

**6. Acariens.** Classe : *Tomato Spider mites Two-spotted spider mite* (*Tetranychus urticae*).
- Le guide décrit surtout l'**acariose bronzée** de la tomate : feuilles qui jaunissent puis brunissent, tiges qui brunissent, causée par de petites araignées invisibles à l'œil nu [G87 p. 140]. Sur pomme de terre : face inférieure des feuilles bronzée, folioles qui se recroquevillent [G87 p. 134]. FAO/RADHORT 2012 cite l'acariose bronzée parmi les grands problèmes de saison fraîche.
- **Attention** : l'acarien de l'acariose bronzée n'est pas le tétranyque de PlantVillage. À clarifier avec Oscar et l'agronome avant d'écrire la fiche.

**7. Virus des feuilles jaunes en cuillère de la tomate** (TYLCV). Classe : *Tomato Yellow Leaf Curl Virus*.
- Transmis par l'aleurode (*Bemisia tabaci*). Le guide décrit les viroses en général : déformation et décoloration des feuilles ; lutter contre les insectes vecteurs dès la pépinière, éviter la taille [G87 p. 140]. Pour les virus du poivron et du piment, le guide conseille de brûler les plants atteints [G87 p. 130].
- Présence : enquête sur 98 champs de tomate des Niayes (oct. 2012 à mai 2014) qui signale l'aleurode et le TYLCV (*Arthropod pest complex and associated damage in field-grown tomato in Senegal* ; chiffres exacts à relire dans l'article). Le TYLCV est aussi cité par FAO/RADHORT 2012.
- Prévention : protéger la pépinière (abri, moustiquaire, d'après la fiche KCOA 2025), choisir des variétés tolérantes (*à sourcer : lesquelles au Sénégal ?*).

**8. Virus de la mosaïque de la tomate** (ToMV). Classe : *Tomato mosaic virus*. Seulement couvert par la mention générale « viroses » du guide. **Présence au Sénégal non vérifiée.**

**9. Tache cible** (*Corynespora cassiicola*). Classe : *Tomato Target Spot*. **Non trouvée dans nos sources sénégalaises.** Si aucune source n'est trouvée, mieux vaut que le produit réponde « incertain » pour cette classe.

### 4.2 Maïs (si la culture est retenue le 4 nov)

Classes PlantVillage : *rouille commune* (*Puccinia sorghi*), *helminthosporiose du nord* (*Exserohilum turcicum*), *cercosporiose / tache grise* (*Cercospora zeae-maydis*). **Aucune source sénégalaise trouvée** sur ces trois maladies. Le grand problème documenté du maïs au Sénégal est la **chenille légionnaire d'automne** (*Spodoptera frugiperda*), un insecte détecté en 2017 et étudié par l'ISRA/CDH (projet KAFACI, 2020-2024) ; PlantVillage ne la couvre pas.

### 4.3 Ravageurs importants que PlantVillage ne couvre pas

Le modèle ne les reconnaîtra pas, mais les agriculteurs en parleront. Le produit doit donc répondre « non pris en charge » et renvoyer vers un agent :

- **Mineuse de la tomate** (*Tuta absoluta*) : signalée pour la première fois au Sénégal en 2012 (Pfeiffer et al., *Florida Entomologist*, 2013). Dans les Niayes, elle peut toucher en moyenne 60 % des cultures de tomate, avec des pics en fin de saison sèche (février à mai) ; sans lutte, les pertes peuvent atteindre 80 à 100 % (thèse de S. Sylla, UCAD/CIRAD).
- **Noctuelle de la tomate / ver du fruit** (*Helicoverpa armigera*) [G87 p. 138 et 140].
- **Nématodes à galles** (*Meloidogyne* spp.) : nodosités sur les racines ; choisir des variétés résistantes, faire une rotation [G87 p. 140-141].
- **Thrips de l'oignon** : taches argentées, bout des feuilles qui sèche ; variété tolérante citée : « Yaakaar » [G87 p. 120].

---

## 5. Pour le module Prévention : ce que nous savons du risque de mildiou

À lire avec Oscar.

- **Règle de référence trouvée : les critères Hutton** (AHDB, Royaume-Uni, depuis 2017). Le risque est élevé après **deux jours consécutifs** où la température minimale est d'au moins 10 °C et où l'humidité relative atteint au moins 90 % pendant au moins 6 heures. Ils remplacent l'ancienne « période de Smith » (11 heures au lieu de 6). Les critères Hutton ont été validés sur plus de 2 000 foyers historiques **en Grande-Bretagne**.
- **Limite importante** : ces seuils n'ont jamais été validés au Sénégal. Dans les Niayes, la température minimale dépasse presque toujours 10 °C : seule l'humidité ferait la différence.
- **Données** : NASA POWER fournit l'humidité relative (`RH2M`) et la température (`T2M`) **heure par heure** (point d'accès `hourly`, communauté `AG`). C'est nécessaire pour compter les « heures à 90 % ».
- **Question pour l'équipe** : faut-il garder le mildiou comme seule maladie du module Prévention, alors que l'alternariose est mieux documentée au Sénégal ? Au minimum, présenter le risque comme « conditions favorables », jamais comme un diagnostic, et le tester sur l'épisode de février 2026 à Notto Gouye Diama.

---

## 6. Questions à poser à l'agronome

1. Ces 8 cultures sont-elles les bonnes pour la zone pilote ? Lesquelles retirer ou ajouter (jaxatu, gombo, laitue…) ?
2. Les périodes de semis du guide de 1987 sont-elles encore valables avec les variétés et le climat actuels ?
3. Le mildiou est-il un vrai problème dans les Niayes, et à quelle saison ? Avez-vous vu l'épisode de Notto Gouye Diama (février 2026) ?
4. Comment l'alternariose et le mildiou se distinguent-ils sur le terrain, en mots simples ?
5. Quels gestes de prévention, sans produit chimique, conseillez-vous pour chaque maladie ?
6. Quelles variétés tolérantes au TYLCV et aux nématodes sont disponibles aujourd'hui sur le marché sénégalais ?
7. Pouvez-vous nous donner les fiches ISRA réactualisées en 2022 ?
8. Quels mots wolof les maraîchers utilisent-ils pour ces maladies (pour le dictionnaire) ?

---

## 7. Sources

Liste complète avec dates d'accès, statut et méthode : [docs/sources/journal-recherche-agronomique.md](../docs/sources/journal-recherche-agronomique.md).

- Beniest J. et al., *Guide pratique du maraîchage au Sénégal*, ISRA / FAO, CDH Cambérène, 1987. <https://open-library.cirad.fr/files/4/751__Guide_pratique_du_maraichage_au_Senegal.pdf>
- ISRA, « L'ISRA et l'USAID s'engagent pour la réactualisation des fiches techniques… », 20 mars 2022. <https://isra.sn/2022/03/20/lisra-et-lusaid-sengagent-pour-la-reactualisation-des-fiches-techniques-des-principales-cultures-maraicheres-au-senegal/>
- KCOA-Africa, *Fiche technique : production biologique de la tomate au Sénégal*, 2025. <https://kcoa-africa.org/wp-content/uploads/2025/10/Fiche-technique_production-biologique-Tomate-2.pdf>
- FAO / RADHORT / ISRA-CDH, *Techniques de production de semences de tomate au Sénégal*, 2012. <https://openknowledge.fao.org/server/api/core/bitstreams/f65c83bb-f7f5-42cb-b3ae-e14b49e7abfb/content>
- De Bon H. et al., « Rendements et pratiques des cultures maraîchères en agriculture biologique au Sénégal », *Cahiers Agricultures*, 2019. <https://www.cahiersagricultures.fr/articles/cagri/full_html/2019/01/cagri180073/cagri180073.html>
- Ministère de l'Agriculture du Sénégal, document sur la typologie des sols dior / dior-deck. <https://edepot.wur.nl/487348>
- ANSD, RGPH-5, chapitre 10 Agriculture, rapport provisoire, juillet 2024. <https://www.ansd.sn/sites/default/files/recensements/rapport/Chapitre%2010%20-%20AGRICULTURE-Rapport-Provisoire-RGPH5_juillet2024.pdf>
- Thiesinfo, « Zone des Niayes : des maraîchers alertent sur une maladie qui menace leurs récoltes », 17 févr. 2026. <https://www.thiesinfo.com/Zone-des-Niayes-des-maraichers-alertent-sur-une-maladie-qui-menace-leurs-recoltes_a13075.html>
- Ephytia (INRAE), Tomate, mildiou. <https://ephytia.inrae.fr/fr/C/5086/Tomate-Mildiou-Phytophthora-infestans>
- Pfeiffer D. G. et al., « First Record of *Tuta absoluta* in Senegal », *Florida Entomologist*, 2013. <https://bioone.org/journals/florida-entomologist/volume-96/issue-2/024.096.0241/First-Record-of-Tuta-absoluta-Lepidoptera-Gelechiidae-in-Senegal/10.1653/024.096.0241.full>
- Sylla S., thèse, UCAD / CIRAD (mineuse de la tomate). <https://agritrop.cirad.fr/590299/1/Th%C3%A8se_Serigne_VF.pdf>
- *Arthropod pest complex and associated damage in field-grown tomato in Senegal*. <https://www.researchgate.net/publication/326608949_Arthropod_pest_complex_and_associated_damage_in_field-grown_tomato_in_Senegal>
- ISRA, projet KAFACI-FAW (chenille légionnaire d'automne), 18 sept. 2024. <https://isra.sn/2024/09/18/lutte-contre-la-chenille-legionnaire-dautomne-cla-le-projet-kafaci-faw-pour-une-gestion-integree-de-la-riposte/>
- AHDB, critères Hutton. <https://potatoes.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria>
- NASA POWER, API horaire. <https://power.larc.nasa.gov/docs/services/api/temporal/hourly/>
