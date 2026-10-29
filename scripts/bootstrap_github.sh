#!/usr/bin/env bash
# Crée (ou met à jour) les labels et milestones GitHub du projet. Idempotent : peut être relancé sans risque.
# Prérequis : gh installé et authentifié (gh auth login). Ne crée aucune issue.
# Usage : ./scripts/bootstrap_github.sh            (dépôt déduit du remote origin)
#         REPO=owner/nom ./scripts/bootstrap_github.sh
set -euo pipefail

gh auth status >/dev/null 2>&1 || { echo "gh n'est pas authentifié : lancer 'gh auth login'." >&2; exit 1; }
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
echo "Dépôt : $REPO"

# --- Labels : nom|couleur|description (--force met à jour s'il existe déjà) ---
labels=(
  "module:planification|0E8A16|Module Planification (GPS, sol, cultures, semis)"
  "module:prevention|1D76DB|Module Prévention (météo, risque de mildiou)"
  "module:diagnostic|5319E7|Module Diagnostic (photo de feuille)"
  "canal:whatsapp|25D366|Façade bot WhatsApp"
  "canal:pwa|0052CC|Façade appli web (PWA)"
  "dashboard|FBCA04|Tableau de bord"
  "ml|8B4513|IA et données"
  "content|C2E0C6|Contenu agronomique et gabarits"
  "research|BFD4F2|Recherche utilisateur et tests"
  "docs|D4C5F9|Documentation"
  "bloquant|B60205|Bloque un jalon ou une démo"
  "bug|D73A4A|Comportement incorrect"
  "owner:oscar|EDEDED|Responsable : Oscar"
  "owner:salam|EDEDED|Responsable : Salam"
  "owner:rama|EDEDED|Responsable : Rama"
)
for entry in "${labels[@]}"; do
  IFS='|' read -r name color desc <<<"$entry"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force
done

# --- Milestones : titre|échéance ISO (créés seulement s'ils n'existent pas) ---
milestones=(
  "J1 03/11|2026-11-03T23:59:59Z"
  "J2 10/11|2026-11-10T23:59:59Z"
  "J3 17/11 gel|2026-11-17T23:59:59Z"
  "J4 22/11 fin de construction|2026-11-22T23:59:59Z"
  "J5 25/11 jury|2026-11-25T23:59:59Z"
)
existing="$(gh api "repos/$REPO/milestones?state=all&per_page=100" -q '.[].title')"
for entry in "${milestones[@]}"; do
  IFS='|' read -r title due <<<"$entry"
  if grep -Fxq "$title" <<<"$existing"; then
    echo "Milestone déjà présent : $title"
  else
    gh api "repos/$REPO/milestones" -f title="$title" -f due_on="$due" >/dev/null
    echo "Milestone créé : $title"
  fi
done

echo "Terminé."
