import { StyleSheet, Text, View } from 'react-native';

import { couleurs, tailles } from '@/theme';

/**
 * Encadré « à construire » : indique ce que l'écran fera, sans afficher de
 * fausses données (règle du concours : rien de factice).
 */
export function AVenir({ texte, api }: { texte: string; api?: string }) {
  return (
    <View style={styles.boite}>
      <Text style={styles.etiquette}>À construire</Text>
      <Text style={styles.texte}>{texte}</Text>
      {api ? <Text style={styles.api}>Moteur : {api}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  boite: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: couleurs.ocre,
    borderRadius: tailles.rayon,
    padding: 16,
    gap: 6,
  },
  etiquette: { color: couleurs.ocre, fontWeight: '700', fontSize: 14 },
  texte: { color: couleurs.texte, fontSize: tailles.corps },
  api: { color: couleurs.texteDoux, fontSize: 14, fontFamily: 'monospace' },
});
