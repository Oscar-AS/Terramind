# Seuils et paramètres : d'où vient chaque valeur

Chaque nombre utilisé par TerraMind pour décider est listé ici, avec sa justification. Il y a trois sortes de justification :
- **[Source]** : valeur publiée, avec sa référence ;
- **[Mesure]** : valeur choisie à partir d'une mesure faite par l'équipe, décrite ici ;
- **[Raisonnement]** : choix de conception expliqué, sans prétention scientifique.

Mise à jour : 13 nov 2026. Fichier de code entre parenthèses.

## 1. Alertes météo (`engine/app/modules/prevention/`)

| Paramètre | Valeur | Justification |
|---|---|---|
| Mildiou : Tmin, humidité, durée | Tmin ≥ 10 °C, humidité ≥ 90 % pendant ≥ 6 h, **2 jours de suite** | **[Source]** Critères Hutton (AHDB, Royaume-Uni, 2017), validés sur plus de 2 000 foyers en Grande-Bretagne. Non validés au Sénégal : d'où la formule « conditions favorables ». |
| Mildiou : plafond de température | 26,6 °C | **[Source]** Borne haute du modèle de Wallin (Blitecast) ; sporulation quasi nulle à 28 °C (*Plant Disease* 2005) ; aucune germination à 27 °C (*Plant Disease* 2009). Sans ce plafond, les heures chaudes et humides de l'hivernage déclencheraient des alertes presque tous les jours. |
| Alternariose : notes TOMCAST | tableau 0 à 4 | **[Source]** Madden, Pennypacker et MacNab 1978 ; tableau UC IPM. |
| Alternariose : seuil d'alerte | 15 points cumulés | **[Source]** La littérature TOMCAST donne 15 à 20 points. **[Raisonnement]** On prend le bas de la fourchette : pour une alerte de prévention, mieux vaut prévenir trop tôt que trop tard (le conseil est seulement de surveiller). |
| Fenêtre d'analyse | 7 jours | **[Raisonnement]** C'est la « semaine » de l'écran Alertes ; elle couvre au moins deux paires de jours pour le critère Hutton. |
| Délai NASA POWER | 3 jours | **[Mesure]** Le 13 nov 2026, la dernière journée horaire complète disponible était le 11 nov (délai de 2 jours). On garde un jour de marge pour ne jamais analyser une journée incomplète. |
| Journée complète | au moins 20 heures sur 24 | **[Raisonnement]** Il faut presque toute la journée pour compter des heures d'humidité. Une ou deux heures manquantes ne changent pas le résultat ; davantage pourraient le fausser. |
| Mineuse de la tomate | seuil 8 °C, 440 degrés-jours par génération | **[Source]** Barrientos et al. 1998 ; Krechemer et Foerster 2015 (417 à 454). |
| Teigne du chou | seuil 7,3 °C, 290 degrés-jours par génération | **[Source]** Dans les fourchettes publiées : seuil 6,3 à 7,8 °C, 260 à 353 degrés-jours (Golizadeh et al. 2007 ; Marchioro et Foerster 2011 ; UC IPM). |
| Ravageurs : quand alerter | à partir de la **3e génération** depuis le repiquage | **[Raisonnement]** Les populations s'accumulent pendant la culture. Notre test 2020-2025 montre qu'une tomate repiquée début décembre en est à 2 à 6 générations entre février et mai, la période des pics rapportés dans les Niayes (thèse de Sylla). La 3e génération tombe environ 2 mois après le repiquage. C'est une règle TerraMind, pas un résultat publié. |

Sources détaillées : [sources/seuils-meteo-maladies-ravageurs.md](sources/seuils-meteo-maladies-ravageurs.md).

## 2. Que planter (`engine/app/modules/planification/`)

| Paramètre | Valeur | Justification |
|---|---|---|
| Périodes de semis, pH minimal, sensibilité au sel, durée au champ | par culture | **[Source]** Guide ISRA/CDH 1987 (tableaux 1 et 3, fiches par culture) et livret PIESAN 2022 pour l'oignon. Détail dans `cultures.py`. |
| Sol lourd | argile ≥ 35 % | **[Raisonnement + Source]** Le guide dit « pas trop lourd » sans chiffre. Dans le triangle des textures USDA (celui d'iSDAsoil), 35 % d'argile est le seuil à partir duquel un sol sableux devient « argilo-sableux » (sandy clay). Les Niayes sont sableuses (59 à 83 % de sable mesurés) : ce seuil ne déclenche que pour les vrais sols argileux. |
| Point de sol | moyenne de 5 × 5 pixels, environ 150 m | **[Raisonnement]** iSDAsoil a des pixels de 30 m : un pixel isolé peut tomber sur une piste ou une mare. La moyenne sur environ 150 m reste à l'échelle d'un champ. |
| Arrondi de la position | 0,01°, environ 1 km | **[Raisonnement]** C'est un compromis entre vie privée et précision : on ne localise pas la parcelle. La météo NASA POWER (mailles de 0,5°) n'en est pas affectée. Pour le sol, c'est une limite assumée : c'est le sol moyen du voisinage, et on demande en plus si le champ est en bas-fond. |
| Sel | question à l'agriculteur, pas de calcul | **[Source]** Aucune carte ouverte ne donne la salinité (études Diallo et al. 2015 ; *European Scientific Journal* 2022). |

## 3. Diagnostic photo (`engine/app/modules/diagnostic/`, `ml/training/`)

| Paramètre | Valeur | Justification |
|---|---|---|
| Seuil d'incertitude | 0,6 | **[Mesure]** Sur la validation de terrain, 90 % des photos dépassent 0,6, et 90 % d'entre elles sont justes. On a écarté 0,4 (proposé par la règle automatique), qui ne donnait que 62 % de réponses justes sur les photos de type PlantDoc. Limite : choix fait après avoir vu les tests. Détails : [ml/eval/diagnostic_v1.md](../ml/eval/diagnostic_v1.md). |
| Calibration | température 0,81 | **[Source + Mesure]** Méthode de Guo et al. 2017 (« On Calibration of Modern Neural Networks ») ; valeur apprise sur la validation de terrain uniquement. |
| Classes retenues | au moins 50 images | **[Source]** Décision D8 d'Oscar (base terramind_v1). |
| Plafond PlantVillage | 600 images par classe | **[Raisonnement]** PlantVillage est photographié en laboratoire, sur fond uni. Le plafonner évite que le modèle apprenne surtout des photos de laboratoire. 600 images restent proches de l'effectif des classes de terrain. |
| Découpage | validation 15 % de TOM2024 et 20 % de PlantDoc entraînement ; test 15 % de TOM2024 et PlantDoc test | **[Raisonnement]** Il faut des photos de terrain pour choisir le modèle et le seuil, et d'autres, jamais vues, pour l'évaluer. Le découpage dépend de l'empreinte de chaque image : il est reproductible et sans fuite entre doublons. |
| Taille d'image | 224 × 224 px | **[Source]** Taille d'entraînement des réseaux pré-entraînés sur ImageNet (MobileNetV3, Howard et al. 2019). |
| Photo maximale | 8 Mo | **[Raisonnement]** Une photo de téléphone fait 2 à 5 Mo. Au-delà, c'est probablement une erreur, et l'envoi serait trop long sur un réseau mobile. |

## 4. Questions libres (RAG, `engine/app/modules/rag/`)

| Paramètre | Valeur | Justification |
|---|---|---|
| Score minimal de pertinence | 3,5 | **[Mesure]** Le 13 nov 2026, sur 20 questions : 10 questions agricoles couvertes par les fiches (score de 4,0 à 11,6) et 10 questions hors sujet (prix du riz, football, Wave, météo de Dakar… : score de 0 à 3,3). 3,5 sépare les deux groupes. Deuxième barrière : Gemini doit répondre « je ne sais pas » si les extraits ne répondent pas. Échantillon petit, à refaire avec de vraies questions d'agriculteurs. Contrôle du 13 nov (soir), après le passage des fiches en 4 sections : « quel temps fait-il à Dakar » obtient 3,95 (3,81 avant ce changement) et passe donc la première barrière ; seule la consigne donnée à Gemini l'arrête. Limite connue, à corriger avec de vraies questions. Contrôle du 14 nov (nuit), après le bonus au titre de fiche, les familles « flétrir »/« fane », « cultiver » = « planter » et les fiches mineuse et teigne en 4 temps : « quel temps fait-il à Dakar » = 3,51 (passe de justesse) ; prix du riz, football, Wave, salutations, blague = 0. |
| Paramètres BM25 | k1 = 1,4 ; b = 0,75 | **[Source]** Valeurs standard de BM25 (Robertson et Zaragoza 2009 : k1 entre 1,2 et 2,0, b = 0,75). |
| Passages envoyés | 3 au plus, plus la section « Prévention » de la fiche principale | **[Raisonnement]** Des réponses courtes pour des utilisateurs peu lettrés ; une question sur un symptôme appelle presque toujours « que faire ? ». |
| Modèle de langage | `gemini-3.5-flash-lite` | **[Raisonnement]** Le plus rapide et le moins cher de la gamme Gemini actuelle. Son rôle se limite à reformuler les extraits de fiche. Le choix final se fera par le test D9, avec des locuteurs du wolof. |
