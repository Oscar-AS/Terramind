"""Enregistre la version wolof relue d'une phrase : python3 scripts/outils/relecture_wolof_valider.py <cle> "<wolof>"."""

import csv
import sys

p = "content/voix/messages_wolof.csv"
with open(p, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
champs = list(rows[0].keys())
cle, wo = sys.argv[1], sys.argv[2]
for r in rows:
    if r["cle"] == cle:
        r["texte_wo"], r["statut"], r["relu_par"] = wo, "relu", "Salam"
        break
else:
    sys.exit("clé inconnue")
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=champs)
    w.writeheader()
    w.writerows(rows)
print("ok", cle)
