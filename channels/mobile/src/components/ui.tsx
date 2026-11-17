// Briques visuelles communes : texte, bouton, carte, pastille, apparition animée.
import type { Icon as IconePhosphor } from 'phosphor-react-native';
import { type ReactNode, useEffect, useState } from 'react';
import {
  Animated, Pressable, type StyleProp, StyleSheet, Text, type TextProps, View, type ViewStyle,
} from 'react-native';

import { couleurs, ombre, polices, tailles } from '@/theme';

type Variante = 'titre' | 'sousTitre' | 'corps' | 'corpsGras' | 'petit' | 'etiquette';

export function T({ v = 'corps', style, ...p }: TextProps & { v?: Variante }) {
  return <Text {...p} style={[styles[v], style]} />;
}

/** Apparition douce (fondu + léger glissement), décalée selon l'ordre : l'écran se construit sous les yeux. */
export function Apparition({ ordre = 0, children, style }: { ordre?: number; children: ReactNode; style?: StyleProp<ViewStyle> }) {
  const [v] = useState(() => new Animated.Value(0));
  useEffect(() => {
    Animated.timing(v, { toValue: 1, duration: 320, delay: 60 * ordre, useNativeDriver: true }).start();
  }, [v, ordre]);
  return (
    <Animated.View style={[style, { opacity: v, transform: [{ translateY: v.interpolate({ inputRange: [0, 1], outputRange: [14, 0] }) }] }]}>
      {children}
    </Animated.View>
  );
}

type PropsBouton = {
  libelle: string;
  Icone?: IconePhosphor;
  onPress?: () => void;
  variante?: 'plein' | 'clair' | 'alerte';
  sousTitre?: string;
  desactive?: boolean;
};

/** Grand bouton : une icône, un mot, un toucher. Ressort à l'appui. */
export function Bouton({ libelle, Icone, onPress, variante = 'plein', sousTitre, desactive }: PropsBouton) {
  const [echelle] = useState(() => new Animated.Value(1));
  const ressort = (vers: number) => Animated.spring(echelle, { toValue: vers, useNativeDriver: true, speed: 40, bounciness: 6 }).start();
  const c = VARIANTES[variante];
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={libelle}
      accessibilityState={{ disabled: desactive }}
      disabled={desactive}
      onPress={onPress}
      onPressIn={() => ressort(0.97)}
      onPressOut={() => ressort(1)}
      android_ripple={{ color: 'rgba(0,0,0,0.06)', borderless: false }}>
      <Animated.View style={[styles.bouton, { backgroundColor: c.fond, borderColor: c.bord, transform: [{ scale: echelle }] },
        variante !== 'plein' && styles.boutonBord, desactive && { opacity: 0.5 }]}>
        {Icone ? (
          <View style={[styles.boutonIcone, { backgroundColor: c.pastille }]}>
            <Icone size={28} color={c.icone} weight="duotone" />
          </View>
        ) : null}
        <View style={{ flex: 1 }}>
          <Text style={[styles.boutonTexte, { color: c.texte }]}>{libelle}</Text>
          {sousTitre ? <Text style={[styles.boutonSous, { color: c.texte }]}>{sousTitre}</Text> : null}
        </View>
      </Animated.View>
    </Pressable>
  );
}

const VARIANTES = {
  plein: { fond: couleurs.foret, bord: couleurs.foret, texte: couleurs.blanc, icone: couleurs.blanc, pastille: 'rgba(255,255,255,0.14)' },
  clair: { fond: couleurs.carte, bord: couleurs.trait, texte: couleurs.encre, icone: couleurs.foret, pastille: couleurs.pousse },
  alerte: { fond: couleurs.terreClair, bord: '#EBC2AA', texte: couleurs.encre, icone: couleurs.terre, pastille: couleurs.carte },
};

export function Carte({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.carte, style]}>{children}</View>;
}

/** Pastille ronde avec une icône : repère visuel avant le texte. */
export function Pastille({ Icone, couleur = couleurs.foret, fond = couleurs.pousse, taille = 48 }: { Icone: IconePhosphor; couleur?: string; fond?: string; taille?: number }) {
  return (
    <View style={{ width: taille, height: taille, borderRadius: taille / 2, backgroundColor: fond, alignItems: 'center', justifyContent: 'center' }}>
      <Icone size={taille * 0.55} color={couleur} weight="duotone" />
    </View>
  );
}

/** Étiquette d'état : couleur ET icône ET mot (jamais la couleur seule). */
export function Badge({ Icone, texte, couleur, fond }: { Icone: IconePhosphor; texte: string; couleur: string; fond: string }) {
  return (
    <View style={[styles.badge, { backgroundColor: fond }]}>
      <Icone size={16} color={couleur} weight="bold" />
      <Text style={[styles.badgeTexte, { color: couleur }]}>{texte}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  titre: { fontFamily: polices.titre, fontSize: tailles.titre, color: couleurs.encre, letterSpacing: -0.5 },
  sousTitre: { fontFamily: polices.titreMoyen, fontSize: 21, color: couleurs.encre, letterSpacing: -0.2 },
  corps: { fontFamily: polices.texte, fontSize: tailles.corps, color: couleurs.encre, lineHeight: 26 },
  corpsGras: { fontFamily: polices.texteGras, fontSize: tailles.corps, color: couleurs.encre, lineHeight: 26 },
  petit: { fontFamily: polices.texte, fontSize: 14, color: couleurs.encreDouce, lineHeight: 20 },
  etiquette: { fontFamily: polices.texteGras, fontSize: 13, color: couleurs.encreDouce, letterSpacing: 1, textTransform: 'uppercase' },
  bouton: {
    minHeight: tailles.boutonMin + 12, borderRadius: tailles.rayon, flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 12, gap: 14, borderWidth: 1.5,
  },
  boutonBord: {},
  boutonIcone: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  boutonTexte: { fontFamily: polices.texteGras, fontSize: 19 },
  boutonSous: { fontFamily: polices.texte, fontSize: 14, opacity: 0.8, marginTop: 2 },
  carte: { backgroundColor: couleurs.carte, borderRadius: tailles.rayon, padding: 18, gap: 10, borderWidth: 1, borderColor: couleurs.trait, ...ombre },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start', borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 },
  badgeTexte: { fontFamily: polices.texteGras, fontSize: 14 },
});
