import csv
import sys

cat = {r["cle"]: r for r in csv.DictReader(open("content/voix/messages_wolof.csv"))}
con = {r["cle"]: r for r in csv.DictReader(open("content/voix/traductions_concordance.csv"))}
ordre = [k for k, r in cat.items() if r["statut"] == "a_relire"]
debut, n = int(sys.argv[1]), int(sys.argv[2])
for i, k in enumerate(ordre[debut : debut + n], debut + 1):
    r, c = cat[k], con.get(k, {})
    print(f"#{i}/{len(ordre)} {k} | usage: {r['usage']}")
    print("FR:", r["texte_fr"])
    print("FR concordance identique:", c.get("texte_fr") == r["texte_fr"])
    print("RETENU:", r["texte_wo"], "| choisi:", c.get("choisi"))
    for s in ("gemini", "nllb", "teranga"):
        print(f"  {s}: {c.get('wo_'+s)}  <= retour: {c.get('retour_'+s)}")
    print("PROBLEMES:", c.get("problemes"))
    print()
