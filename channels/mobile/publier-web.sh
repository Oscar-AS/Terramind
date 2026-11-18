#!/bin/zsh
# Publie la version web de l'application sur Vercel (projet « terramind-app », lien de production du concours).
# Usage : ./publier-web.sh   (depuis channels/mobile ; le compte Vercel doit être connecté : npx vercel login)
set -e
cd "$(dirname "$0")"
rm -rf dist
EXPO_PUBLIC_ENGINE_URL=https://terramind-moteur.onrender.com npx expo export -p web
DOSSIER="${TMPDIR:-/tmp}/terramind-app"   # le nom du dossier donne le nom du projet Vercel
rm -rf "$DOSSIER" && mkdir -p "$DOSSIER" && cp -R dist/. "$DOSSIER/"
# Vercel n'envoie jamais les dossiers « node_modules » : les polices rangées dans assets/node_modules
# manquaient en ligne et l'app restait sur un écran vide. On renomme le dossier et ses références.
if [ -d "$DOSSIER/assets/node_modules" ]; then
  mv "$DOSSIER/assets/node_modules" "$DOSSIER/assets/modules"
  grep -rl 'assets/node_modules/' "$DOSSIER" | xargs perl -pi -e 's#assets/node_modules/#assets/modules/#g'
fi
# Les navigateurs gardent l'ancien favicon en cache : son nom change avec son contenu.
EMPREINTE=$(shasum "$DOSSIER/favicon.ico" | cut -c1-8)
cp "$DOSSIER/favicon.ico" "$DOSSIER/favicon-$EMPREINTE.ico"
grep -rl 'href="/favicon.ico"' "$DOSSIER" --include='*.html' | xargs perl -pi -e "s#href=\"/favicon.ico\"#href=\"/favicon-$EMPREINTE.ico\"#g"
# Application d'une seule page : toutes les adresses (/plan, /alertes…) renvoient vers index.html.
cat > "$DOSSIER/vercel.json" <<'JSON'
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
JSON
cd "$DOSSIER"
npx -y vercel --prod --yes   # le domaine terramind-afrique.vercel.app suit toujours le dernier déploiement
echo "En ligne : https://terramind-afrique.vercel.app"
