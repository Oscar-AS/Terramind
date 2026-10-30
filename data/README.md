# Données : registre de provenance

Toute donnée utilisée par le projet (entraînement, évaluation, cartes, météo, échantillons) est inscrite ici **avant** d'être utilisée.

Règles :
- Aucune donnée inventée.
- Les photos et positions GPS de vrais agriculteurs ne sont jamais commitées.
- Les gros fichiers (images, rasters, archives, modèles) restent hors Git ; seul `data/sample/` contient de petits échantillons publics.

Comment les sources ont été trouvées et vérifiées : [docs/sources/journal-recherche-agronomique.md](../docs/sources/journal-recherche-agronomique.md).

| Nom | Source | URL | Licence | Date de téléchargement | Usage | Responsable |
|---|---|---|---|---|---|---|
| Guide pratique du maraîchage au Sénégal (Tableaux 1 et 3, fiches cultures) | J. Beniest et al., ISRA / FAO, CDH Cambérène, 1987 | https://open-library.cirad.fr/files/4/751__Guide_pratique_du_maraichage_au_Senegal.pdf | © ISRA-FAO 1987, diffusé en libre accès par la bibliothèque ouverte du CIRAD ; conditions de réutilisation à vérifier | 2026-10-30 | Brouillon de table sol → culture et fiches maladies (`research/`), non validé | Salam (collecte), Rama (contenu) |
| Superficie, rendement et production agricoles, 2010-2024 (`raw/dapsa_superficie_rendement_production_2010-2024_odp_2026-10-30.csv`) | Producteur : DAPSA (Enquête agricole annuelle) ; diffusé par l'ANSD sur le Senegal Data Portal | https://senegal.opendataforafrica.org/ekihmme/superficie-rendement-et-production-agricoles | Accord de licence de données ouvertes de l'ANSD (gratuite, non exclusive, usage commercial autorisé, attribution obligatoire, voir ci-dessous) | 2026-10-30 | Contexte statistique pour le choix des cultures et de la zone pilote (maïs surtout) ; aucune culture maraîchère dans ce fichier | Salam |

## Notes par jeu de données

### Superficie, rendement et production agricoles (DAPSA / ANSD)

- Fichier brut conservé tel quel, sans modification. SHA-256 : `12b3cea1358bdcd0c6aff1db5be1fc21230804ab55de9ea36bab11d9c6081645` (9 955 lignes).
- Contenu : 8 cultures pluviales (arachide, fonio, maïs, manioc, mil, niébé, riz, sorgho) ; superficie (ha), production (t), rendement (kg/ha) ; national et régional de 2010 à 2022, départemental de 2017 à 2022, puis 2024 (pas de 2023).
- Mention de source obligatoire (licence ANSD) : « Source : Agence Nationale de la Statistique et de la Démographie. Contient des informations sous licence conformément à l'Accord de licence de données ouvertes de l'ANSD. » Pour un produit dérivé (graphique, table, slide) : « Ce produit a été adapté à partir des informations de l'Agence Nationale de la Statistique et de la Démographie, qui sont sous licence conformément à l'Accord de licence de données ouvertes de l'ANSD. »
- Point à vérifier : la licence ANSD exclut les données de tiers. Le producteur étant la DAPSA, citer aussi « Enquête agricole annuelle, DAPSA, www.dapsa.gouv.sn » et confirmer auprès de l'ANSD ou de la DAPSA que cette licence couvre bien ce jeu.
- La licence interdit de suggérer une approbation officielle : ne pas présenter TerraMind comme validé par l'ANSD ou la DAPSA.
- Anomalies à exclure de toute analyse : rendement arachide Région de Dakar 2013-2016 égal à l'année (erreur de saisie) ; Bignona 2010-2015, série identique copiée sur toutes les cultures ; Birkilane 2010-2012 et maïs Région de Kolda 2010-2012, valeurs recopiées d'autres lignes ; plusieurs lignes 2024 à zéro ou sans unité (zéro possiblement = non enquêté) ; Région de Dakar = Rufisque à partir de 2017 (ne pas additionner).
