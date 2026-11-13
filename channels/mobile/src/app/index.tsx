import { Redirect } from 'expo-router';

// Pour l'instant, on démarre toujours par la première ouverture.
// Plus tard : si la langue et le champ sont déjà enregistrés, aller à l'accueil.
export default function Depart() {
  return <Redirect href="/bienvenue" />;
}
