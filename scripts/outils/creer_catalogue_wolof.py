"""Crée content/voix/messages_wolof.csv : toutes les phrases que le bot dit en wolof (notes vocales).

Chaque ligne : une clé (nom du fichier audio content/audio/wo/<cle>.ogg), l'usage, le type de voix
(humaine : enregistrée par un locuteur ; synthese : générée par Kiriku-Wolof-TTS puis écoutée),
le texte français « pour l'oreille » (phrases courtes, aucun chiffre ni symbole, voir docs/voix-wolof.md),
le texte wolof (brouillon puis relu par un locuteur) et son statut.

Les résumés oraux des fiches reprennent uniquement le contenu sourcé des fiches (content/fiches/).
Relancer ce script réécrit les textes français mais conserve les textes wolof déjà saisis.

    python3 scripts/outils/creer_catalogue_wolof.py
"""

import csv
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "content" / "voix" / "messages_wolof.csv"
CHAMPS = ["cle", "usage", "voix", "texte_fr", "texte_wo", "statut", "relu_par"]

H = "humaine"
S = "synthese"
MESSAGES = [
    # --- Guide : voix humaine (accueil et messages sensibles) ---
    ("choix_langue", "au démarrage, avant le choix de la langue (toujours envoyé)", H,
     "Bienvenue sur TerraMind. Pour que je te parle en wolof, touche le bouton Wolof."),
    ("accueil", "après le choix du wolof", H,
     "Bonjour, je suis TerraMind, ton assistant pour le maraîchage. Je peux te dire quoi planter selon ton sol, "
     "surveiller ta culture avec la météo, et examiner la photo d'une feuille malade. Pour commencer, touche le "
     "bouton qui envoie la position de ton champ. Je ne donne jamais de produit chimique : pour un traitement, "
     "je t'envoie vers un agent agricole."),
    ("demande_position", "position nécessaire", H,
     "Pour t'aider, j'ai besoin de connaître ton champ. Touche le bouton qui envoie la position de ton champ, "
     "de préférence quand tu es dans ton champ."),
    ("position_recue", "position reçue", H,
     "Merci, j'ai bien reçu la position de ton champ. Je regarde maintenant ton sol et la saison. "
     "Attends un petit moment."),
    ("conseils_photo", "bouton Examiner une feuille", H,
     "Envoie-moi la photo d'une seule feuille malade. Prends-la de près, pour que la feuille remplisse la photo, "
     "à la lumière du jour, sans ombre."),
    ("attente_photo", "photo reçue", H, "Merci, je regarde ta photo. Attends quelques secondes."),
    ("photo_incertaine", "diagnostic incertain", H,
     "Je ne suis pas sûr de ce que je vois. Plutôt que de te donner une mauvaise réponse, je préfère que tu "
     "reprennes la photo : une seule feuille, de près, à la lumière du jour. Si la plante va mal, montre-la "
     "aussi à un agent agricole."),
    ("photo_illisible", "photo illisible", H,
     "Je n'arrive pas à lire cette photo. Reprends-la, bien nette, de près, à la lumière du jour."),
    ("photo_saine", "feuille saine", H,
     "Bonne nouvelle : cette feuille semble saine. Si d'autres plants ont des taches, envoie-moi leur photo."),
    ("diagnostic_prudence", "après chaque diagnostic", H,
     "Ce n'est qu'une première indication, pas un diagnostic sûr. Pour confirmer, montre ta plante à un agent "
     "agricole."),
    ("pas_de_fiche", "maladie sans fiche", H,
     "Je n'ai pas encore d'explication sur ce problème. Montre ta plante à un agent agricole."),
    ("je_ne_sais_pas", "question sans réponse", H,
     "Je n'ai pas trouvé la réponse dans mes documents, et je préfère ne pas inventer. Pour cette question, "
     "demande à un agent agricole."),
    ("vocal_non_compris", "note vocale reçue", H,
     "Je ne comprends pas encore les messages vocaux. Utilise les boutons en bas de l'écran, ou envoie-moi la "
     "photo d'une feuille malade."),
    ("choix_culture", "bouton Surveiller ma culture", H,
     "Quelle culture veux-tu que je surveille ? Touche son nom dans la liste."),
    ("date_repiquage", "après le choix de la culture", H,
     "À quelle date l'as-tu repiquée ? Écris le jour et le mois. Si tu ne sais plus, écris : je ne sais pas."),
    ("plan_intro", "avant le plan de culture", H,
     "Voici ce que tu peux planter ce mois-ci, selon le sol de ton champ et la saison."),
    ("alerte_rien", "aucune alerte", H,
     "Bonne nouvelle : la météo de cette semaine ne favorise aucune des maladies que je surveille pour ta "
     "culture. Reviens me demander la semaine prochaine."),
    ("alerte_intro", "avant les alertes", H,
     "Attention : la météo de cette semaine demande de surveiller ta culture."),
    ("eau_salee", "fin du plan de culture", H,
     "Une précaution : si l'eau de ton puits est salée, évite l'oignon et la carotte."),

    # --- Alertes météo : voix de synthèse (repris de engine/app/modules/prevention/alerte.py) ---
    ("alerte_late_blight", "alerte mildiou", S,
     "Le temps de ces derniers jours est favorable au mildiou. Regarde le dessous des feuilles : des taches "
     "brunes avec un duvet blanc."),
    ("alerte_alternaria", "alerte alternariose", S,
     "Le temps de ces derniers jours est favorable à l'alternariose. Regarde les vieilles feuilles : des taches "
     "brunes avec des cercles."),
    ("alerte_tuta_absoluta", "alerte mineuse", S,
     "Une nouvelle génération de mineuse de la tomate est probable. Regarde s'il y a des galeries claires dans "
     "les feuilles."),
    ("alerte_plutella_xylostella", "alerte teigne du chou", S,
     "Une nouvelle génération de teigne du chou est probable. Regarde tes choux de près, surtout le dessous des "
     "feuilles."),

    # --- Résumés oraux des fiches (diagnostic photo) : voix de synthèse, 4 temps ---
    ("fiche_maladie-alternariose", "diagnostic alternariose", S,
     "Cela ressemble à l'alternariose. C'est un champignon qui fait des taches brunes avec des cercles, comme "
     "une cible. Il aime l'humidité et peut venir de graines malades. Retire les feuilles brunes, avec des gants. "
     "Pour éviter qu'elle revienne, sème des graines saines, et arrose au pied, le matin, sans mouiller les "
     "feuilles."),
    ("fiche_maladie-mildiou", "diagnostic mildiou", S,
     "Cela ressemble au mildiou. Cette maladie fait sur les feuilles des taches mal délimitées qui brunissent, "
     "et par temps très humide le feuillage sèche vite. Enlève tout de suite les parties malades et brûle-les. "
     "Pour éviter qu'il revienne, espace les plants, arrose au pied, et ne plante pas la tomate à côté de la "
     "pomme de terre."),
    ("fiche_maladie-cladosporiose", "diagnostic cladosporiose", S,
     "Cela ressemble à la cladosporiose. C'est un champignon de la tomate : taches jaunâtres sur le dessus des "
     "feuilles et duvet brun en dessous. Il aime l'air humide et les plants mal aérés. Aère tes plants et "
     "enlève les feuilles du bas déjà atteintes. Pour éviter qu'elle revienne, ne mets pas trop d'engrais "
     "azoté."),
    ("fiche_maladie-tache-bacterienne", "diagnostic tache bactérienne", S,
     "Cela ressemble à la tache bactérienne. C'est une bactérie qui fait de petites taches mouillées qui "
     "noircissent. Elle aime la pluie et la chaleur, et peut venir de graines malades. Pour un traitement, "
     "demande à un agent agricole. Pour éviter qu'elle revienne, utilise des semences saines."),
    ("fiche_maladie-viroses-tomate", "diagnostic virose", S,
     "Cela ressemble à une virose. C'est un virus : les feuilles se déforment et changent de couleur. Sur la "
     "tomate, il est souvent apporté par une petite mouche blanche, dès la pépinière. Montre la plante à un "
     "agent agricole. Pour éviter qu'il revienne, protège la pépinière sous un voile ou une moustiquaire."),
    ("fiche_maladie-fusariose", "diagnostic fusariose", S,
     "Cela ressemble à la fusariose. C'est un champignon du sol qui entre par les racines : la plante jaunit et "
     "se fane. Il reste longtemps dans le sol et peut venir de semences malades. Arrache et élimine les plantes "
     "malades. Pour éviter qu'elle revienne, ne replante pas la même culture au même endroit pendant plusieurs "
     "années, et utilise des semences saines."),
    ("fiche_maladie-fletrissement-bacterien", "diagnostic flétrissement bactérien", S,
     "Cela ressemble au flétrissement bactérien. C'est une bactérie : les feuilles deviennent molles et se "
     "fanent. Elle aime un sol très humide et chaud. Aucun produit n'est efficace : arrache et détruis les "
     "plantes atteintes. Pour éviter qu'il revienne, change de culture, draine bien le sol, et garde tes outils "
     "propres."),
    ("fiche_maladie-septoriose", "diagnostic septoriose", S,
     "Cela ressemble à la septoriose. C'est un champignon qui fait de petites taches rondes avec des points "
     "noirs au centre. Il vit dans les débris de plantes malades et se propage quand les feuilles sont "
     "mouillées. Arrache les plants très atteints. Pour éviter qu'elle revienne, change de culture, enlève les "
     "restes après la récolte, et arrose au pied."),
    ("fiche_maladie-tache-cible", "diagnostic tache cible", S,
     "Cela ressemble à la tache cible. C'est un champignon des pays chauds et humides, qui fait des taches avec "
     "des cercles et un bord jaune. Elle ressemble beaucoup à l'alternariose : fais confirmer par un agent "
     "agricole. Enlève les feuilles du bas atteintes. Pour éviter qu'elle revienne, change de culture et ne "
     "plante pas à côté d'un champ malade."),
    ("fiche_ravageur-noctuelle-tomate", "diagnostic noctuelle", S,
     "Cela ressemble à la noctuelle de la tomate. C'est la chenille d'un papillon, qui troue les fruits. Elle "
     "peut venir des herbes autour du champ. Bine le sol pour éliminer les chenilles. Pour éviter qu'elle "
     "revienne, désherbe autour du champ et change de culture."),
    ("fiche_ravageur-chenilles-oignon", "diagnostic chenilles de l'oignon", S,
     "Je vois des chenilles sur l'oignon. Elles mangent les feuilles, surtout la nuit. Ramasse à la main les "
     "feuilles qui portent des œufs ou des groupes de jeunes chenilles. Pour éviter qu'elles reviennent, "
     "surveille dès la pépinière, laboure le sol, et détruis les mauvaises herbes."),
    ("fiche_ravageur-acariose-tomate", "diagnostic acariens", S,
     "Cela ressemble à des acariens. Ils sont trop petits pour être vus : le dessous des feuilles devient "
     "brillant, puis couleur bronze, et la plante sèche. Regarde le dessous des feuilles. Pour la lutte, "
     "demande à un agent agricole."),
    ("fiche_accident-necrose-apicale", "diagnostic cul noir", S,
     "C'est le cul noir du fruit. Ce n'est pas une maladie contagieuse : la plante manque de calcium, souvent "
     "à cause d'arrosages irréguliers. Arrose de façon régulière, et paille le sol pour le garder frais."),
    ("fiche_accident-coup-de-soleil", "diagnostic coup de soleil", S,
     "C'est un coup de soleil sur le fruit. Ce n'est pas une maladie : le fruit a brûlé au soleil. Mets les "
     "pieds à l'ombre."),
]

# --- Plan de culture : une phrase par culture et par cas (voix de synthèse) ---
CULTURES = {"tomato": "la tomate", "potato": "la pomme de terre", "onion": "l'oignon",
            "cabbage": "le chou", "pepper": "le poivron", "carrot": "la carotte"}
for k, nom in CULTURES.items():
    MESSAGES += [
        (f"culture_{k}_conseillee", f"plan : {nom} conseillée", S, f"Pour {nom}, c'est le bon moment pour planter."),
        (f"culture_{k}_possible", f"plan : {nom} possible", S,
         f"Pour {nom}, c'est possible, avec quelques précautions. Demande conseil à un agent agricole."),
        (f"culture_{k}_deconseillee", f"plan : {nom} déconseillée", S,
         f"Pour {nom}, ce n'est pas le bon moment ce mois-ci."),
    ]


def main():
    anciens = {}
    if SORTIE.exists():
        with SORTIE.open(encoding="utf-8") as f:
            anciens = {r["cle"]: r for r in csv.DictReader(f)}
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS)
        w.writeheader()
        for cle, usage, voix, fr in MESSAGES:
            assert not any(c.isdigit() for c in fr), f"{cle} : pas de chiffre dans un texte lu à voix haute"
            a = anciens.get(cle, {})
            w.writerow({"cle": cle, "usage": usage, "voix": voix, "texte_fr": fr,
                        "texte_wo": a.get("texte_wo", ""), "statut": a.get("statut") or "a_traduire",
                        "relu_par": a.get("relu_par", "")})
    print(f"{len(MESSAGES)} messages dans {SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
