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
  /** Remplace tout le profil (passage d'une conversation à une autre : chacune garde son champ, sa culture…). */
  remplacer(p: Profil): Profil {
    globalThis.localStorage?.setItem(CLE, JSON.stringify(p));
    return p;
  },
  /** /oublier : langue, champ, culture et toutes les conversations effacés ; un nouvel identifiant anonyme. */
  oublier() {
    for (const c of conversations.lister()) globalThis.localStorage?.removeItem(CLE_MESSAGES + c.id);
    globalThis.localStorage?.removeItem(CLE_LISTE);
    globalThis.localStorage?.removeItem(CLE_ANCIENNE);
    globalThis.localStorage?.removeItem(CLE);
  },
};

// Plusieurs conversations, comme dans une messagerie : la liste (titre, date, ce que l'agriculteur avait indiqué
// dans cette conversation) et, pour chacune, ses 150 derniers messages. Tout reste sur le téléphone.
export type Conversation = { id: string; titre: string; maj: number; profil: Omit<Profil, 'id'> };
const CLE_LISTE = 'terramind.conversations';
const CLE_MESSAGES = 'terramind.conversation.';
const CLE_ANCIENNE = 'terramind.conversation'; // une seule conversation (avant le 21 nov) : reprise comme la première

function lireJson<T>(cle: string, defaut: T): T {
  try {
    const brut = globalThis.localStorage?.getItem(cle);
    return brut ? (JSON.parse(brut) as T) : defaut;
  } catch {
    return defaut;
  }
}

export const conversations = {
  lister(): Conversation[] {
    const liste = lireJson<Conversation[]>(CLE_LISTE, []);
    const ancienne = globalThis.localStorage?.getItem(CLE_ANCIENNE);
    if (!liste.length && ancienne) {
      const { id: _id, ...reste } = profil.lire();
      const c = { id: nouvelId(), titre: '', maj: Date.now(), profil: reste };
      globalThis.localStorage?.setItem(CLE_MESSAGES + c.id, ancienne);
      globalThis.localStorage?.removeItem(CLE_ANCIENNE);
      conversations.enregistrer([c]);
      return [c];
    }
    return liste;
  },
  enregistrer(liste: Conversation[]) {
    globalThis.localStorage?.setItem(CLE_LISTE, JSON.stringify(liste));
  },
  messages<T>(id: string): T[] {
    return lireJson<T[]>(CLE_MESSAGES + id, []);
  },
  ecrireMessages<T>(id: string, messages: T[]) {
    globalThis.localStorage?.setItem(CLE_MESSAGES + id, JSON.stringify(messages.slice(-150)));
  },
  nouvelId,
};
