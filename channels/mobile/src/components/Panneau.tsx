// Panneau latéral des conversations, comme ChatGPT : « Nouvelle conversation » en haut, puis les récentes.
// Il glisse depuis la gauche ; toucher le voile ou la croix le referme.
import type { Icon } from 'phosphor-react-native';
import { Camera } from 'phosphor-react-native/src/icons/Camera';
import { ChatCircleText } from 'phosphor-react-native/src/icons/ChatCircleText';
import { CloudSun } from 'phosphor-react-native/src/icons/CloudSun';
import { MapPin } from 'phosphor-react-native/src/icons/MapPin';
import { Microphone } from 'phosphor-react-native/src/icons/Microphone';
import { Plant } from 'phosphor-react-native/src/icons/Plant';
import { NotePencil } from 'phosphor-react-native/src/icons/NotePencil';
import { X } from 'phosphor-react-native/src/icons/X';
import { useEffect, useState } from 'react';
import { Animated, Easing, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { T } from '@/components/ui';
import type { Conversation } from '@/profil';
import { couleurs, polices } from '@/theme';

const LARGEUR = 300;

const heure = (t: number) => {
  const d = new Date(t);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

/** Groupes par jour (Aujourd'hui, Hier, Plus tôt), comme les historiques de ChatGPT ou de la « Chat Sidebar » de 21st.dev. */
function groupe(t: number) {
  const d = new Date(t).toDateString();
  if (d === new Date().toDateString()) return "Aujourd'hui";
  if (d === new Date(Date.now() - 86_400_000).toDateString()) return 'Hier';
  return 'Plus tôt';
}

/** Une icône par sorte de conversation, pour la reconnaître sans lire. */
function iconeDe(titre: string): Icon {
  const t = titre.toLowerCase();
  if (t.includes('photo') || t.includes('malade')) return Camera;
  if (t.includes('planter')) return Plant;
  if (t.includes('météo')) return CloudSun;
  if (t.includes('position')) return MapPin;
  if (t.includes('micro')) return Microphone;
  return ChatCircleText;
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

        <ScrollView style={{ flex: 1, marginTop: 10 }} contentContainerStyle={{ gap: 2, paddingBottom: 12 }}>
          {recentes.map((c, i) => {
            const active = c.id === actuelle;
            const Icone = iconeDe(c.titre);
            const titreGroupe = groupe(c.maj);
            return (
              <View key={c.id}>
                {i === 0 || groupe(recentes[i - 1].maj) !== titreGroupe ? <T style={styles.section}>{titreGroupe}</T> : null}
                <Pressable accessibilityRole="button" disabled={occupe && !active} onPress={() => onChoisir(c.id)}
                  style={({ pressed }) => [styles.ligne, active && styles.ligneActive, pressed && { backgroundColor: couleurs.pousse }]}>
                  <View style={[styles.pastille, active && { backgroundColor: couleurs.foret }]}>
                    <Icone size={18} color={active ? couleurs.blanc : couleurs.foret} weight={active ? 'fill' : 'regular'} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <T style={[styles.titre, active && { fontFamily: polices.texteGras }]} numberOfLines={1}>{c.titre || 'Nouvelle conversation'}</T>
                    <T style={styles.date}>{active ? `En cours · ${heure(c.maj)}` : heure(c.maj)}</T>
                  </View>
                </Pressable>
              </View>
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
  section: { fontFamily: polices.texteGras, fontSize: 12.5, color: '#8C877B', letterSpacing: 0.4, textTransform: 'uppercase', marginTop: 16, marginBottom: 6, marginLeft: 14 },
  pastille: { width: 34, height: 34, borderRadius: 17, backgroundColor: couleurs.pousse, alignItems: 'center', justifyContent: 'center' },
  ligne: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 52, paddingHorizontal: 14, paddingVertical: 6, borderRadius: 14 },
  ligneActive: { backgroundColor: couleurs.sable },
  titre: { fontFamily: polices.texte, fontSize: 15.5, color: couleurs.encre },
  date: { fontFamily: polices.texte, fontSize: 12.5, color: '#8C877B', marginTop: 1 },
});
