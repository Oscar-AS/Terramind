"""Génère les bannières SVG des README de chaque dossier (docs/assets/readme/).

Usage (depuis la racine du dépôt) : python3 scripts/outils/generer_bannieres.py
Les SVG sont du texte : ils s'affichent sur GitHub et restent légers.
"""

from pathlib import Path

SORTIE = Path(__file__).resolve().parents[2] / "docs" / "assets" / "readme"

FORET, FEUILLE, OCRE, SABLE, CREME, ENCRE = "#1f4d3a", "#3f8f5f", "#d08a2e", "#f3e3c3", "#fbf7ef", "#14261d"

# Icônes dessinées à la main (repère 120 x 120), en traits blancs.
ICONES = {
    "engine": """<circle cx="60" cy="60" r="22" fill="none" stroke="#fff" stroke-width="8"/>
      <g stroke="#fff" stroke-width="12" stroke-linecap="round">
      <line x1="60" y1="18" x2="60" y2="30"/><line x1="60" y1="90" x2="60" y2="102"/>
      <line x1="18" y1="60" x2="30" y2="60"/><line x1="90" y1="60" x2="102" y2="60"/>
      <line x1="30" y1="30" x2="38" y2="38"/><line x1="82" y1="82" x2="90" y2="90"/>
      <line x1="30" y1="90" x2="38" y2="82"/><line x1="82" y1="38" x2="90" y2="30"/></g>""",
    "channels": """<path d="M16 26 h66 a10 10 0 0 1 10 10 v30 a10 10 0 0 1 -10 10 h-38 l-18 16 v-16 h-10 a10 10 0 0 1 -10 -10 v-30 a10 10 0 0 1 10 -10z" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>
      <rect x="74" y="50" width="34" height="56" rx="7" fill="none" stroke="#fff" stroke-width="7"/>
      <circle cx="91" cy="97" r="3.5" fill="#fff"/>""",
    "dashboard": """<rect x="16" y="20" width="88" height="80" rx="10" fill="none" stroke="#fff" stroke-width="7"/>
      <rect x="32" y="62" width="12" height="26" rx="2" fill="#fff"/><rect x="54" y="46" width="12" height="42" rx="2" fill="#fff"/>
      <rect x="76" y="34" width="12" height="54" rx="2" fill="#fff"/>""",
    "content": """<path d="M30 14 h40 l22 22 v70 h-62z" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>
      <path d="M70 14 v22 h22" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>
      <path d="M44 84 c0 -18 10 -30 28 -32 c0 18 -10 30 -28 32z M44 84 l16 -18" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>""",
    "data": """<ellipse cx="60" cy="28" rx="38" ry="12" fill="none" stroke="#fff" stroke-width="7"/>
      <path d="M22 28 v64 c0 7 17 12 38 12 s38 -5 38 -12 v-64" fill="none" stroke="#fff" stroke-width="7"/>
      <path d="M22 60 c0 7 17 12 38 12 s38 -5 38 -12" fill="none" stroke="#fff" stroke-width="7"/>""",
    "docs": """<path d="M60 30 c-12 -10 -30 -12 -44 -8 v72 c14 -4 32 -2 44 8 c12 -10 30 -12 44 -8 v-72 c-14 -4 -32 -2 -44 8z" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>
      <line x1="60" y1="30" x2="60" y2="102" stroke="#fff" stroke-width="7"/>""",
    "ml": """<rect x="18" y="18" width="84" height="84" rx="12" fill="none" stroke="#fff" stroke-width="7" stroke-dasharray="20 12"/>
      <path d="M38 86 c0 -32 18 -50 46 -52 c0 30 -18 50 -46 52z M38 86 l30 -32" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>""",
    "research": """<circle cx="50" cy="50" r="28" fill="none" stroke="#fff" stroke-width="8"/>
      <line x1="71" y1="71" x2="100" y2="100" stroke="#fff" stroke-width="12" stroke-linecap="round"/>
      <path d="M38 52 l8 8 l16 -18" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>""",
    "scripts": """<rect x="14" y="22" width="92" height="76" rx="10" fill="none" stroke="#fff" stroke-width="7"/>
      <path d="M32 48 l16 12 l-16 12" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="56" y1="74" x2="86" y2="74" stroke="#fff" stroke-width="7" stroke-linecap="round"/>""",
}

BANNIERES = {
    "engine": ("engine/", "Le moteur", "Un seul cerveau pour WhatsApp, l'appli web et le tableau de bord"),
    "channels": ("channels/", "Les façades", "Là où l'agriculteur parle au bot : WhatsApp d'abord, l'appli web en secours"),
    "dashboard": ("dashboard/", "Le tableau de bord", "Ce que l'équipe et les partenaires voient : usage, questions, alertes"),
    "content": ("content/", "Le savoir du bot", "Fiches agronomiques, réponses types et voix wolof, tout sourcé"),
    "data": ("data/", "Les données", "Sols, météo, cultures, prix, images : chaque fichier avec sa source"),
    "docs": ("docs/", "La documentation", "Décisions, architecture, API, risques et sources de recherche"),
    "ml": ("ml/", "L'intelligence artificielle", "Le modèle qui reconnaît une maladie sur la photo d'une feuille"),
    "research": ("research/", "Le terrain", "Base agronomique, tests avec les agriculteurs, consentement"),
    "scripts": ("scripts/", "Les outils", "Scripts qui collectent et vérifient les données, reproductibles"),
}


def banniere(cle, chemin, titre, sous_titre):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260" role="img" aria-label="{titre} : {sous_titre}">
  <defs>
    <linearGradient id="fond" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{FORET}"/><stop offset="1" stop-color="{ENCRE}"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="260" rx="22" fill="url(#fond)"/>
  <!-- dunes stylisées des Niayes -->
  <path d="M0 210 C 220 170 380 240 600 200 S 980 160 1200 205 V260 H0z" fill="{FEUILLE}" opacity="0.35"/>
  <path d="M0 232 C 260 205 460 255 700 228 S 1020 210 1200 232 V260 H0z" fill="{OCRE}" opacity="0.45"/>
  <circle cx="1090" cy="62" r="26" fill="{OCRE}" opacity="0.9"/>
  <g transform="translate(70 62) scale(1.1)">{ICONES[cle]}</g>
  <text x="230" y="92" font-family="Georgia, 'Times New Roman', serif" font-size="22" fill="{SABLE}" letter-spacing="3">TERRAMIND AFRIQUE · {chemin.upper()}</text>
  <text x="230" y="146" font-family="Georgia, 'Times New Roman', serif" font-size="52" font-weight="bold" fill="#ffffff">{titre}</text>
  <text x="230" y="186" font-family="Helvetica, Arial, sans-serif" font-size="22" fill="{CREME}">{sous_titre}</text>
</svg>
"""


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    for cle, (chemin, titre, sous_titre) in BANNIERES.items():
        (SORTIE / f"{cle}.svg").write_text(banniere(cle, chemin, titre, sous_titre), encoding="utf-8")
        print(f"  ok  docs/assets/readme/{cle}.svg")
