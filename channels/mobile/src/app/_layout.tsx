import { BricolageGrotesque_700Bold, BricolageGrotesque_800ExtraBold } from '@expo-google-fonts/bricolage-grotesque';
import { Figtree_500Medium, Figtree_700Bold, useFonts } from '@expo-google-fonts/figtree';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Platform, View } from 'react-native';

import { LecteurVoix } from '@/components/Voix';
import { couleurs } from '@/theme';

// Sur ordinateur (version web pour le jury), l'app garde la largeur d'un téléphone, centrée.
const colonneWeb = Platform.OS === 'web'
  ? { width: '100%' as const, maxWidth: 480, alignSelf: 'center' as const, overflow: 'hidden' as const }
  : null;

export default function Racine() {
  const [chargees, erreur] = useFonts({
    BricolageGrotesque_700Bold, BricolageGrotesque_800ExtraBold, Figtree_500Medium, Figtree_700Bold,
  });
  // Fond sable pendant le chargement des polices (une fraction de seconde), pas d'écran blanc.
  // Si une police ne se charge pas, on affiche quand même l'app avec la police du système.
  if (!chargees && !erreur) return <View style={{ flex: 1, backgroundColor: couleurs.sable }} />;
  return (
    <View style={{ flex: 1, backgroundColor: Platform.OS === 'web' ? couleurs.sableFonce : couleurs.sable }}>
      <View style={[{ flex: 1 }, colonneWeb]}>
        <StatusBar style="light" />
        <LecteurVoix>
          <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: couleurs.sable } }} />
        </LecteurVoix>
      </View>
    </View>
  );
}
