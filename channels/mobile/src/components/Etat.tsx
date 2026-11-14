import { ArrowsClockwise, BookOpen, type Icon, WifiSlash } from 'phosphor-react-native';
import { useEffect, useState } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';

import type { Source } from '@/api';
import { Bouton, Carte, T } from '@/components/ui';
import { couleurs } from '@/theme';

/** Attente : l'icône au centre d'un halo qui s'élargit (l'agriculteur voit que ça travaille). */
export function Chargement({ Icone, texte }: { Icone: Icon; texte: string }) {
  const [v] = useState(() => new Animated.Value(0));
  useEffect(() => {
    const boucle = Animated.loop(Animated.timing(v, { toValue: 1, duration: 1400, easing: Easing.out(Easing.quad), useNativeDriver: true }));
    boucle.start();
    return () => boucle.stop();
  }, [v]);
  return (
    <View style={styles.centre} accessibilityLiveRegion="polite">
      <View style={styles.halo}>
        <Animated.View style={[styles.onde, { opacity: v.interpolate({ inputRange: [0, 1], outputRange: [0.45, 0] }),
          transform: [{ scale: v.interpolate({ inputRange: [0, 1], outputRange: [0.8, 1.6] }) }] }]} />
        <View style={styles.coeur}><Icone size={44} color={couleurs.foret} weight="duotone" /></View>
      </View>
      <T v="corpsGras" style={{ textAlign: 'center' }}>{texte}</T>
    </View>
  );
}

/** Erreur claire, avec un seul bouton pour réessayer. */
export function Erreur({ texte, onReessayer }: { texte: string; onReessayer: () => void }) {
  return (
    <View style={styles.centre}>
      <View style={[styles.coeur, { backgroundColor: couleurs.terreClair }]}><WifiSlash size={40} color={couleurs.terre} weight="duotone" /></View>
      <T v="corps" style={{ textAlign: 'center' }}>{texte}</T>
      <View style={{ alignSelf: 'stretch' }}><Bouton libelle="Réessayer" Icone={ArrowsClockwise} onPress={onReessayer} variante="clair" /></View>
    </View>
  );
}

// Notes destinées à l'équipe (chemins de fichiers, archive, script) : retirées pour l'agriculteur.
const TECHNIQUE = /`|\.(md|py|csv)\b|archive|scripts?\//i;

/** Nom d'une source lisible par l'agriculteur : sans les parenthèses techniques ni le code. */
export function nomLisible(document: string): string {
  let nom = document;
  let precedent = '';
  while (nom !== precedent) {
    precedent = nom;
    // parenthèses les plus internes d'abord, pour gérer les parenthèses imbriquées
    nom = nom.replace(/\s*\(([^()]*)\)/g, (tout, dedans: string) => (TECHNIQUE.test(dedans) ? '' : tout));
  }
  return nom.replace(/,?\s*`[^`]*`/g, '').replace(/\s+,/g, ',').trim();
}

/** D'où vient le conseil : toujours montré, discrètement. */
export function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  const lisibles = sources.map((s) => ({ ...s, document: nomLisible(s.document) }));
  const uniques = [...new Map(lisibles.map((s) => [`${s.document} ${s.page}`, s])).values()];
  return (
    <Carte style={styles.sources}>
      <View style={styles.sourcesTete}>
        <BookOpen size={18} color={couleurs.encreDouce} weight="duotone" />
        <T v="etiquette">Sources</T>
      </View>
      {uniques.map((s) => (
        <T key={`${s.document}-${s.page}`} v="petit">
          {s.document}{/^\d/.test(s.page) ? `, p. ${s.page}` : s.page === '—' || TECHNIQUE.test(s.page) ? '' : ` (${s.page})`}
        </T>
      ))}
    </Carte>
  );
}

const styles = StyleSheet.create({
  centre: { alignItems: 'center', gap: 18, paddingVertical: 28 },
  halo: { width: 120, height: 120, alignItems: 'center', justifyContent: 'center' },
  onde: { position: 'absolute', width: 120, height: 120, borderRadius: 60, backgroundColor: couleurs.feuille },
  coeur: { width: 88, height: 88, borderRadius: 44, backgroundColor: couleurs.pousse, alignItems: 'center', justifyContent: 'center' },
  sources: { backgroundColor: 'transparent', shadowOpacity: 0, elevation: 0, gap: 6 },
  sourcesTete: { flexDirection: 'row', alignItems: 'center', gap: 8 },
});
