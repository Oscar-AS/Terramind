import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { ImageBackground, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { couleurs, tailles } from '@/theme';

// Écran de bienvenue plein écran (inspiré de Wolt et de PictureThis 01).
// Photo générée par IA, décorative : voir assets/illustrations/CREDITS.md.
const PHOTO = require('../../../assets/illustrations/bienvenue.jpg');

export default function Bienvenue() {
  return (
    <ImageBackground source={PHOTO} resizeMode="cover" style={styles.page} accessible={false}>
      {/* Dégradé vert en bas : garde le nom et le bouton lisibles sur la photo. */}
      <LinearGradient
        colors={['rgba(63,143,95,0)', 'rgba(63,143,95,0.85)', couleurs.vert]}
        locations={[0, 0.45, 1]}
        style={styles.degrade}
      />
      <SafeAreaView style={styles.contenu}>
        <View style={styles.bas}>
          <Text style={styles.nom}>TerraMind</Text>
          {/* Phrase dite à voix haute en wolof au lancement (voix à brancher). */}
          <Text style={styles.promesse}>Prends ta plante en photo, on te dit quoi faire.</Text>
          <View style={styles.boutons}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Écouter"
              style={styles.ecouter}>
              <Text style={styles.ecouterTexte}>🔊</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Commencer"
              onPress={() => router.push('/bienvenue/langue')}
              style={({ pressed }) => [styles.commencer, pressed && { opacity: 0.85 }]}>
              <Text style={styles.commencerTexte}>Commencer ➜</Text>
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: couleurs.vert },
  degrade: { position: 'absolute', left: 0, right: 0, bottom: 0, height: '50%' },
  contenu: { flex: 1, justifyContent: 'flex-end' },
  bas: { padding: tailles.marge * 1.5, gap: 12 },
  nom: { fontSize: 40, fontWeight: '800', color: couleurs.blanc },
  promesse: { fontSize: 22, color: couleurs.blanc },
  boutons: { flexDirection: 'row', gap: 12, marginTop: 12 },
  ecouter: {
    width: tailles.boutonMin * 1.2,
    height: tailles.boutonMin * 1.2,
    borderRadius: tailles.rayon,
    backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  ecouterTexte: { fontSize: 32 },
  commencer: {
    flex: 1,
    borderRadius: tailles.rayon,
    backgroundColor: couleurs.blanc,
    alignItems: 'center',
    justifyContent: 'center',
  },
  commencerTexte: { fontSize: 22, fontWeight: '700', color: couleurs.vert },
});
