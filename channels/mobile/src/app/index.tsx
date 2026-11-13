import { Redirect } from 'expo-router';

import { profil } from '@/profil';

// Première ouverture si la langue ou la position manquent ; sinon directement l'accueil.
export default function Depart() {
  return <Redirect href={profil.premiereOuvertureFaite() ? '/accueil' : '/bienvenue'} />;
}
