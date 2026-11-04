# Catalogue des sources de données

État au 4 novembre 2026. Ce catalogue recense toutes les sources de données repérées pour TerraMind, qu'elles soient déjà téléchargées, demandées ou à obtenir. Le registre de provenance officiel reste [README.md](README.md) : une donnée n'est utilisée qu'une fois inscrite là-bas.

- Téléchargement reproductible : `python3 scripts/donnees/telecharger_sources.py [source …]`.
- Empreintes SHA-256, URL exactes et dates : [raw/MANIFESTE.csv](raw/MANIFESTE.csv).
- Les licences marquées « à vérifier » n'ont pas été lues sur la page officielle : ne pas publier de résultat qui en dépend avant vérification.

Points pilotes météo et sols : centroïdes des départements de Rufisque, Thiès, Tivaouane et Kébémer, calculés à partir des limites geoBoundaries. Ce ne sont pas des parcelles réelles.

| Département | Latitude | Longitude |
|---|---|---|
| Rufisque | 14,7593 | -17,2054 |
| Thiès | 14,7459 | -16,8698 |
| Tivaouane | 15,0884 | -16,6518 |
| Kébémer | 15,3042 | -16,2611 |

---

## 1. Téléchargé (dans `data/raw/`)

| Source | Fichiers | Contenu | Licence | Module | Limites |
|---|---|---|---|---|---|
| DAPSA, Enquête agricole annuelle, diffusé par l'ANSD (Senegal Data Portal) | `dapsa_superficie_rendement_production_2010-2024_odp_2026-10-30.csv` | Superficie, production, rendement de 8 cultures pluviales, national, région, département (2010-2024, sans 2023) | Licence de données ouvertes de l'ANSD | Choix des cultures, contexte | Aucune culture maraîchère ; anomalies listées dans le registre |
| FAOSTAT, production végétale et animale (QCL) | `faostat/faostat_qcl_senegal_extrait.csv` | 117 produits pour le Sénégal, 1961-2024, avec indicateurs de qualité : tomate, pomme de terre, oignon, chou, carotte, aubergine, gombo, pastèque, maïs… | CC BY 4.0 | Choix des cultures (niveau national) | National uniquement ; pas de poivron frais (seulement piment sec) ; vérifier les indicateurs (estimations FAO ou chiffres officiels) |
| NASA POWER (MERRA-2) | `nasa_power/<département>/journalier_1991-2025.csv` et `horaire_2020.csv` à `horaire_2025.csv` | Journalier : température moyenne, max, min, humidité relative, pluie. Horaire (UTC) : température, humidité relative, pluie, vent à 2 m | Données publiques de la NASA, citation demandée | Prévention (alertes météo), calendrier cultural | Maille d'environ 50 km, pas une station au sol ; aucune valeur manquante (-999) relevée dans les fichiers horaires contrôlés |
| PAM (WFP) via HDX, prix alimentaires du Sénégal | `wfp_prix/wfp_food_prices_sen.csv`, `wfp_prix/wfp_markets_sen.csv` | 54 038 prix, 2000-2026, toutes régions. Céréales et niébé sur la durée ; tomate, pomme de terre, oignon, chou, carotte sur 48 marchés mais seulement de mai à août 2026 | CC BY-IGO | Choix des cultures (demande, valeur), pitch | Série légumes très courte ; source primaire : ANSD et SIM via FAO GIEWS |
| geoBoundaries, limites administratives du Sénégal | `geoboundaries/geoBoundaries-SEN-ADM1_simplified.geojson`, `…-ADM2_simplified.geojson`, métadonnées | 14 régions, 45 départements (découpage 2019, source Gouvernement du Sénégal et OCHA) | CC BY 3.0 IGO | Cartes, tableau de bord, points pilotes | Ne contient pas le département de Keur Massar (créé en 2021) ; géométries simplifiées |
| CHIRPS v3.0 (Climate Hazards Center) | `chirps/chirps_v3_pentades_1991-2025_points_pilotes.csv` | Pluie totale par pentade (5 jours), 1991-2025, 4 points pilotes, résolution 0,05° | Domaine public (CC0) | Prévention, calendrier cultural | Valeur d'un seul pixel par point ; pas de journalier (déconseillé par le producteur) |
| iSDAsoil (iSDA) | `isdasoil/isdasoil_points_pilotes.csv`, `isdasoil/metadonnees/` | 20 propriétés des sols (pH, sable, limon, argile, classe de texture, carbone, azote, P, K, Ca, Mg, S, Zn, Fe, Al, CEC, densité apparente, cailloux, profondeur de la roche), 0-20 et 20-50 cm, 30 m, aux 4 points pilotes | CC BY 4.0 | Planification (sol → cultures) | Lu sans compte dans les COG publics d'AWS ; azote corrigé (règle exp(x/100)-1 du catalogue Earth Engine, les métadonnées d'AWS se trompent) ; texture en classes USDA (Rufisque : limon argilo-sableux ; Thiès, Tivaouane, Kébémer : limon sableux) ; pas de salinité |
| PlantVillage (Mohanty et al. 2016, Hugging Face `mohanty/PlantVillage`) | `images/plantvillage/` (exclu de Git), inventaire `extraits/images_diagnostic_inventaire.csv` | 22 787 photos couleur prises en laboratoire : 10 classes tomate, 3 pomme de terre, 2 poivron. Seules ces classes ont été extraites de l'archive de 2,2 Go (script `telecharger_images.py`) | CC BY-SA 3.0 (fiche Hugging Face) | Diagnostic photo (entraînement) | Fond uni de laboratoire : le modèle se trompe sur des photos de champ ; **pas d'oignon ni de chou** |
| PlantDoc (Singh et al. 2020) | `images/plantdoc/` (exclu de Git) | 1 100 photos prises au champ, mêmes cultures (12 classes en test, 13 en entraînement) | CC BY 4.0 (citer DOI 10.1145/3371158.3371196) | Diagnostic photo (test en conditions réelles) | Peu d'images par classe (6 à 11 en test) ; pas d'oignon ni de chou |

## 1 bis. Tableaux extraits de rapports publics (dans `data/extraits/`)

Documents sources téléchargés dans `raw/documents/` (source `documents` du script), tableaux extraits par `python3 scripts/donnees/extraire_rapports.py`. Chaque extraction comporte des contrôles (chiffres cités dans le texte du rapport) et échoue si l'ordre des colonnes ne correspond pas. Détail des sources : [extraits/SOURCES.csv](extraits/SOURCES.csv).

| Fichier | Source | Contenu | Usage |
|---|---|---|---|
| `rgph5_2023_part_menages_maraichers_par_culture.csv` | ANSD, RGPH-5 (2023), chapitre 10, tableaux X21 à X24, p. 38-41 | Part des ménages maraîchers qui cultivent chaque produit (25 produits), par région et milieu, en contre-saison froide et chaude | **Choix des cultures (besoin)** : c'est la meilleure mesure par région que nous ayons |
| `dhort_production_horticole_nationale_2015-2022.csv` | ANSD, bulletin d'octobre 2023, tableau I.4-3 (source : Direction de l'Horticulture) | Production nationale (t) de 16 produits horticoles, campagnes 2015/2016 à 2021/2022 (dernière provisoire) | Choix des cultures, pitch |
| `eaa_2020-2021_part_menages_maraichage_par_region.csv` | DAPSA, EAA 2020-2021, tableaux annexes 4.2.1 | Part des ménages agricoles qui font du maraîchage, par région | Contexte |
| `eaa_2020-2021_production_moyenne_menage_maraichage.csv` | DAPSA, EAA 2020-2021, tableaux annexes 4.2.3 | Production moyenne par ménage producteur, par région et culture (10 cultures) | Ordre de grandeur seulement (petits échantillons) |
| `eaa_2020-2021_production_moyenne_menage_national.csv` | DAPSA, EAA 2020-2021, tableaux annexes 4.2.2 | Moyenne nationale par culture et taille de l'échantillon (N) | Contexte |
| `eaa_2020-2021_utilisation_productions_maraicheres.csv` | DAPSA, EAA 2020-2021, tableaux annexes 4.2.4 | Part vendue, consommée, gardée en semence, donnée | Pitch (le maraîchage est une activité marchande : 74 % vendu) |
| `eaa_2022-2023_chocs_production_par_region.csv` | DAPSA, EAA 2022-2023, graphique 8.1.2 | % des ménages agricoles touchés par chaque choc de production (sécheresse, inondation, ravageurs, prix bas…), par région | **Besoin** : ravageurs inhabituels 43,9 % à Louga, 20,6 % à Thiès (15,3 % au national) |
| `eaa_2022-2023_produits_phytosanitaires_par_culture.csv` | DAPSA, EAA 2022-2023, graphique 3.4.3 | % des parcelles traitées par type de produit selon la culture | **Besoin** : insecticides sur 99 % des parcelles de chou, 97 % de tomate cerise, 78 % d'oignon |
| `eaa_2022-2023_utilisation_productions_maraicheres.csv` | DAPSA, EAA 2022-2023, graphique 4.2.3 (bloc de gauche) | Part vendue, gardée en semence, donnée, consommée | Pitch |

Ce que disent déjà ces tableaux pour la zone pilote (contre-saison froide, % des ménages maraîchers) : oignon 55,6 % à Thiès et 58,6 % à Louga, tomate 52,7 % et 55,6 %, chou 47,2 % et 45,7 %, pomme de terre 34,4 % et 36,7 %, poivron 31,3 % et 27,0 %, maïs 8,1 % et 6,1 %.

Classeur `dapsa_eaa_2022-2023_tableaux.xlsx` : ce sont les données des graphiques du rapport. Trois tableaux en sont extraits (ci-dessus) ; les blocs de droite sans titre (production moyenne, usages) ne sont pas repris faute de savoir ce qu'ils mesurent. Le classeur `dapsa_eaa_2017-2022_superficie_rendement_production.xlsx` ne contient que les 8 cultures pluviales (déjà couvertes par le fichier du Senegal Data Portal).

## 2. Demandé, en attente

| Source | Demande | Contenu attendu | Module | Suivi |
|---|---|---|---|---|
| DAPSA, Enquête agricole annuelle 2024-2025 (microdonnées, via ANADS) | Formulaire ANADS envoyé le 30/10/2026 | Cultures pratiquées, superficies, rendements et intrants dans les régions de Dakar et de Thiès, y compris le maraîchage | Choix des cultures, planification | Relance vers le 6/11/2026 |

## 3. À obtenir

| Source | Comment | Contenu | Licence | Module | Priorité |
|---|---|---|---|---|---|
| SoilGrids 2.0 (ISRIC) | Script, source `soilgrids` (API souvent indisponible) | pH, argile, sable, limon, carbone organique, CEC, azote, résolution 250 m | CC BY 4.0 | Planification (vérification croisée d'iSDAsoil) | Basse (iSDAsoil couvre le besoin) |
| Photos de ravageurs du chou (teigne) et compléments chou | Oignon : couvert par TOM2024 (branche d'Oscar). Chou : 203 images d'origine téléchargées le 4 nov (Mendeley, CC BY 4.0), mais aucune image de teigne et peu de mildiou (28) ou de pourriture noire (37). À compléter par des photos de terrain avec consentement | Teigne, borer, mildiou du chou | — | Diagnostic photo | Moyenne |
| Fiches techniques maraîchères ISRA-CDH (publiées en déc. 2022 sur marcheagricole.sn : tomate, pomme de terre, oignon, carotte, poivron…) | Le site marcheagricole.sn ne répond plus (nom de domaine introuvable) ; les pages de téléchargement (`/wpfd_file/fiche-technique-…-isra-cdh/`) n'ont **jamais été archivées** par la Wayback Machine (vérifié le 2 nov. 2026). Seule voie : **demander au CDH de Cambérène** (ISRA) | Itinéraires techniques réactualisés de 20 cultures | À demander | Planification, contenu | Haute |
| DPV, Enquête de surveillance phytosanitaire 2018 | ANADS, catalogue 200, demande écrite au Directeur de la DPV | Ravageurs et maladies suivis | Autorisation de la DPV | Prévention, choix des cultures | Moyenne |
| ANACIM (stations, séries ENACTS) | Courrier à la Direction de l'Exploitation de la Météorologie | Pluie, température, humidité au sol | Inconnue, tarif possible | Vérification de NASA POWER | Basse |
| ESA WorldCover / Digital Earth Africa (cultures) | Rasters | Occupation du sol, masques de cultures | CC BY 4.0 (à vérifier) | Cartes de la zone pilote | Basse |
| Géo Sénégal (BaseGéo, pôle AGRO) | Téléchargement libre | Données agricoles et sols nationales | Licence BaseGéo (usage commercial soumis à accord) | Planification, cartes | Moyenne, à explorer |
| ANSD, RGPH-5 (2023), module agriculture | Rapport PDF et microdonnées ANADS | Ménages agricoles, cultures par zone | Licence ANSD | Contexte, marché (pitch) | Basse |

## 4. Sources documentaires (pas des jeux de données)

Les documents utilisés pour le contenu agronomique (guide ISRA 1987, fiche KCOA 2025, articles sur le mildiou, la mineuse de la tomate et la chenille légionnaire…) sont recensés dans le [journal de recherche](../docs/sources/journal-recherche-agronomique.md).
