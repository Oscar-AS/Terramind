#!/bin/zsh
# Publie la version web de l'application sur Vercel (projet « terramind-app », lien de production du concours).
# Usage : ./publier-web.sh   (depuis channels/mobile ; le compte Vercel doit être connecté : npx vercel login)
set -e
cd "$(dirname "$0")"
rm -rf dist
EXPO_PUBLIC_ENGINE_URL=https://terramind-moteur.onrender.com npx expo export -p web
DOSSIER="${TMPDIR:-/tmp}/terramind-app"   # le nom du dossier donne le nom du projet Vercel
rm -rf "$DOSSIER" && mkdir -p "$DOSSIER" && cp -R dist/. "$DOSSIER/"
# Application d'une seule page : toutes les adresses (/plan, /alertes…) renvoient vers index.html.
cat > "$DOSSIER/vercel.json" <<'JSON'
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
JSON
cd "$DOSSIER"
npx -y vercel --prod --yes   # le domaine terramind-afrique.vercel.app suit toujours le dernier déploiement
echo "En ligne : https://terramind-afrique.vercel.app"
