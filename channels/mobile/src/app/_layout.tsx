import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function Racine() {
  return (
    <>
      <StatusBar style="dark" />
      {/* Pas d'en-tête natif : chaque écran a son propre cadre (components/Ecran). */}
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }} />
    </>
  );
}
