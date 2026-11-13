import { BricolageGrotesque_700Bold, BricolageGrotesque_800ExtraBold } from '@expo-google-fonts/bricolage-grotesque';
import { Figtree_500Medium, Figtree_700Bold, useFonts } from '@expo-google-fonts/figtree';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';

import { couleurs } from '@/theme';

export default function Racine() {
  const [chargees] = useFonts({
    BricolageGrotesque_700Bold, BricolageGrotesque_800ExtraBold, Figtree_500Medium, Figtree_700Bold,
  });
  // Fond sable pendant le chargement des polices (une fraction de seconde), pas d'écran blanc.
  if (!chargees) return <View style={{ flex: 1, backgroundColor: couleurs.sable }} />;
  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right', contentStyle: { backgroundColor: couleurs.sable } }} />
    </>
  );
}
