import { StyleSheet, View } from 'react-native';

import { couleurs } from '@/theme';

/** Barre d'étapes : montre la progression sans texte. */
export function Etapes({ actuelle, total }: { actuelle: number; total: number }) {
  return (
    <View style={styles.ligne} accessible accessibilityLabel={`Étape ${actuelle} sur ${total}`}>
      {Array.from({ length: total }, (_, i) => (
        <View key={i} style={[styles.trait, { backgroundColor: i < actuelle ? couleurs.feuille : couleurs.sableFonce }]} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  ligne: { flex: 1, flexDirection: 'row', gap: 6 },
  trait: { flex: 1, height: 6, borderRadius: 3 },
});
