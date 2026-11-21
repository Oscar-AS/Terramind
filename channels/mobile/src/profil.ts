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
  dateRepiquage?: string | null; // AAAA-MM-JJ ; null : l'agriculteur ne s'en souvient pas
  attendDate?: boolean; // la conversation attend la date de plantation (comme le bot)
  dateLibre?: boolean; // la date peut être écrite à n'importe quel moment
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
  /** /oublier : langue, champ, culture et conversation effacés ; un nouvel identifiant anonyme. */
  oublier() {
    globalThis.localStorage?.removeItem(CLE);
    globalThis.localStorage?.removeItem(CLE_CONVERSATION);
  },
};

// La conversation est gardée sur le téléphone (les 150 derniers messages), comme l'historique d'une messagerie.
const CLE_CONVERSATION = 'terramind.conversation';
export const conversationGardee = {
  lire<T>(): T[] {
    try {
      return JSON.parse(globalThis.localStorage?.getItem(CLE_CONVERSATION) ?? '[]') as T[];
    } catch {
      return [];
    }
  },
  ecrire<T>(messages: T[]) {
    globalThis.localStorage?.setItem(CLE_CONVERSATION, JSON.stringify(messages.slice(-150)));
  },
};
