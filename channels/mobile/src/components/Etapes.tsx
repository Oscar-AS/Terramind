import { StyleSheet, View } from 'react-native';

import { couleurs } from '@/theme';

/** Points d'étape (● ● ○) : montrent la progression sans texte. */
export function Etapes({ actuelle, total }: { actuelle: number; total: number }) {
  return (
    <View
      style={styles.ligne}
      accessible
      accessibilityLabel={`Étape ${actuelle} sur ${total}`}>
      {Array.from({ length: total }, (_, i) => (
        <View
          key={i}
          style={[styles.point, i < actuelle ? styles.fait : styles.aFaire, i === actuelle - 1 && styles.actuel]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  ligne: { flexDirection: 'row', justifyContent: 'center', gap: 10, paddingBottom: 4 },
  point: { width: 14, height: 14, borderRadius: 7 },
  fait: { backgroundColor: couleurs.vert },
  aFaire: { backgroundColor: couleurs.vertClair },
  actuel: { width: 32 },
});
