import { router } from 'expo-router';
import { ArrowLeft } from 'phosphor-react-native/src/icons/ArrowLeft';
import { SpeakerHigh } from 'phosphor-react-native/src/icons/SpeakerHigh';
import { Stop } from 'phosphor-react-native/src/icons/Stop';
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { PhraseWolof } from '@/api';
import { Etapes } from '@/components/Etapes';
import { T } from '@/components/ui';
import { LecteurVoix, useLecteur } from '@/components/Voix';
import { couleurs, tailles } from '@/theme';

type Props = {
  titre: string;
  /** Bouton retour, sauf pendant la première ouverture et sur l'accueil. */
  avecRetour?: boolean;
  etape?: { actuelle: number; total: number };
  /** Notes vocales wolof de l'écran : le bouton Écouter n'apparaît que s'il y en a. */
  voix?: PhraseWolof[];
  children: ReactNode;
};

function BoutonRond({ libelle, onPress, children }: { libelle: string; onPress?: () => void; children: ReactNode }) {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={libelle} onPress={onPress} hitSlop={8}
      style={({ pressed }) => [styles.rond, pressed && { backgroundColor: couleurs.sableFonce }]}>
      {children}
    </Pressable>
  );
}

/** Bouton Écouter de l'en-tête : lit (ou arrête) les notes vocales wolof de l'écran. */
function EcouterEcran({ voix }: { voix?: PhraseWolof[] }) {
  const { jouer, arreter, enCours } = useLecteur();
  if (!voix?.some((p) => p.audio_url)) return <View style={styles.vide} />;
  const actif = enCours === voix;
  return (
    <BoutonRond libelle={actif ? 'Arrêter' : 'Écouter en wolof'} onPress={() => (actif ? arreter() : jouer(voix))}>
      {actif ? <Stop size={24} color={couleurs.terre} weight="fill" /> : <SpeakerHigh size={26} color={couleurs.foret} weight="duotone" />}
    </BoutonRond>
  );
}

/** Cadre commun : retour, titre, bouton Écouter (notes vocales wolof, s'il y en a). */
export function Ecran({ titre, avecRetour = true, etape, voix, children }: Props) {
  return (
    <LecteurVoix>
    <SafeAreaView style={styles.page}>
      <View style={styles.entete}>
        {avecRetour ? (
          <BoutonRond libelle="Retour" onPress={() => (router.canGoBack() ? router.back() : router.replace('/accueil'))}>
            <ArrowLeft size={26} color={couleurs.encre} weight="bold" />
          </BoutonRond>
        ) : <View style={styles.vide} />}
        {etape ? <Etapes actuelle={etape.actuelle} total={etape.total} /> : <View style={{ flex: 1 }} />}
        <EcouterEcran voix={voix} />
      </View>
      <ScrollView contentContainerStyle={styles.contenu} showsVerticalScrollIndicator={false}>
        <T v="titre" accessibilityRole="header">{titre}</T>
        {children}
      </ScrollView>
    </SafeAreaView>
    </LecteurVoix>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: couleurs.sable },
  entete: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: tailles.marge, paddingTop: 8, gap: 12 },
  rond: {
    width: 52, height: 52, borderRadius: 26, alignItems: 'center', justifyContent: 'center',
    backgroundColor: couleurs.carte, borderWidth: 1, borderColor: couleurs.trait,
  },
  vide: { width: 52 },
  contenu: { padding: tailles.marge, paddingTop: 16, gap: 16, flexGrow: 1, paddingBottom: 40 },
});
