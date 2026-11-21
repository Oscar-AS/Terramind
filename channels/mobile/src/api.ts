// Client du moteur TerraMind (contrat : docs/api.md). Adresse : EXPO_PUBLIC_ENGINE_URL
// (fichier .env.local, ex. http://192.168.1.20:8000 pour un téléphone sur le même wifi).
import { profil } from '@/profil';

export const ENGINE_URL = (process.env.EXPO_PUBLIC_ENGINE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export type Statut = 'ok' | 'incertain' | 'je_ne_sais_pas' | 'culture_requise' | 'erreur';
export type Source = { document: string; page: string };
/** Phrase wolof relue par un locuteur, avec sa note vocale (adresse relative au moteur). */
export type PhraseWolof = { cle: string; texte_wo: string; texte_fr: string; audio_url: string | null };
export type Reponse<T> = {
  statut: Statut;
  mock: boolean;
  langue: 'fr' | 'wo';
  /** En wolof : `texte` est le wolof, `texte_fr` le français, `wolof` les phrases avec leurs notes vocales. */
  message: { texte: string; texte_fr: string; audio_url: string | null; wolof?: PhraseWolof[] };
  sources: Source[];
  donnees: T;
};

export type Adaptation = 'conseillee' | 'possible' | 'deconseillee';
export type CulturePlan = {
  culture: string;
  libelle: string;
  adaptation: Adaptation;
  periode_semis: string;
  cycle_jours: [number, number];
  raisons: string[];
  avertissements: string[];
  wo?: PhraseWolof | null;
};
export type Plan = {
  sol: { texture: string | null; sable_pct: number | null; argile_pct: number | null; ph: number | null; ph_mots?: string | null };
  cultures: CulturePlan[];
};
export type Alerte = {
  id: string;
  risque: string;
  niveau: 'aucun' | 'surveiller' | 'favorable' | 'date_requise';
  conseil: string | null;
  wo?: PhraseWolof | null;
};
export type Alertes = { alertes: Alerte[]; meteo: { source: string; periode: [string, string] } };
export type Prediction = { culture: string; etiquette: string; categorie: string; libelle: string; confiance: number };
export type Diagnostic = {
  predictions: Prediction[];
  seuil_incertain: number;
  /** Fiche en 4 parties : ce que c'est, pourquoi, que faire maintenant, pour que ça ne revienne pas. */
  fiche?: {
    fiche: string;
    titre: string;
    ce_que_c_est: string | null;
    pourquoi: string | null;
    que_faire: string | null;
    eviter: string | null;
  } | null;
  /** Ravageurs que la photo ne reconnaît pas (mineuse de la tomate) : question oui/non tirée de la fiche. */
  questions_suivi?: { question: string; si_oui: string; fiche: string }[];
};

export class ErreurReseau extends Error {}

function commun() {
  const p = profil.lire();
  // En wolof, le moteur ajoute les phrases relues et leurs notes vocales (plan, alertes, diagnostic).
  return { utilisateur: p.id, canal: 'mobile', langue: p.langue ?? 'fr' };
}

// Le serveur gratuit (Render) se met en veille : le premier appel le réveille en une minute environ.
// Au-delà de 90 secondes, on arrête d'attendre au lieu de laisser tourner le chargement sans fin.
const DELAI_MS = 90_000;

async function appeler<T>(chemin: string, init: RequestInit): Promise<Reponse<T>> {
  const arret = new AbortController();
  const minuterie = setTimeout(() => arret.abort(), DELAI_MS);
  let r: Response;
  try {
    r = await fetch(`${ENGINE_URL}${chemin}`, { ...init, signal: arret.signal });
  } catch {
    throw new ErreurReseau(arret.signal.aborted
      ? 'TerraMind met trop de temps à répondre. Réessaie dans une minute.'
      : 'Pas de connexion avec TerraMind. Vérifie ton réseau.');
  } finally {
    clearTimeout(minuterie);
  }
  const corps = await r.json().catch(() => null);
  if (r.status === 422) throw new ErreurReseau('Ta demande est trop longue ou incomplète. Raccourcis-la et réessaie.');
  if (!corps?.message) throw new ErreurReseau('Le service ne répond pas correctement. Réessaie plus tard.');
  return corps as Reponse<T>;
}

const json = (corps: object): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ...commun(), ...corps }),
});

export function demanderPlan() {
  const p = profil.lire();
  return appeler<Plan>('/v1/plan', json({
    lat: p.position?.lat, lon: p.position?.lon,
    eau_puits_salee: p.eauSalee ?? 'ne_sait_pas', champ_en_bas_fond: p.basFond ?? 'ne_sait_pas',
  }));
}

export function demanderAlertes() {
  const p = profil.lire();
  return appeler<Alertes>('/v1/alert', json({
    lat: p.position?.lat, lon: p.position?.lon, culture: p.culture, date_repiquage: p.dateRepiquage,
  }));
}

export function poserQuestion(texte: string) {
  return appeler<{ passages: unknown[] }>('/v1/chat', json({ texte }));
}

/** Question dite en wolof : ce que le moteur a compris, et sa réponse dite en wolof (si la voix a pu être faite). */
export type Vocal = {
  transcription: { wolof: string; francais: string | null } | null;
  voix: PhraseWolof | null;
};

export async function poserQuestionVocale(uri: string, dureeSecondes: number) {
  const form = new FormData();
  if (uri.startsWith('blob:') || uri.startsWith('data:')) {
    // Web : l'enregistrement du navigateur (souvent audio/webm).
    const audio = await (await fetch(uri)).blob();
    form.append('audio', audio, audio.type.includes('webm') ? 'question.webm' : 'question.m4a');
  } else {
    // Android / iOS : fichier .m4a écrit par expo-audio.
    form.append('audio', { uri, name: 'question.m4a', type: 'audio/mp4' } as unknown as Blob);
  }
  // La question est dite en wolof : la réponse revient aussi en wolof, à écouter.
  Object.entries({ ...commun(), langue: 'wo' }).forEach(([k, v]) => form.append(k, v));
  form.append('duree', String(Math.round(dureeSecondes)));
  return appeler<Vocal>('/v1/chat/vocal', { method: 'POST', body: form });
}

export async function diagnostiquer(uri: string, mimeType: string | null) {
  const c = commun();
  const form = new FormData();
  if (uri.startsWith('blob:') || uri.startsWith('data:')) {
    // Web : l'image est un blob du navigateur.
    form.append('photo', await (await fetch(uri)).blob(), 'feuille.jpg');
  } else {
    // Android / iOS : React Native lit le fichier à partir de son adresse.
    form.append('photo', { uri, name: 'feuille.jpg', type: mimeType ?? 'image/jpeg' } as unknown as Blob);
  }
  // Pas de culture envoyée : la feuille peut venir d'une autre culture que celle surveillée.
  Object.entries(c).forEach(([k, v]) => form.append(k, v));
  return appeler<Diagnostic>('/v1/diagnose', { method: 'POST', body: form });
}
