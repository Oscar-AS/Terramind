// Client du moteur TerraMind (contrat : docs/api.md). Adresse : EXPO_PUBLIC_ENGINE_URL
// (fichier .env.local, ex. http://192.168.1.20:8000 pour un téléphone sur le même wifi).
import { profil } from '@/profil';

export const ENGINE_URL = (process.env.EXPO_PUBLIC_ENGINE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export type Statut = 'ok' | 'incertain' | 'je_ne_sais_pas' | 'culture_requise' | 'erreur';
export type Source = { document: string; page: string };
export type Reponse<T> = {
  statut: Statut;
  mock: boolean;
  message: { texte: string; texte_fr: string; audio_url: string | null };
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
};
export type Plan = {
  sol: { texture: string | null; sable_pct: number | null; argile_pct: number | null; ph: number | null };
  cultures: CulturePlan[];
};
export type Alerte = {
  id: string;
  risque: string;
  niveau: 'aucun' | 'surveiller' | 'favorable';
  conseil: string | null;
};
export type Alertes = { alertes: Alerte[]; meteo: { source: string; periode: [string, string] } };
export type Prediction = { culture: string; etiquette: string; categorie: string; libelle: string; confiance: number };
export type Diagnostic = {
  predictions: Prediction[];
  seuil_incertain: number;
  explication?: { fiche: string; texte: string } | null;
  conseils?: { fiche: string; titre: string; texte: string } | null;
};

export class ErreurReseau extends Error {}

function commun() {
  const p = profil.lire();
  // Le texte wolof et la voix ne sont pas encore branchés côté moteur : il répond en français.
  return { utilisateur: p.id, canal: 'mobile', langue: p.langue ?? 'fr' };
}

async function appeler<T>(chemin: string, init: RequestInit): Promise<Reponse<T>> {
  let r: Response;
  try {
    r = await fetch(`${ENGINE_URL}${chemin}`, init);
  } catch {
    throw new ErreurReseau('Pas de connexion avec TerraMind. Vérifie ton réseau.');
  }
  const corps = await r.json().catch(() => null);
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

export function envoyerRetour(alerteId: string, vu: 'oui' | 'non') {
  return appeler<{ enregistre: boolean }>('/v1/feedback', json({ alerte_id: alerteId, vu }));
}

export function poserQuestion(texte: string) {
  return appeler<{ passages: unknown[] }>('/v1/chat', json({ texte }));
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
  const culture = profil.lire().culture;
  if (culture) form.append('culture', culture);
  Object.entries(c).forEach(([k, v]) => form.append(k, v));
  return appeler<Diagnostic>('/v1/diagnose', { method: 'POST', body: form });
}
