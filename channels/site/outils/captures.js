// Captures des écrans de l'application pour le site vitrine (channels/site/captures/*.webp).
// À refaire quand l'application est finale (demande de Salam) :
//   1. moteur local :  .venv/bin/python -m uvicorn engine.app.main:app --port 8000
//   2. app web :       cd channels/mobile && EXPO_PUBLIC_ENGINE_URL=http://127.0.0.1:8000 npx expo start --web --port 8081
//   3. ici :           mkdir -p /tmp/cap && cd /tmp/cap && npm i puppeteer && node "<chemin>/channels/site/outils/captures.js"
//   4. conversion :    les PNG de /tmp/cap/ en WebP (qualité 82) dans channels/site/captures/
// Taille : écran d'iPhone 16 (393 × 852 points, Apple), densité 2.
// Profil de démonstration : Rufisque, tomate plantée le 20 octobre (aucune donnée réelle d'agriculteur).
// Photo du diagnostic : feuille_tom2024_test.jpg, mildiou de la tomate tiré du jeu de TEST de TOM2024
// (CC BY 4.0, Project-AgML/TOM2024_disease_classification ; image jamais vue à l'entraînement, graine 2026).
const path = require('path');
const puppeteer = require('puppeteer');
const BASE = 'http://localhost:8081';
const PROFIL = { id: 'm-demo00000000000', langue: 'fr', position: { lat: 14.76, lon: -17.21, nom: 'Rufisque' },
  eauSalee: 'non', basFond: 'non', culture: 'tomato', dateRepiquage: '2026-10-20' };
const pause = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({ headless: 'new' });
  const page = async (profil) => {
    const p = await b.newPage();
    await p.setViewport({ width: 393, height: 852, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    if (profil) await p.evaluateOnNewDocument((v) => localStorage.setItem('terramind.profil', v), JSON.stringify(profil));
    return p;
  };
  const neuf = await page(null);
  for (const [nom, chemin] of [['bienvenue', '/bienvenue'], ['langue', '/bienvenue/langue'], ['position', '/bienvenue/position']]) {
    await neuf.goto(BASE + chemin, { waitUntil: 'networkidle0', timeout: 180000 }); await pause(4000);
    await neuf.screenshot({ path: `app_${nom}.png` });
  }
  const p = await page(PROFIL);
  for (const nom of ['accueil', 'plan', 'alertes']) {
    await p.goto(`${BASE}/${nom}`, { waitUntil: 'networkidle0', timeout: 180000 }); await pause(7000);
    await p.screenshot({ path: `app_${nom}.png` });
  }
  // Diagnostic : comme un utilisateur, on choisit la photo dans la galerie (vrai clic, sinon pas de sélecteur).
  await p.goto(BASE + '/diagnostic', { waitUntil: 'networkidle0', timeout: 180000 }); await pause(2500);
  const [choix] = await Promise.all([p.waitForFileChooser({ timeout: 20000 }), p.click('::-p-text(Choisir dans ma galerie)')]);
  await choix.accept([path.join(__dirname, 'feuille_tom2024_test.jpg')]);
  await pause(12000);
  await p.screenshot({ path: 'app_resultat.png' });
  await p.evaluate(() => { const s = [...document.querySelectorAll('div')].filter((d) => d.scrollHeight > d.clientHeight + 50 && getComputedStyle(d).overflowY !== 'visible'); (s[s.length - 1] || document.scrollingElement).scrollBy(0, 640); });
  await pause(1500);
  await p.screenshot({ path: 'app_resultat2.png' });
  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });
