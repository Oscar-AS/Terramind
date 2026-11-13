import { router } from 'expo-router';
import { ArrowLeft, SpeakerHigh } from 'phosphor-react-native';
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Etapes } from '@/components/Etapes';
import { T } from '@/components/ui';
import { couleurs, tailles } from '@/theme';

type Props = {
  titre: string;
  /** Bouton retour, sauf pendant la première ouverture et sur l'accueil. */
  avecRetour?: boolean;
  etape?: { actuelle: number; total: number };
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

/** Cadre commun : retour, titre, bouton Écouter (lecture vocale, branchée plus tard sur la voix wolof). */
export function Ecran({ titre, avecRetour = true, etape, children }: Props) {
  return (
    <SafeAreaView style={styles.page}>
      <View style={styles.entete}>
        {avecRetour ? (
          <BoutonRond libelle="Retour" onPress={() => (router.canGoBack() ? router.back() : router.replace('/accueil'))}>
            <ArrowLeft size={26} color={couleurs.encre} weight="bold" />
          </BoutonRond>
        ) : <View style={styles.vide} />}
        {etape ? <Etapes actuelle={etape.actuelle} total={etape.total} /> : <View style={{ flex: 1 }} />}
        <BoutonRond libelle="Écouter">
          <SpeakerHigh size={26} color={couleurs.foret} weight="duotone" />
        </BoutonRond>
      </View>
      <ScrollView contentContainerStyle={styles.contenu} showsVerticalScrollIndicator={false}>
        <T v="titre" accessibilityRole="header">{titre}</T>
        {children}
      </ScrollView>
    </SafeAreaView>
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
