// Panneau latéral des conversations, comme ChatGPT : « Nouvelle conversation » en haut, puis les récentes.
// Il glisse depuis la gauche ; toucher le voile ou la croix le referme.
import { ChatCircleText } from 'phosphor-react-native/src/icons/ChatCircleText';
import { NotePencil } from 'phosphor-react-native/src/icons/NotePencil';
import { X } from 'phosphor-react-native/src/icons/X';
import { useEffect, useState } from 'react';
import { Animated, Easing, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { T } from '@/components/ui';
import type { Conversation } from '@/profil';
import { couleurs, polices } from '@/theme';

const LARGEUR = 300;

function quand(t: number) {
  const d = new Date(t);
  const heure = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  if (d.toDateString() === new Date().toDateString()) return `Aujourd'hui, ${heure}`;
  if (d.toDateString() === new Date(Date.now() - 86_400_000).toDateString()) return `Hier, ${heure}`;
  return `${d.getDate()}/${String(d.getMonth() + 1).padStart(2, '0')}, ${heure}`;
}

type Props = {
  ouvert: boolean;
  onFermer: () => void;
  liste: Conversation[];
  actuelle: string;
  occupe: boolean;
  onNouvelle: () => void;
  onChoisir: (id: string) => void;
};

export function Panneau({ ouvert, onFermer, liste, actuelle, occupe, onNouvelle, onChoisir }: Props) {
  const marges = useSafeAreaInsets();
  const [v] = useState(() => new Animated.Value(0));
  // Reste affiché le temps de l'animation de fermeture.
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    Animated.timing(v, { toValue: ouvert ? 1 : 0, duration: 240, easing: Easing.out(Easing.cubic), useNativeDriver: true })
      .start(() => setVisible(ouvert));
  }, [ouvert, v]);

  if (!ouvert && !visible) return null;
  const recentes = [...liste].sort((a, b) => b.maj - a.maj);
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents={ouvert ? 'auto' : 'none'}>
      <Animated.View style={[StyleSheet.absoluteFill, styles.voile, { opacity: v }]}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onFermer} accessibilityLabel="Fermer la liste des conversations" />
      </Animated.View>
      <Animated.View style={[styles.panneau, { paddingTop: marges.top + 14, paddingBottom: marges.bottom + 12 },
        { transform: [{ translateX: v.interpolate({ inputRange: [0, 1], outputRange: [-LARGEUR, 0] }) }] }]}>
        <View style={styles.tete}>
          <T style={styles.marque}>TerraMind</T>
          <Pressable accessibilityRole="button" accessibilityLabel="Fermer" hitSlop={8} onPress={onFermer} style={styles.fermer}>
            <X size={20} color={couleurs.encre} />
          </Pressable>
        </View>

        <Pressable accessibilityRole="button" disabled={occupe} onPress={onNouvelle}
          style={({ pressed }) => [styles.nouvelle, pressed && { backgroundColor: couleurs.pousse }, occupe && { opacity: 0.5 }]}>
          <NotePencil size={22} color={couleurs.foret} />
          <T style={styles.texteNouvelle}>Nouvelle conversation</T>
        </Pressable>
        {occupe ? <T style={styles.attente}>TerraMind répond encore…</T> : null}

        <T style={styles.section}>Récentes</T>
        <ScrollView style={{ flex: 1 }} contentContainerStyle={{ gap: 2 }}>
          {recentes.map((c) => {
            const active = c.id === actuelle;
            return (
              <Pressable key={c.id} accessibilityRole="button" disabled={occupe && !active} onPress={() => onChoisir(c.id)}
                style={({ pressed }) => [styles.ligne, active && styles.ligneActive, pressed && { backgroundColor: couleurs.pousse }]}>
                <ChatCircleText size={20} color={active ? couleurs.foret : couleurs.encreDouce} />
                <View style={{ flex: 1 }}>
                  <T style={[styles.titre, active && { fontFamily: polices.texteGras }]} numberOfLines={1}>{c.titre || 'Nouvelle conversation'}</T>
                  <T style={styles.date}>{quand(c.maj)}</T>
                </View>
              </Pressable>
            );
          })}
        </ScrollView>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  voile: { backgroundColor: 'rgba(27,38,32,0.35)' },
  panneau: {
    position: 'absolute', top: 0, bottom: 0, left: 0, width: LARGEUR, backgroundColor: couleurs.carte, paddingHorizontal: 12,
    borderTopRightRadius: 24, borderBottomRightRadius: 24,
    shadowColor: '#000', shadowOpacity: 0.15, shadowRadius: 20, shadowOffset: { width: 4, height: 0 }, elevation: 12,
  },
  tete: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 8, marginBottom: 14 },
  marque: { fontFamily: polices.titreDemi, fontSize: 24, color: couleurs.encre, letterSpacing: -0.4 },
  fermer: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  nouvelle: {
    flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 50, paddingHorizontal: 14, borderRadius: 14,
    backgroundColor: couleurs.sable,
  },
  texteNouvelle: { fontFamily: polices.texteGras, fontSize: 16, color: couleurs.foret },
  attente: { fontFamily: polices.texte, fontSize: 13, color: couleurs.encreDouce, marginTop: 6, marginLeft: 14 },
  section: { fontFamily: polices.texte, fontSize: 14, color: '#8C877B', marginTop: 26, marginBottom: 8, marginLeft: 14 },
  ligne: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 52, paddingHorizontal: 14, paddingVertical: 6, borderRadius: 14 },
  ligneActive: { backgroundColor: couleurs.sable },
  titre: { fontFamily: polices.texte, fontSize: 15.5, color: couleurs.encre },
  date: { fontFamily: polices.texte, fontSize: 12.5, color: '#8C877B', marginTop: 1 },
});
