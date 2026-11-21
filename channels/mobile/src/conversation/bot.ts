// La conversation de l'application : même parcours, mêmes textes et mêmes notes vocales que le bot Telegram
// (engine/app/routes/telegram.py, fonction traiter). Le moteur ne change pas : on appelle les mêmes points
// d'entrée /v1 (plan, alert, diagnose, chat, chat/vocal) et les notes vocales servies sur /audio/wo/.
// Toute modification d'un texte ou d'un parcours du bot doit être reportée ici, et inversement.
//
// Mise en forme : <b>gras</b> et <i>italique</i>, comme le HTML de Telegram (lu par components/Bulle.tsx).
import {
  type Alertes, type Diagnostic, ErreurReseau, type Plan, type Source,
  demanderAlertes, demanderPlan, diagnostiquer, poserQuestion, poserQuestionVocale,
} from '@/api';
import { type OuiNon, profil } from '@/profil';

export const B_POSITION = 'Envoyer la position de mon champ';
export const B_PHOTO = 'Voir si ma plante est malade';
export const B_PLAN = 'Que planter dans mon champ ?';
export const B_ALERTES = "Que dois-je retenir concernant la météo de cette semaine pour mes plantes ?";
export const B_QUESTION = "J'ai une question à te poser";
// Démonstration (décision de Salam, 15 nov 2026) : position fixe des Niayes (Rufisque) pour essayer sans révéler
// où l'on est. À retirer si TerraMind est retenu : EXPO_PUBLIC_POSITION_TEST=0 au moment de compiler.
export const B_POSITION_TEST = 'Envoyer une position test';
export const AVEC_POSITION_TEST = process.env.EXPO_PUBLIC_POSITION_TEST !== '0';
const POSITION_TEST = { nom: 'Rufisque', lat: 14.76, lon: -17.21 };

// En wolof, chaque bouton porte un numéro, que les notes vocales citent (« appuie sur le 2 »).
// Bouton test : numéro 0, en tout premier (demande de Rama, 21 nov 2026), dans le bot comme dans l'application.
const NUMEROS: Record<string, number> = {
  [B_POSITION_TEST]: 0, [B_POSITION]: 1, [B_PHOTO]: 2, [B_PLAN]: 3, [B_ALERTES]: 4, [B_QUESTION]: 5,
};

/** Les grands boutons du bas de l'écran (clavier du bot), un par ligne, numérotés et rangés par numéro en wolof. */
export function clavier(langue: 'fr' | 'wo' | undefined): { texte: string; bouton: string }[] {
  const boutons = [...(AVEC_POSITION_TEST ? [B_POSITION_TEST] : []), B_POSITION, B_PHOTO, B_PLAN, B_ALERTES, B_QUESTION];
  if (langue !== 'wo') return boutons.map((b) => ({ texte: b, bouton: b }));
  return [...boutons].sort((a, b) => NUMEROS[a] - NUMEROS[b]).map((b) => ({ texte: `${NUMEROS[b]}. ${b}`, bouton: b }));
}

const AGENT = "un agent agricole (ANCAR, service départemental de l'agriculture)";

const ACCUEIL =
  '<b>Bonjour, je suis TerraMind.</b>\n' +
  "Je suis ton assistant pour le maraîchage dans les Niayes. Je t'accompagne pas à pas, à partir de " +
  'documents agricoles publiés (ISRA, FAO, DPV) et de la météo de la zone de ton champ.\n\n' +
  '<b>Ce que je peux faire pour toi</b>\n' +
  '1. Te dire quoi planter ce mois-ci, selon le sol de ton champ.\n' +
  '2. Surveiller ta culture et te dire si la météo de ces derniers jours favorise une maladie ou un ravageur.\n' +
  "3. Regarder la photo de ta plante malade et t'expliquer quoi faire.\n\n" +
  '<b>Par où commencer</b>\n' +
  `Partage la position de ton champ avec le bouton « ${B_POSITION} », en bas de l'écran. ` +
  "Tu peux aussi m'envoyer directement une photo de ta plante, ou me poser ta question par écrit " +
  '(en français), ou en message vocal en wolof.\n\n' +
  "<i>Je ne donne jamais de nom de produit ni de dose : pour un traitement, je t'oriente vers " +
  `${AGENT}.</i>`;
const CONSEILS_PHOTO =
  "1. Montre ce qui t'inquiète : une feuille, un fruit, une tige ou toute la plante.\n" +
  "2. Approche-toi, pour que je voie bien les taches ou les trous.\n" +
  '3. À la lumière du jour, sans ombre.';
const DEMANDE_POSITION =
  "Pour cela, j'ai besoin de connaître ton champ.\n\n" +
  '<b>Ce que tu peux faire ensuite</b>\n' +
  `Touche le bouton « ${B_POSITION} » en bas de l'écran, de préférence quand tu es dans ton champ.`;
const CHOIX_LANGUE =
  '<b>Bienvenue sur TerraMind.</b>\n' +
  'En quelle langue veux-tu que je te parle ? Touche « Wolof » ou « Français ».\n\n' +
  '<i>En wolof, je te réponds par des messages vocaux, avec le texte en français en dessous.</i>';
const JE_NE_SAIS_PAS =
  "Je n'ai pas trouvé la réponse dans mes fiches, et je préfère ne pas inventer.\n" +
  `Pour cette question, le mieux est de demander à ${AGENT}.\n\n` +
  '<b>Ce que je sais faire</b>\n' +
  '• Te dire quoi planter, selon ton sol.\n' +
  '• Surveiller ta culture selon la météo.\n' +
  '• Regarder la photo de ta plante malade.';

// Même ordre que engine/app/modules/planification/cultures.py : la note vocale « choix_culture » cite ces numéros.
const CULTURES: [string, string][] = [
  ['tomato', 'Tomate'], ['potato', 'Pomme de terre'], ['onion', 'Oignon'], ['cabbage', 'Chou pommé'],
  ['pepper', 'Poivron'], ['carrot', 'Carotte'], ['chili', 'Piment'], ['bitter_eggplant', 'Jaxatu'],
];
const libelleCulture = (id: string) => CULTURES.find(([k]) => k === id)?.[1] ?? id;

// ── Ce que la conversation reçoit et renvoie ──────────────────────────────────────────────────────────────
export type BoutonEnLigne = { texte: string; action: string };
export type Entree =
  | { texte: string }
  | { action: string } // bouton sous un message : « langue:wo », « eau:oui », « culture:tomato »…
  | { position: { lat: number; lon: number } }
  | { photo: { uri: string; type: string | null } }
  | { vocal: { uri: string; duree: number } };

export type Sortie = {
  /** Message écrit du bot, avec ses boutons éventuels (lignes de boutons). */
  envoyer: (texte: string, boutons?: BoutonEnLigne[][]) => void;
  /** Note vocale wolof préparée (clé de content/audio/wo/). */
  noteVocale: (cle: string) => void;
  /** Réponse dite en wolof par Octopus (adresse relative au moteur). */
  voix: (adresse: string) => void;
};

const langue = () => profil.lire().langue;

function dire(s: Sortie, cle: string, toujours = false) {
  if (toujours || langue() === 'wo') s.noteVocale(cle);
}

// ── Petits utilitaires repris du bot ─────────────────────────────────────────────────────────────────────
const echapper = (t: string) => t.replace(/</g, '‹').replace(/>/g, '›');
const liste = (lignes: string[]) => lignes.map((l) => `• ${echapper(l)}`).join('\n');
const nombreFr = (x: number) => String(Number(x.toPrecision(6))).replace('.', ',');
const NIVEAUX_PH: [number, string][] = [
  [5.6, 'très acide'], [6.6, 'un peu acide'], [7.4, 'ni acide ni basique'],
  [8.5, "un peu basique (le contraire d'acide)"], [99, "très basique (le contraire d'acide)"],
];
function phrasePh(ph: number) {
  const mots = NIVEAUX_PH.find(([limite]) => ph < limite)![1];
  return mots.startsWith('ni ') ? `ton sol n'est ${mots}` : `ton sol est ${mots}`;
}
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
function periodeFr(debut: string, fin: string) {
  const [d, f] = [debut, fin].map((x) => x.slice(0, 10).split('-').map(Number));
  if (d[1] === f[1]) return `du ${d[2]} au ${f[2]} ${MOIS[f[1] - 1]}`;
  return `du ${d[2]} ${MOIS[d[1] - 1]} au ${f[2]} ${MOIS[f[1] - 1]}`;
}
const NOMS_LISIBLES: [string, string][] = [
  ['Beniest J. et al.', 'Guide pratique du maraîchage au Sénégal (ISRA / FAO)'],
  ['Sylla S.', 'Thèse sur la mineuse de la tomate (UCAD / CIRAD)'],
  ['Pfeiffer D. G. et al.', 'Florida Entomologist (2013)'],
  ['Diallo et al. 2015', 'African Crop Science Journal (2015)'],
  ['Blancard D.', 'Ephytia (INRAE)'],
  ['Zitter T. A.', 'Université Cornell'],
  ['Spry C.', 'Université du Kentucky'],
  ['Jackson G.', 'Pacific Pests (fiche 163)'],
  ['Panthee D. R.', 'International Journal of Vegetable Science'],
];
/** Nom court d'une source (comme _court du bot) ; null pour nos notes internes et le modèle photo. */
function court(document: string): string | null {
  if (document.startsWith('Seuils météo des maladies et ravageurs') || document.startsWith('Modèle TerraMind')) return null;
  const lisible = NOMS_LISIBLES.find(([auteur]) => document.startsWith(auteur));
  if (lisible) return lisible[1];
  let nom = document.split(',')[0].trim();
  if ((nom.match(/\(/g) ?? []).length > (nom.match(/\)/g) ?? []).length) nom = nom.slice(0, nom.lastIndexOf('(')).trim();
  return nom;
}

// ── Parcours ─────────────────────────────────────────────────────────────────────────────────────────────
const QUESTIONS_CHAMP = {
  eau: { voix: 'question_eau_salee', texte: "<b>Une question sur ton eau</b>\nL'eau de ton puits est-elle salée ?", champ: 'eauSalee' },
  basfond: {
    voix: 'question_bas_fond',
    texte: '<b>Une question sur ton champ</b>\nTon champ est-il dans un bas-fond, un endroit bas où l\'eau reste longtemps après la pluie ?',
    champ: 'basFond',
  },
} as const;

function demanderChamp(s: Sortie): boolean {
  const p = profil.lire();
  for (const [cle, q] of Object.entries(QUESTIONS_CHAMP)) {
    if (p[q.champ] === undefined) {
      dire(s, q.voix);
      const wo = p.langue === 'wo';
      s.envoyer(q.texte, [[
        { texte: wo ? '1. Oui' : 'Oui', action: `${cle}:oui` },
        { texte: wo ? '2. Non' : 'Non', action: `${cle}:non` },
        { texte: wo ? '3. Je ne sais pas' : 'Je ne sais pas', action: `${cle}:ne_sait_pas` },
      ]]);
      return true;
    }
  }
  return false;
}

async function plan(s: Sortie) {
  if (demanderChamp(s)) return; // le plan suivra la dernière réponse
  s.envoyer('Je regarde maintenant le sol de ton champ et la saison. Cela prend environ 30 secondes.');
  const r = await demanderPlan();
  if (r.statut !== 'ok') {
    s.envoyer(
      "Je n'arrive pas à lire la carte des sols à cet endroit pour le moment. " +
      `Réessaie dans quelques minutes avec le bouton « ${B_PLAN} ».`,
    );
    return;
  }
  const d: Plan = r.donnees;
  const eauSalee = profil.lire().eauSalee;
  const groupes = { conseillee: d.cultures.filter((c) => c.adaptation === 'conseillee'), possible: d.cultures.filter((c) => c.adaptation === 'possible'), deconseillee: d.cultures.filter((c) => c.adaptation === 'deconseillee') };
  dire(s, 'plan_intro');
  for (const c of [...groupes.conseillee, ...groupes.possible]) dire(s, `culture_${c.culture}_${c.adaptation}`);
  if (eauSalee === 'ne_sait_pas') dire(s, 'eau_salee');

  const sol = d.sol;
  const blocs = [
    "<b>Ce qu'il faut savoir sur ton sol</b>\nD'après la carte des sols iSDAsoil, ton champ " +
    (sol.sable_pct != null ? `contient environ ${Math.round(sol.sable_pct)} % de sable ` : '') +
    (sol.ph != null ? `et son pH est de ${nombreFr(sol.ph)} : ${phrasePh(sol.ph)}.` : '(pH inconnu à cet endroit).'),
  ];
  const ligne = (c: Plan['cultures'][number]) =>
    `• ${echapper(c.libelle)} : ${echapper(c.periode_semis)}` + c.avertissements.map((a) => `\n   <i>${echapper(a)}</i>`).join('');
  if (groupes.conseillee.length) blocs.push('<b>Ce que tu peux planter maintenant</b>\n' + groupes.conseillee.map(ligne).join('\n'));
  if (groupes.possible.length) blocs.push('<b>Ce que tu peux planter, avec quelques précautions</b>\n' + groupes.possible.map(ligne).join('\n'));
  if (groupes.deconseillee.length) {
    blocs.push("<b>Ce qu'il vaut mieux ne pas planter ce mois-ci</b>\n" + echapper(groupes.deconseillee.map((c) => c.libelle).join(', ')) + '.');
  }
  if (eauSalee === 'ne_sait_pas') {
    blocs.push("<b>Une précaution importante</b>\nSi l'eau de ton puits est salée, évite l'oignon et la carotte.");
  }
  blocs.push(
    '<b>Ce que tu peux faire ensuite</b>\n' +
    `Si une culture est déjà en place, touche « ${B_ALERTES} » : je regarde si la météo de la ` +
    'semaine favorise une maladie. Si tu vois des taches sur ta plante (feuille, fruit, tige), envoie-moi une photo.',
  );
  blocs.push('<i>Sources : Guide pratique du maraîchage au Sénégal (ISRA, 1987) ; carte des sols iSDAsoil.</i>');
  dire(s, 'plan_suite');
  s.envoyer(blocs.join('\n\n'));
}

async function alertes(s: Sortie) {
  const p = profil.lire();
  const r = await demanderAlertes();
  if (r.statut !== 'ok') {
    s.envoyer('La météo est momentanément indisponible. Réessaie dans quelques minutes.');
    return;
  }
  const d: Alertes = r.donnees;
  const culture = libelleCulture(p.culture!).toLowerCase();
  if (!d.alertes.length) { // aucune règle météo pour cette culture : ne pas dire « rien d'inquiétant »
    dire(s, 'alerte_pas_de_regle');
    s.envoyer(
      `<b>Pour ta culture (${echapper(culture)}), je ne surveille pas encore la météo.</b>\n` +
      "Je n'ai pas de règle sourcée qui relie le temps aux maladies de cette culture.\n\n" +
      '<b>Ce que tu peux faire</b>\nSi tu vois des taches sur ta plante (feuille, fruit, tige), envoie-moi une photo.',
    );
    return;
  }
  const actives = d.alertes.filter((a) => a.niveau !== 'aucun' && a.conseil);
  if (actives.length) {
    dire(s, 'alerte_intro');
    for (const a of actives) dire(s, `alerte_${a.risque}`);
  } else {
    dire(s, 'alerte_rien');
  }
  const [debut, fin] = d.meteo.periode;
  // NASA POWER donne la météo MESURÉE (avec quelques jours de retard), pas une prévision : le titre le dit.
  const blocs = [
    `<b>Ce que la météo de ces derniers jours dit pour ta culture (${echapper(culture)})</b>\n` +
    `J'ai regardé la météo de la zone de ton champ ${periodeFr(debut, fin)}.`,
  ];
  if (actives.length) blocs.push("<b>Ce qu'il faut surveiller</b>\n" + liste(actives.map((a) => a.conseil!)));
  else {
    blocs.push(
      "<b>Bonne nouvelle : rien d'inquiétant pour le moment</b>\nLa météo de ces derniers jours ne favorise aucune " +
      'des maladies ni aucun des ravageurs que je surveille pour cette culture.',
    );
  }
  blocs.push(
    '<b>Ce que tu peux faire ensuite</b>\n' +
    `Reviens me demander la semaine prochaine avec le bouton « ${B_ALERTES} ». ` +
    'Si tu vois des taches sur ta plante (feuille, fruit, tige), envoie-moi une photo.',
  );
  blocs.push(
    "<i>Météo : NASA POWER. Ces règles viennent d'études faites hors du Sénégal : je parle de " +
    'conditions favorables, pas de maladie certaine.</i>',
  );
  if (d.alertes.some((a) => a.niveau === 'date_requise')) {
    profil.ecrire({ dateLibre: true }); // la date pourra être écrite à n'importe quel moment
    blocs.push(
      "<b>Pour surveiller aussi les insectes</b>\nÉcris-moi le jour où tu l'as plantée, " +
      'comme ça : <b>15/10</b> pour le 15 octobre.',
    );
  }
  s.envoyer(blocs.join('\n\n'));
  s.envoyer('Tu veux surveiller une autre culture ?', [[{ texte: 'Changer de culture', action: 'changer_culture' }]]);
}

function choisirCulture(s: Sortie) {
  const wo = langue() === 'wo';
  dire(s, 'choix_culture');
  s.envoyer(
    '<b>Quelle culture veux-tu que je surveille ?</b>\nChoisis-la dans la liste.',
    CULTURES.map(([k, l], i) => [{ texte: wo ? `${i + 1}. ${l}` : l, action: `culture:${k}` }]),
  );
}

function sansPosition(s: Sortie) {
  dire(s, 'demande_position');
  s.envoyer(DEMANDE_POSITION);
}

function verifierAussi(d: Diagnostic) {
  return (d.questions_suivi ?? [])
    .map((q) => `\n\n<b>À vérifier aussi</b>\n${echapper(q.question)}\n<i>Si oui : ${echapper(q.si_oui)}</i>`)
    .join('');
}

const PARTIES_FICHE = {
  ce_que_c_est: "Ce que c'est", pourquoi: "Pourquoi c'est arrivé", que_faire: 'Que faire maintenant', eviter: 'Pour que ça ne revienne pas',
} as const;

async function photo(s: Sortie, uri: string, type: string | null) {
  dire(s, 'attente_photo');
  s.envoyer('Merci, je regarde ta photo. Cela prend quelques secondes.');
  const r = await diagnostiquer(uri, type);
  if (r.statut === 'erreur') {
    if (r.message.texte.includes('indisponible')) {
      s.envoyer("L'examen des photos est momentanément indisponible. Réessaie plus tard.");
      return;
    }
    dire(s, 'photo_illisible');
    s.envoyer("Je n'arrive pas à lire cette photo. Peux-tu la reprendre, bien nette ?\n\n" + CONSEILS_PHOTO);
    return;
  }
  if (r.statut === 'incertain') {
    dire(s, 'photo_incertaine');
    s.envoyer(
      '<b>Je ne suis pas sûr de ce que je vois.</b>\n' +
      'Plutôt que de te donner une mauvaise réponse, je préfère que tu reprennes la photo.\n\n' +
      '<b>Comment reprendre la photo</b>\n' + CONSEILS_PHOTO + '\n\n' +
      `<i>Si la plante va mal, montre-la aussi à ${AGENT}.</i>`,
    );
    return;
  }
  const d = r.donnees;
  const top = d.predictions[0];
  if (top.categorie === 'sain') {
    dire(s, 'photo_saine');
    s.envoyer(
      '<b>Bonne nouvelle : ce que je vois semble sain.</b>\n' +
      'Je ne vois pas de signe de maladie sur cette photo.\n\n' +
      "<b>Ce que tu peux faire ensuite</b>\nSi d'autres plants ont des taches, envoie-moi leur photo." + verifierAussi(d),
    );
    return;
  }
  const tete =
    '<b>Ce que je vois sur ta photo</b>\n' +
    `Cela ressemble à : <b>${echapper(top.libelle)}</b> ` +
    `(confiance du modèle : ${Math.round(top.confiance * 100)} %).\n` +
    "C'est une première indication, pas un diagnostic sûr.";
  dire(s, d.fiche ? `fiche_${d.fiche.fiche}` : 'pas_de_fiche');
  dire(s, 'diagnostic_prudence');
  const suite =
    '<b>Ce que tu peux faire ensuite</b>\n' +
    `Pour confirmer, montre ta plante à ${AGENT}. ` +
    "Tu peux aussi m'écrire une question sur ce problème.";
  if (!d.fiche) {
    s.envoyer(`${tete}\n\nJe n'ai pas encore de fiche sur ce problème.\n\n${suite}` + verifierAussi(d));
    return;
  }
  const fiche = d.fiche;
  let n = 0;
  const blocs: string[] = [];
  for (const [cle, titre] of Object.entries(PARTIES_FICHE) as [keyof typeof PARTIES_FICHE, string][]) {
    const texte = fiche[cle];
    if (!texte) continue;
    n += 1;
    const lignes = texte.split('\n').filter((l) => l.trim()).map((l) => l.replace(/^[-\s]+/, '').trim());
    blocs.push(`<b>${n}. ${echapper(titre)}</b>\n` + liste(lignes));
  }
  // Sources de la fiche seulement (le moteur y ajoute le modèle photo et la source de la question de suivi).
  const suivi = new Set((d.questions_suivi ?? []).map((q) => (q as { source?: Source }).source?.document));
  const documents = [...new Set(r.sources.filter((x) => !suivi.has(x.document)).map((x) => court(x.document)).filter((x): x is string => !!x))].sort();
  const sources = '<i>Sources : ' + echapper(documents.join(' ; ')) + '</i>';
  s.envoyer(`${tete}\n\n${blocs.join('\n\n')}\n\n${suite}${verifierAussi(d)}\n\n${sources}`);
}

async function question(s: Sortie, texte: string) {
  const r = await poserQuestion(texte);
  if (r.statut !== 'ok') {
    dire(s, 'je_ne_sais_pas');
    s.envoyer(JE_NE_SAIS_PAS);
    return;
  }
  repondre(s, r.message.texte, r.sources);
}

function repondre(s: Sortie, texte: string, sources: Source[]) {
  const liste = sources
    .filter((x) => court(x.document))
    .slice(0, 3)
    .map((x) => court(x.document)! + (/^\d/.test(x.page) ? `, p. ${x.page}` : ''))
    .join(' ; ');
  s.envoyer(`${echapper(texte.replace(/\*\*/g, ''))}` + (liste ? `\n\n<i>Sources : ${echapper(liste)}</i>` : ''));
}

async function vocal(s: Sortie, uri: string, duree: number) {
  const ecrire = 'Tu peux aussi écrire ta question, ou utiliser les boutons en bas de l\'écran.';
  if (duree > 60) {
    dire(s, 'vocal_trop_long');
    s.envoyer('Ta note vocale est trop longue pour moi. Pose ta question en moins d\'une minute.');
    return;
  }
  dire(s, 'vocal_ecoute');
  s.envoyer("J'écoute ta note vocale. Cela prend quelques secondes.");
  const r = await poserQuestionVocale(uri, duree);
  const compris = r.donnees?.transcription?.francais;
  if (r.statut === 'erreur') {
    if (r.message.texte.includes('trop longue')) {
      dire(s, 'vocal_trop_long');
      s.envoyer('Ta note vocale est trop longue pour moi. Pose ta question en moins d\'une minute.');
    } else {
      dire(s, 'vocal_indisponible');
      s.envoyer(`Je ne peux pas écouter les messages vocaux pour le moment. ${ecrire}`);
    }
    return;
  }
  if (!compris) {
    dire(s, 'vocal_non_compris');
    s.envoyer(`Je n'ai pas bien compris ta note vocale. Peux-tu la redire plus lentement, dans un endroit calme ? ${ecrire}`);
    return;
  }
  // L'agriculteur voit ce qui a été compris : s'il y a une erreur, il peut reformuler.
  s.envoyer(`<i>J'ai compris ta question ainsi : « ${echapper(compris)} »</i>`);
  if (r.statut !== 'ok') {
    dire(s, 'je_ne_sais_pas');
    s.envoyer(JE_NE_SAIS_PAS);
    return;
  }
  if (r.donnees.voix?.audio_url) s.voix(r.donnees.voix.audio_url);
  repondre(s, r.message.texte, r.sources);
}

function poserLangue(s: Sortie) {
  dire(s, 'choix_langue', true); // la question est aussi dite en wolof
  s.envoyer(CHOIX_LANGUE, [[{ texte: 'Wolof', action: 'langue:wo' }, { texte: 'Français', action: 'langue:fr' }]]);
}

/** Ouverture de l'application sans conversation : la question de la langue, comme /start sur le bot. */
export function demarrer(s: Sortie) {
  poserLangue(s);
}

async function action(s: Sortie, donnee: string) {
  const [cle, reponse] = donnee.split(':');
  const champ = { eau: 'eauSalee', basfond: 'basFond' }[cle] as 'eauSalee' | 'basFond' | undefined;
  if (champ && ['oui', 'non', 'ne_sait_pas'].includes(reponse)) {
    profil.ecrire({ [champ]: reponse as OuiNon });
    if (profil.lire().position) await plan(s);
    else sansPosition(s);
    return;
  }
  if (donnee === 'changer_culture') {
    choisirCulture(s);
    return;
  }
  if (donnee === 'langue:wo' || donnee === 'langue:fr') {
    profil.ecrire({ langue: reponse as 'wo' | 'fr' });
    dire(s, 'accueil');
    s.envoyer(ACCUEIL);
    return;
  }
  if (cle === 'culture' && CULTURES.some(([k]) => k === reponse)) {
    profil.ecrire({ culture: reponse, attendDate: true, dateLibre: false, dateRepiquage: undefined });
    dire(s, 'date_repiquage');
    s.envoyer(
      `C'est noté : ${echapper(libelleCulture(reponse).toLowerCase())}.\n\n` +
      '<b>Une dernière question pour bien te conseiller</b>\nTu l\'as plantée quand ? ' +
      'Écris-moi le jour comme ça : <b>15/10</b> pour le 15 octobre. ' +
      'Si tu ne t\'en souviens plus, écris juste : <b>je ne sais pas</b>.',
    );
  }
}

async function message(s: Sortie, brut: string) {
  let texte = brut.trim();
  for (const [bouton, numero] of Object.entries(NUMEROS)) { // bouton numéroté (wolof) ou numéro écrit → même action
    if (texte === `${numero}. ${bouton}` || texte === String(numero)) texte = bouton;
  }
  const p = profil.lire();
  if (texte.startsWith('/oublier')) {
    profil.oublier();
    s.envoyer("C'est fait : j'ai oublié ta langue, ton champ, ta culture et nos derniers échanges. Écris /start pour recommencer.");
    return;
  }
  if (texte.startsWith('/start') || texte.startsWith('/langue') || (!p.langue && !p.attendDate)) {
    poserLangue(s);
    return;
  }
  if (texte === B_POSITION_TEST && AVEC_POSITION_TEST) {
    profil.ecrire({ position: { lat: POSITION_TEST.lat, lon: POSITION_TEST.lon, nom: `${POSITION_TEST.nom} (test)` } });
    dire(s, 'position_recue');
    s.envoyer(
      `Position test : ${POSITION_TEST.nom}, dans la zone pilote des Niayes. ` +
      `C'est un bouton de démonstration ; pour ton vrai champ, utilise « ${B_POSITION} ».`,
    );
    await plan(s);
    return;
  }
  if (texte === '/aide') {
    dire(s, 'accueil');
    s.envoyer(ACCUEIL + "\n\n<i>Pour changer de langue, écris /langue. Pour que j'oublie tout ce que tu m'as dit, écris /oublier.</i>");
    return;
  }
  if (texte === B_QUESTION) {
    dire(s, 'invite_question');
    s.envoyer("Je t'écoute. Pose-moi ta question par écrit (en français), ou envoie-moi un message vocal en wolof.");
    return;
  }
  if (texte === B_PHOTO) {
    dire(s, 'conseils_photo');
    s.envoyer(
      "<b>Envoie-moi une photo de ta plante, là où quelque chose t'inquiète.</b>\n" +
      'Touche le petit bouton rond tout à gauche de la case « Message », juste au-dessus des grands boutons. ' +
      'Choisis ensuite « Appareil photo » pour prendre la photo maintenant, ou une photo déjà prise dans ta galerie.\n\n' +
      '<b>Pour une photo bien lisible</b>\n' + CONSEILS_PHOTO,
    );
    return;
  }
  if (texte === B_PLAN) {
    if (p.position) await plan(s);
    else {
      dire(s, 'demande_position');
      s.envoyer('Je peux te dire quoi planter ce mois-ci, selon le sol de ton champ. ' + DEMANDE_POSITION);
    }
    return;
  }
  if (texte === B_ALERTES) {
    if (!p.position) {
      dire(s, 'demande_position');
      s.envoyer('Je peux surveiller ta culture avec la météo de ton champ. ' + DEMANDE_POSITION);
    } else if (p.culture && !p.attendDate) await alertes(s);
    else choisirCulture(s);
    return;
  }
  if (p.attendDate && /^((je )?ne sais (pas|plus)|xamu ?ma|xamu ?ma ko)\s*[.!]?$/.test(texte.toLowerCase())) {
    profil.ecrire({ dateRepiquage: null, attendDate: false });
    dire(s, 'date_ignoree');
    s.envoyer('Pas de souci, je fais sans la date.');
    if (p.position) await alertes(s);
    else sansPosition(s);
    return;
  }
  const m = texte.match(/^(\d{1,2})[/.\- ](\d{1,2})$/);
  if ((p.attendDate || p.dateLibre) && p.culture && m) {
    const auj = new Date();
    const jour = Number(m[1]);
    const mois = Number(m[2]);
    const annee = auj.getFullYear() - (mois > auj.getMonth() + 1 ? 1 : 0);
    const date = new Date(annee, mois - 1, jour);
    if (mois < 1 || mois > 12 || date.getDate() !== jour) {
      dire(s, 'date_incomprise');
      s.envoyer("Je n'ai pas compris la date. Écris-la comme ceci : <b>15/10</b> pour le 15 octobre.");
      return;
    }
    if (date > auj) {
      dire(s, 'date_future');
      s.envoyer("Cette date n'est pas encore arrivée. Écris le jour où tu as planté, par exemple <b>15/10</b> pour le 15 octobre.");
      return;
    }
    const iso = `${annee}-${String(mois).padStart(2, '0')}-${String(jour).padStart(2, '0')}`;
    profil.ecrire({ dateRepiquage: iso, attendDate: false, dateLibre: false });
    if (p.position) await alertes(s);
    else sansPosition(s);
    return;
  }
  if (texte) await question(s, texte);
}

/** Traite un message de l'agriculteur, comme traiter() du bot. Une erreur imprévue ne le laisse jamais sans réponse. */
export async function traiter(e: Entree, s: Sortie) {
  try {
    if ('action' in e) await action(s, e.action);
    else if ('position' in e) {
      profil.ecrire({ position: e.position });
      dire(s, 'position_recue');
      s.envoyer("C'est bon, j'ai bien reçu la position de ton champ.");
      await plan(s);
    } else if ('photo' in e) await photo(s, e.photo.uri, e.photo.type);
    else if ('vocal' in e) await vocal(s, e.vocal.uri, e.vocal.duree);
    else await message(s, e.texte);
  } catch (err) {
    s.envoyer(err instanceof ErreurReseau ? err.message : 'Désolé, un problème m\'a empêché de répondre. Réessaie dans un instant.');
  }
}

/** Ce qui s'affiche dans la bulle de l'agriculteur quand il touche un bouton sous un message. */
export function libelleAction(boutons: BoutonEnLigne[][] | undefined, actionChoisie: string) {
  return boutons?.flat().find((b) => b.action === actionChoisie)?.texte ?? actionChoisie;
}
