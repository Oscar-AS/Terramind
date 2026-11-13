// Ce que l'agriculteur a indiqué, gardé sur le téléphone seulement (localStorage : navigateur
// sur le web, SQLite sur Android/iOS via expo-sqlite). Aucun compte, aucun numéro.
import 'expo-sqlite/localStorage/install';

export type OuiNon = 'oui' | 'non' | 'ne_sait_pas';
export type Profil = {
  id: string;
  langue?: 'fr' | 'wo';
  position?: { lat: number; lon: number; nom?: string };
  eauSalee?: OuiNon;
  basFond?: OuiNon;
  culture?: string;
  dateRepiquage?: string; // AAAA-MM-JJ
};

const CLE = 'terramind.profil';

function nouvelId() {
  // Identifiant anonyme aléatoire : ne contient rien de personnel.
  return 'm-' + Array.from({ length: 16 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
}

export const profil = {
  lire(): Profil {
    try {
      const brut = globalThis.localStorage?.getItem(CLE);
      if (brut) return JSON.parse(brut) as Profil;
    } catch {
      // profil illisible : on repart de zéro
    }
    const p = { id: nouvelId() };
    globalThis.localStorage?.setItem(CLE, JSON.stringify(p));
    return p;
  },
  ecrire(modif: Partial<Profil>): Profil {
    const p = { ...profil.lire(), ...modif };
    globalThis.localStorage?.setItem(CLE, JSON.stringify(p));
    return p;
  },
  premiereOuvertureFaite(): boolean {
    const p = profil.lire();
    return Boolean(p.langue && p.position);
  },
};

// Zones pilotes (centroïdes des départements, geoBoundaries) pour qui refuse le GPS.
export const ZONES = [
  { nom: 'Rufisque', lat: 14.76, lon: -17.21 },
  { nom: 'Thiès', lat: 14.75, lon: -16.87 },
  { nom: 'Tivaouane', lat: 15.09, lon: -16.65 },
  { nom: 'Kébémer', lat: 15.3, lon: -16.26 },
];

export const CULTURES = [
  { id: 'tomato', libelle: 'Tomate', icone: '🍅' },
  { id: 'onion', libelle: 'Oignon', icone: '🧅' },
  { id: 'cabbage', libelle: 'Chou', icone: '🥬' },
  { id: 'potato', libelle: 'Pomme de terre', icone: '🥔' },
  { id: 'pepper', libelle: 'Poivron', icone: '🫑' },
  { id: 'carrot', libelle: 'Carotte', icone: '🥕' },
];
