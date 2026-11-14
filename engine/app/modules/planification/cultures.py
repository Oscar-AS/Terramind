"""Exigences des cultures pour le plan (POST /v1/plan).

Tout vient du « Guide pratique du maraîchage au Sénégal » (ISRA/CDH, 1987, cité G87) et du
livret PIESAN oignon (2022, cité LIV), tels que relevés dans
research/base-de-travail-agronomique.md et research/itineraires-par-culture.md.
La traduction en règles (mois, pH minimal, sensibilité au sel, sol lourd) est une proposition
de l'équipe, non validée par un agronome.
"""

G87 = "Guide pratique du maraîchage au Sénégal (ISRA/CDH, 1987)"
LIV = "Bonnes pratiques de production d'oignon dans les Niayes (PIESAN, 2022)"

# sel : "tres_sensible" | "moins_sensible" | None (non indiqué dans le tableau 1 du G87, p. 5)
CULTURES = {
    "tomato": {
        "libelle": "Tomate", "mois_semis": [9, 10, 11, 12, 1, 2, 3, 4],
        "periode": "pépinière de septembre à avril", "cycle_jours": [110, 150],
        "ph_min": 5.5, "sel": "moins_sensible", "sol_lourd_deconseille": True,
        "saison": "La meilleure saison est fraîche et sèche (décembre à juillet).",
        "sources": [{"document": G87, "page": "139-141"}],
    },
    "potato": {
        "libelle": "Pomme de terre", "mois_semis": [10, 11, 12, 1, 2, 3],
        "periode": "plantation d'octobre à mars", "cycle_jours": [75, 100],
        "ph_min": 5.0, "sel": "moins_sensible", "sol_lourd_deconseille": True,
        "saison": "Elle a besoin de la saison fraîche : la chaleur gêne la formation des tubercules.",
        "sources": [{"document": G87, "page": "133-135"}],
    },
    "onion": {
        "libelle": "Oignon", "mois_semis": [10, 11, 12, 1, 2],
        "periode": "semis en pépinière d'octobre à février", "cycle_jours": [70, 150],
        "ph_min": 6.0, "sel": "tres_sensible", "sol_lourd_deconseille": True,
        "saison": "C'est une culture de saison fraîche et sèche.",
        "sources": [{"document": G87, "page": "119-120"}, {"document": LIV, "page": "3"}],
    },
    "cabbage": {
        "libelle": "Chou pommé", "mois_semis": [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7],
        "periode": "septembre à avril ; mai à juillet avec une variété d'hivernage", "cycle_jours": [60, 100],
        "ph_min": 6.0, "sel": "moins_sensible", "sol_lourd_deconseille": False,
        "saison": "La meilleure saison est sèche et fraîche ; en hivernage, il faut une variété adaptée.",
        "hivernage": [5, 6, 7],
        "sources": [{"document": G87, "page": "89-90"}],
    },
    "pepper": {
        "libelle": "Poivron", "mois_semis": [9, 10, 11, 12, 1, 2],
        "periode": "pépinière de septembre à février", "cycle_jours": [120, 180],
        "ph_min": 5.5, "sel": None, "sol_lourd_deconseille": False,
        "saison": "La chaleur fait tomber les fleurs et les fruits : préférer la saison fraîche.",
        "sources": [{"document": G87, "page": "129-130"}],
    },
    "carrot": {
        "libelle": "Carotte", "mois_semis": [10, 11, 12, 1, 2, 3, 4],
        "periode": "semis direct d'octobre à avril", "cycle_jours": [100, 120],
        "ph_min": 5.5, "sel": "tres_sensible", "sol_lourd_deconseille": True,
        "saison": "La chaleur donne des racines courtes et fibreuses : semer en saison fraîche.",
        "sources": [{"document": G87, "page": "85-86"}],
    },
    # Ajoutées le 14 nov 2026 à partir de la proposition d'Oscar (content/regles_sol_culture.csv, branche
    # ml/dataset-merge), en ne gardant que ce que dit le G87 : il n'indique pas de pH pour ces deux cultures
    # (tableau 3, p. 11), donc pas de contrôle du pH. La fiche CNRADA du piment place au contraire les
    # meilleurs résultats en décembre-février : on suit le G87, qui reste la source de toutes les cultures.
    "chili": {
        "libelle": "Piment", "mois_semis": list(range(1, 13)),
        "periode": "semis en pépinière toute l'année", "cycle_jours": [180, 240],
        "ph_min": None, "sel": "moins_sensible", "sol_lourd_deconseille": False,
        "saison": "Les meilleurs résultats viennent en hivernage ; le froid de décembre à février freine sa croissance.",
        "sources": [{"document": G87, "page": "127-128"}],
    },
    "bitter_eggplant": {
        "libelle": "Jaxatu", "mois_semis": list(range(1, 13)),
        "periode": "semis en pépinière toute l'année", "cycle_jours": [130, 200],
        "ph_min": None, "sel": "moins_sensible", "sol_lourd_deconseille": True,
        "saison": "Il pousse toute l'année ; les meilleurs résultats viennent en saison fraîche et sèche, avec irrigation.",
        "sources": [{"document": G87, "page": "107-108"}],
    },
}
SOURCE_SEL = {"document": G87, "page": "5 (tableau 1, salinité)"}
SOURCE_PH = {"document": G87, "page": "11 (tableau 3, pH)"}
