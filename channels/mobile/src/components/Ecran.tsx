import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Etapes } from '@/components/Etapes';
import { couleurs, tailles } from '@/theme';

type Props = {
  titre: string;
  /** Bouton « accueil » toujours visible, sauf pendant la première ouverture. */
  avecAccueil?: boolean;
  /** Points d'étape, pendant la première ouverture. */
  etape?: { actuelle: number; total: number };
  children: ReactNode;
};

/** Cadre commun à tous les écrans : titre, bouton 🔊, retour à l'accueil. */
export function Ecran({ titre, avecAccueil = true, etape, children }: Props) {
  return (
    <SafeAreaView style={styles.page}>
      {etape ? <Etapes actuelle={etape.actuelle} total={etape.total} /> : null}
      <View style={styles.entete}>
        {avecAccueil ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Retour à l'accueil"
            onPress={() => router.dismissTo('/accueil')}
            style={styles.icone}>
            <Text style={styles.iconeTexte}>🏠</Text>
          </Pressable>
        ) : (
          <View style={styles.icone} />
        )}
        <Text style={styles.titre} numberOfLines={2}>
          {titre}
        </Text>
        {/* Lecture vocale : branchée plus tard sur la voix wolof (docs/voix-wolof.md). */}
        <Pressable accessibilityRole="button" accessibilityLabel="Écouter" style={styles.icone}>
          <Text style={styles.iconeTexte}>🔊</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.contenu}>{children}</ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: couleurs.fond },
  entete: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: tailles.marge,
    paddingVertical: 12,
    gap: 12,
  },
  icone: {
    width: tailles.boutonMin,
    height: tailles.boutonMin,
    borderRadius: tailles.boutonMin / 2,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: couleurs.vertClair,
  },
  iconeTexte: { fontSize: 28 },
  titre: {
    flex: 1,
    fontSize: tailles.titre,
    fontWeight: '700',
    color: couleurs.texte,
    textAlign: 'center',
  },
  contenu: { padding: tailles.marge, gap: 16, flexGrow: 1 },
});
