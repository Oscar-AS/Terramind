# Vérification des règles sol-culture proposées par Oscar (14 nov 2026)

Proposition vérifiée : `content/regles_sol_culture.csv` de la branche `ml/dataset-merge` (b28a1e1).
Méthode : relecture du Guide pratique du maraîchage au Sénégal (ISRA/CDH 1987, cité G87 ; les pages
citées sont les pages imprimées) et recherche d'autres sources par un agent de recherche, puis contrôle.
Règles en ligne : `engine/app/modules/planification/cultures.py` et `plan.py`.

## Ce qui a été appliqué

| Point | Décision | Source | Confiance |
|---|---|---|---|
| Piment, meilleure saison | Hivernage et chaleur ; le froid de décembre-février le freine | G87 p. 127 et p. 13 ; PROTA *Capsicum annuum* (Grubben et El Tahir, 2004) | probable |
| Piment, pH minimal | 5,5 | PROTA *Capsicum annuum* (pH 5,5-6,8) ; absent du G87 | probable |
| Piment, cycle | 180 à 240 jours (« 6 à 8 mois dont 3 à 4 de récolte ») | G87 p. 128 | sûr |
| Jaxatu, cycle | 130 à 200 jours | G87 p. 108 (fiche jaxatu p. 107-108 ; la page 79-80 citée par Oscar est l'aubergine) | sûr |
| Oignon et pomme de terre en bas-fond | « possible » avec un avertissement (sols trop humides) | G87 p. 11 | sûr |
| Oignon, cycle 70-150 jours | inchangé ; source PIESAN ajoutée (70 à 120 jours selon les variétés) | G87 p. 120 ; livret PIESAN 2022 p. 25 | sûr |

## Ce qui n'a pas été repris, et pourquoi

- **pH maximal 6,8 par culture** : le tableau 3 du G87 (p. 11) donne des préférences (« pH 6-6,8 », « 5,5-6,8 »…), pas des limites ; le G87 situe le pH idéal « autour de 6-7 ». La carte iSDAsoil a une erreur moyenne de 0,46 unité de pH (Hengl et al. 2021) : Kébémer (6,9) et 6,8 ne se distinguent pas. Pas de plafond.
- **Mois de semis, cycles de la tomate (105-150), de la carotte (90-120), du piment (120-210), du jaxatu (90-140)** : les valeurs actuelles suivent le G87 (p. 85, 89, 108, 128, 133, 139, 141) ; celles d'Oscar s'en écartent.
- **Sel du poivron « modéré »** : absent du tableau 1 du G87 (p. 5). Valeur gardée vide en attendant un agronome (FAO Irrigation et drainage 29, tableau 4 : 1,5 dS/m, entre l'oignon et la tomate).
- **Besoin en eau « moyen »** : aucune source ; seul le chou est dit « exigeant en eau » (G87 p. 89).
- **Désaccord CNRADA sur le piment** : la fiche CNRADA reprend le texte du G87 (mêmes variétés, même fumure) en inversant la phrase sur la saison ; adaptation à Kaédi ou erreur, aucune source ne le dit.

## Points ouverts (à qui les poser)

1. Saison du piment dans les Niayes avec les variétés actuelles : ISRA-CDH Cambérène (itinéraires techniques 2022), Rama.
2. Alerte pour sol alcalin (pistes : message au-delà de 7,3, « possible » à partir de 8,0 ; classes USDA/FAO et fiche UF/IFAS HS1207, non lues directement) : agronome ou pédologue.
3. pH du jaxatu (groupe Kumba, sans valeur chez PROTA) : ISRA-CDH.
4. Sensibilité du poivron au sel : agronome.
5. Bas-fond pour la carotte et le jaxatu (rien dans le G87 ; PROTA : le jaxatu ne supporte pas l'engorgement) : Rama ou agronome.
6. CCMT (Ghana, Mensah et al., *Data in Brief* 49, 2023) : l'article ne définit ni « leaf blight » (mildiou ? alternariose ?) ni « leaf curl » (quel virus ?). Ces classes ne sont pas fusionnées avec nos maladies ; « leaf blight » n'entre pas dans le modèle v2. À demander aux auteurs (University of Energy and Natural Resources, Sunyani) ou à un phytopathologiste (ISRA, DPV) sur un échantillon d'images.

## Complément : « leaf blight » et « leaf curl » de CCMT (2e recherche, 14 nov 2026)

- **leaf blight : non tranché.** Aucune source primaire. Seule une équipe tierce (Sun et al., BMC Plant Biology 2024, doi:10.1186/s12870-024-05797-9) l'appelle « early blight », sans justification. Contexte ghanéen : l'alternariose est la maladie fongique de la tomate la plus citée (Opoku et al., Ghana J. Agric. Sci. 56(2), 2021, doi:10.4314/gjas.v56i2.5) ; aucune source ghanéenne sur le mildiou. Indice visuel seulement (20 images au hasard) : 1 ressemble au mildiou, 3 à l'alternariose, 15 ambiguës (nécroses de bord, jaunissements) → classe probablement « fourre-tout ». **Décision : exclue du modèle** (ni mildiou, ni alternariose).
- **leaf curl : probablement l'enroulement viral (begomovirus transmis par l'aleurode ; au Ghana : ToLCGhV, ToLCKuV, Osei et al., Plant Disease 92:1585, 2008), non confirmé pour ce jeu** ; indice visuel : 3 images sur 7 montrent un enroulement. **Décision : exclue** (notre classe leaf_curl = TYLCV de PlantVillage).
- **Pour confirmer** : écrire à l'auteur correspondant, Kwabena Adu (adresse publique dans l'article, UENR Sunyani) : pathogène retenu pour « leaf blight » (diagnostic visuel ou laboratoire ?) et virus de « leaf curl » (PCR ?).
