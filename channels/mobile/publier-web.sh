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
# Pas d'écran vide pendant le chargement :
# 1. les 4 polices utilisées sont demandées tout de suite, en même temps que le code ;
# 2. un écran « Chargement » (logo) est dans la page même ; React le remplace dès que l'app est prête.
PRECHARGE=""
for police in Figtree_500Medium Figtree_700Bold BricolageGrotesque_700Bold BricolageGrotesque_800ExtraBold; do
  f=$(cd "$DOSSIER" && find assets/modules -name "${police}.*.ttf" | head -1)
  [ -n "$f" ] && PRECHARGE+="<link rel=\"preload\" href=\"/$f\" as=\"font\" type=\"font/ttf\" crossorigin>"
done
CHARGEMENT='<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;background:#F5EFE3;font-family:system-ui,sans-serif;color:#1F4D3A"><svg width="64" height="64" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#1F4D3A"/><path d="M8 25c0-10 6-16 17-17 0 11-6 16-17 17z" fill="#F5EFE3"/></svg><div style="font-size:17px">Chargement de TerraMind…</div></div>'
PRECHARGE="$PRECHARGE" CHARGEMENT="$CHARGEMENT" perl -pi -e '
  s#<html lang="en">#<html lang="fr">#;
  s#</head>#$ENV{PRECHARGE}<meta name="theme-color" content="\#1F4D3A"></head>#;
  s#<div id="root"></div>#<div id="root">$ENV{CHARGEMENT}</div>#;
' "$DOSSIER/index.html"
# Application d'une seule page : toutes les adresses (/plan, /alertes…) renvoient vers index.html.
# Les fichiers dont le nom contient une empreinte ne changent jamais : le navigateur les garde un an.
cat > "$DOSSIER/vercel.json" <<'JSON'
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "headers": [
    { "source": "/_expo/static/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] },
    { "source": "/assets/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] }
  ]
}
JSON
cd "$DOSSIER"
npx -y vercel --prod --yes   # le domaine terramind-afrique.vercel.app suit toujours le dernier déploiement
echo "En ligne : https://terramind-afrique.vercel.app"
