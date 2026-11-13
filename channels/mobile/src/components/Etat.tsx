import { useEffect, useState } from 'react';
import { ActivityIndicator, Animated, StyleSheet, Text, View } from 'react-native';

import { GrosBouton } from '@/components/GrosBouton';
import type { Source } from '@/api';
import { couleurs } from '@/theme';

/** Attente animée : une icône qui « respire » et une phrase (l'agriculteur sait que ça travaille). */
export function Chargement({ icone, texte }: { icone: string; texte: string }) {
  const [echelle] = useState(() => new Animated.Value(1));
  useEffect(() => {
    const boucle = Animated.loop(Animated.sequence([
      Animated.timing(echelle, { toValue: 1.15, duration: 700, useNativeDriver: true }),
      Animated.timing(echelle, { toValue: 1, duration: 700, useNativeDriver: true }),
    ]));
    boucle.start();
    return () => boucle.stop();
  }, [echelle]);
  return (
    <View style={styles.centre} accessibilityLiveRegion="polite">
      <Animated.Text style={[styles.icone, { transform: [{ scale: echelle }] }]}>{icone}</Animated.Text>
      <Text style={styles.texte}>{texte}</Text>
      <ActivityIndicator color={couleurs.vert} size="large" />
    </View>
  );
}

/** Erreur claire, avec un seul bouton pour réessayer. */
export function Erreur({ texte, onReessayer }: { texte: string; onReessayer: () => void }) {
  return (
    <View style={styles.centre}>
      <Text style={styles.icone}>📶</Text>
      <Text style={styles.texte}>{texte}</Text>
      <GrosBouton icone="🔁" libelle="Réessayer" onPress={onReessayer} variante="clair" />
    </View>
  );
}

/** Sources de la réponse, en petit : on montre d'où vient le conseil. */
export function Sources({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  const uniques = [...new Map(sources.map((s) => [`${s.document} ${s.page}`, s])).values()];
  return (
    <View style={styles.sources}>
      <Text style={styles.sourcesTitre}>Sources</Text>
      {uniques.map((s) => (
        <Text key={`${s.document}-${s.page}`} style={styles.source}>
          • {s.document}, p. {s.page}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  centre: { alignItems: 'center', gap: 16, paddingVertical: 32 },
  icone: { fontSize: 64 },
  texte: { fontSize: 20, color: couleurs.texte, textAlign: 'center', lineHeight: 28 },
  sources: { gap: 4, paddingTop: 8 },
  sourcesTitre: { fontSize: 14, fontWeight: '700', color: couleurs.texteDoux },
  source: { fontSize: 13, color: couleurs.texteDoux },
});
