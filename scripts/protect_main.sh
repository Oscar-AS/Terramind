#!/usr/bin/env bash
# CONDITION : à lancer SEULEMENT APRÈS que la CI a tourné au moins une fois sur main,
# sinon la vérification obligatoire `ci-ok` n'existe pas encore pour GitHub.
# Réglages du dépôt + protection de main. Idempotent. Prérequis : gh authentifié avec droits admin.
# Usage : ./scripts/protect_main.sh            (dépôt déduit du remote origin)
#         REPO=owner/nom ./scripts/protect_main.sh
set -euo pipefail

gh auth status >/dev/null 2>&1 || { echo "gh n'est pas authentifié : lancer 'gh auth login'." >&2; exit 1; }
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
echo "Dépôt : $REPO"

# --- 1. Réglages du dépôt : squash seulement, branches fusionnées supprimées, pas d'auto-merge ---
gh api -X PATCH "repos/$REPO" \
  -F allow_squash_merge=true \
  -F allow_merge_commit=false \
  -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true \
  -F allow_auto_merge=false \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY >/dev/null
echo "Réglages de fusion appliqués."

# --- 2. Protection de main (PUT : remplace la règle existante, donc relançable) ---
# Relecture CODEOWNERS non obligatoire : chaque dossier n'a qu'un propriétaire, qui ne peut pas
# approuver sa propre PR. La rendre obligatoire bloquerait toute PR de son propre périmètre.
# CODEOWNERS continue de demander automatiquement la relecture au bon membre.
protection=$(cat <<'JSON'
{
  "required_status_checks": { "strict": true, "checks": [{ "context": "ci-ok" }] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
)

if output=$(printf '%s' "$protection" | gh api -X PUT "repos/$REPO/branches/main/protection" --input - 2>&1); then
  echo "Protection de main appliquée."
elif grep -qiE "upgrade to github pro|make this repository public|not available" <<<"$output"; then
  # --- 3. Plan gratuit + dépôt privé : on prévient sans échouer ---
  echo "Protection non disponible sur ce plan : rends le dépôt public (après vérification qu'il ne contient aucun secret) ou active GitHub Pro. En attendant, la règle reste celle de CONTRIBUTING.md"
else
  echo "Échec de la protection de main :" >&2
  echo "$output" >&2
  exit 1
fi
