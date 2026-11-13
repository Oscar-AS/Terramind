import { Pressable, StyleSheet, Text } from 'react-native';

import { couleurs, tailles } from '@/theme';

type Props = {
  icone: string;
  libelle: string;
  onPress?: () => void;
  variante?: 'plein' | 'clair';
};

/** Grand bouton : une icône, un mot, un seul toucher. */
export function GrosBouton({ icone, libelle, onPress, variante = 'plein' }: Props) {
  const plein = variante === 'plein';
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={libelle}
      onPress={onPress}
      style={({ pressed }) => [
        styles.bouton,
        { backgroundColor: plein ? couleurs.vert : couleurs.vertClair },
        pressed && styles.appuye,
      ]}>
      <Text style={styles.icone}>{icone}</Text>
      <Text style={[styles.libelle, { color: plein ? couleurs.blanc : couleurs.texte }]}>
        {libelle}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bouton: {
    minHeight: tailles.boutonMin * 1.5,
    borderRadius: tailles.rayon,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    gap: 16,
  },
  appuye: { opacity: 0.8, transform: [{ scale: 0.98 }] },
  icone: { fontSize: 36 },
  libelle: { fontSize: 22, fontWeight: '700', flexShrink: 1 },
});
