import csv, sys
p = "content/voix/messages_wolof.csv"
rows = list(csv.DictReader(open(p)))
champs = list(rows[0].keys())
cle, wo = sys.argv[1], sys.argv[2]
for r in rows:
    if r["cle"] == cle:
        r["texte_wo"], r["statut"], r["relu_par"] = wo, "relu", "Salam"
        break
else:
    sys.exit("clé inconnue")
w = csv.DictWriter(open(p, "w", newline=""), fieldnames=champs); w.writeheader(); w.writerows(rows)
print("ok", cle)
