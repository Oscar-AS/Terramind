#!/usr/bin/env bash
# Publie le moteur sur l'espace Hugging Face (SDK Docker).
# Usage : bash scripts/outils/deployer_space.sh <utilisateur>/<espace>
# Le jeton d'écriture est lu dans .env (HF_TOKEN_ECRITURE) et n'est jamais affiché.
set -euo pipefail
ESPACE="${1:?usage: deployer_space.sh utilisateur/espace}"
RACINE="$(cd "$(dirname "$0")/../.." && pwd)"
JETON="$(grep '^HF_TOKEN_ECRITURE=' "$RACINE/.env" | cut -d= -f2- | tr -d ' "\r')"
[ -n "$JETON" ] || { echo "HF_TOKEN_ECRITURE vide dans .env"; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git clone -q "https://user:${JETON}@huggingface.co/spaces/${ESPACE}" "$TMP/espace"
cd "$TMP/espace"
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp "$RACINE/deploy/huggingface/Dockerfile" "$RACINE/deploy/huggingface/README.md" .
mkdir -p engine
rsync -a --exclude '__pycache__' --exclude 'tests' "$RACINE/engine/" engine/
git add -A
git -c user.name="TerraMind" -c user.email="noreply@terramind.invalid" commit -q -m "Déploiement du moteur ($(cd "$RACINE" && git rev-parse --short HEAD))" || { echo "rien à publier"; exit 0; }
git push -q origin HEAD
echo "publié sur https://huggingface.co/spaces/${ESPACE}"
