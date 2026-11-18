import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { ArrowRight } from 'phosphor-react-native/src/icons/ArrowRight';
import { SpeakerHigh } from 'phosphor-react-native/src/icons/SpeakerHigh';
import { Stop } from 'phosphor-react-native/src/icons/Stop';
import { ImageBackground, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { PhraseWolof } from '@/api';
import { LecteurVoix, useLecteur } from '@/components/Voix';
import { couleurs, polices, tailles } from '@/theme';

// Note bilingue relue (comme le message de départ du bot) : une phrase en français, puis en wolof,
// qui explique comment choisir sa langue à l'écran suivant. Servie par le moteur.
const VOIX_ACCUEIL: PhraseWolof[] = [{ cle: 'choix_langue', texte_wo: '', texte_fr: '', audio_url: '/audio/wo/choix_langue.mp3' }];

function Ecouter() {
  const { jouer, arreter, enCours } = useLecteur();
  const actif = enCours === VOIX_ACCUEIL;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={actif ? 'Arrêter' : 'Écouter'}
      onPress={() => (actif ? arreter() : jouer(VOIX_ACCUEIL))}
      style={styles.ecouter}>
      {actif ? <Stop size={30} color={couleurs.blanc} weight="fill" /> : <SpeakerHigh size={32} color={couleurs.blanc} weight="duotone" />}
    </Pressable>
  );
}

// Écran de bienvenue plein écran (inspiré de Wolt et de PictureThis 01).
// Photo générée par IA, décorative : voir assets/illustrations/CREDITS.md.
const PHOTO = require('../../../assets/illustrations/bienvenue.jpg');

export default function Bienvenue() {
  return (
    <LecteurVoix>
    <ImageBackground source={PHOTO} resizeMode="cover" style={styles.page} accessible={false}>
      {/* Dégradé vert en bas : garde le nom et le bouton lisibles sur la photo. */}
      <LinearGradient
        colors={['rgba(31,77,58,0)', 'rgba(31,77,58,0.88)', couleurs.foret]}
        locations={[0, 0.45, 1]}
        style={styles.degrade}
      />
      <SafeAreaView style={styles.contenu}>
        <View style={styles.bas}>
          <Text style={styles.nom}>TerraMind</Text>
          <Text style={styles.promesse}>Prends ta plante en photo, on te dit quoi faire.</Text>
          <View style={styles.boutons}>
            <Ecouter />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Commencer"
              onPress={() => router.push('/bienvenue/langue')}
              style={({ pressed }) => [styles.commencer, pressed && { opacity: 0.85 }]}>
              <Text style={styles.commencerTexte}>Commencer</Text>
              <ArrowRight size={24} color={couleurs.foret} weight="bold" />
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    </ImageBackground>
    </LecteurVoix>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: couleurs.foret },
  degrade: { position: 'absolute', left: 0, right: 0, bottom: 0, height: '50%' },
  contenu: { flex: 1, justifyContent: 'flex-end' },
  bas: { padding: tailles.marge * 1.5, gap: 12 },
  nom: { fontSize: 44, fontFamily: polices.titre, color: couleurs.blanc, letterSpacing: -1 },
  promesse: { fontSize: 21, lineHeight: 29, fontFamily: polices.texte, color: couleurs.blanc },
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
    backgroundColor: couleurs.carte,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  commencerTexte: { fontSize: 21, fontFamily: polices.texteGras, color: couleurs.foret },
});
