import type { ReactNode } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { couleurs, polices, tailles } from '@/theme';

type Props = {
  visible: boolean;
  onFermer: () => void;
  titre: string;
  children: ReactNode;
};

/**
 * Feuille qui monte du bas de l'écran (comme chez Wolt) : on garde l'écran
 * d'origine en arrière-plan au lieu d'ouvrir une nouvelle page.
 * Modal intégrée à React Native : aucune bibliothèque en plus.
 */
export function FeuilleGlissante({ visible, onFermer, titre, children }: Props) {
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onFermer}>
      <View style={styles.fond}>
        <Pressable style={styles.zoneFermer} onPress={onFermer} accessibilityLabel="Fermer" />
        <SafeAreaView edges={['bottom']} style={styles.feuille}>
          <View style={styles.poignee} />
          <View style={styles.entete}>
            <Text style={styles.titre}>{titre}</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Fermer"
              onPress={onFermer}
              style={styles.fermer}>
              <Text style={styles.fermerTexte}>✕</Text>
            </Pressable>
          </View>
          <View style={styles.contenu}>{children}</View>
        </SafeAreaView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  fond: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' },
  zoneFermer: { flex: 1 },
  feuille: {
    backgroundColor: couleurs.sable,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: tailles.marge,
    paddingBottom: tailles.marge,
    minHeight: '55%',
  },
  poignee: {
    alignSelf: 'center',
    width: 48,
    height: 5,
    borderRadius: 3,
    backgroundColor: couleurs.encreDouce,
    opacity: 0.4,
    marginVertical: 10,
  },
  entete: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  titre: { flex: 1, fontSize: 24, fontFamily: polices.titre, color: couleurs.encre },
  fermer: {
    width: tailles.boutonMin,
    height: tailles.boutonMin,
    borderRadius: tailles.boutonMin / 2,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: couleurs.carte, borderWidth: 1, borderColor: couleurs.trait,
  },
  fermerTexte: { fontSize: 24, color: couleurs.encre },
  contenu: { gap: 16 },
});
