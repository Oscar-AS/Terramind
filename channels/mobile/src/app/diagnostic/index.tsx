import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { Camera, Images, Leaf, Sun } from 'phosphor-react-native';
import { useEffect, useState } from 'react';
import { Animated, Easing, Platform, StyleSheet, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Apparition, Bouton, T } from '@/components/ui';
import { couleurs } from '@/theme';

/** Cadre de visée : coins marqués et feuille qui flotte doucement. */
function Viseur() {
  const [v] = useState(() => new Animated.Value(0));
  useEffect(() => {
    const boucle = Animated.loop(Animated.sequence([
      Animated.timing(v, { toValue: 1, duration: 1600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      Animated.timing(v, { toValue: 0, duration: 1600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
    ]));
    boucle.start();
    return () => boucle.stop();
  }, [v]);
  return (
    <View style={styles.viseur}>
      {(['hg', 'hd', 'bg', 'bd'] as const).map((c) => <View key={c} style={[styles.coin, styles[c]]} />)}
      <Animated.View style={{ transform: [{ translateY: v.interpolate({ inputRange: [0, 1], outputRange: [-8, 8] }) }, { rotate: '-12deg' }] }}>
        <Leaf size={120} color={couleurs.feuille} weight="duotone" />
      </Animated.View>
    </View>
  );
}

// Étape 5a : photo de ce qui inquiète (feuille, fruit, tige ou plante entière). Appareil photo du téléphone (cadrage carré), galerie en secours.
export default function Photo() {
  const [message, setMessage] = useState<string | null>(null);

  const ouvrir = async (source: 'camera' | 'galerie') => {
    setMessage(null);
    if (source === 'camera' && Platform.OS !== 'web') {
      const { granted } = await ImagePicker.requestCameraPermissionsAsync();
      if (!granted) {
        setMessage("Sans l'appareil photo, choisis une photo dans ta galerie.");
        return;
      }
    }
    const options: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], quality: 0.8, allowsEditing: true, aspect: [1, 1] };
    const r = source === 'camera' ? await ImagePicker.launchCameraAsync(options) : await ImagePicker.launchImageLibraryAsync(options);
    if (r.canceled || !r.assets?.[0]) return;
    router.push({ pathname: '/diagnostic/resultat', params: { uri: r.assets[0].uri, type: r.assets[0].mimeType ?? '' } });
  };

  return (
    <Ecran titre="Ma plante est malade">
      <Apparition ordre={0}><Viseur /></Apparition>
      <Apparition ordre={1} style={styles.conseils}>
        <View style={styles.conseil}><Leaf size={22} color={couleurs.foret} weight="duotone" /><T v="corps" style={{ flex: 1 }}>Feuille, fruit ou toute la plante, de près</T></View>
        <View style={styles.conseil}><Sun size={22} color={couleurs.soleil} weight="duotone" /><T v="corps" style={{ flex: 1 }}>À la lumière du jour</T></View>
      </Apparition>
      {message ? <T v="corpsGras" style={{ color: couleurs.terre }}>{message}</T> : null}
      <Apparition ordre={2}><Bouton libelle="Prendre la photo" Icone={Camera} onPress={() => ouvrir('camera')} /></Apparition>
      <Apparition ordre={3}><Bouton libelle="Choisir dans ma galerie" Icone={Images} onPress={() => ouvrir('galerie')} variante="clair" /></Apparition>
    </Ecran>
  );
}

const COIN = { position: 'absolute' as const, width: 44, height: 44, borderColor: couleurs.foret };
const styles = StyleSheet.create({
  viseur: { aspectRatio: 1.15, borderRadius: 28, backgroundColor: couleurs.pousse, alignItems: 'center', justifyContent: 'center' },
  coin: COIN,
  hg: { top: 18, left: 18, borderTopWidth: 5, borderLeftWidth: 5, borderTopLeftRadius: 14 },
  hd: { top: 18, right: 18, borderTopWidth: 5, borderRightWidth: 5, borderTopRightRadius: 14 },
  bg: { bottom: 18, left: 18, borderBottomWidth: 5, borderLeftWidth: 5, borderBottomLeftRadius: 14 },
  bd: { bottom: 18, right: 18, borderBottomWidth: 5, borderRightWidth: 5, borderBottomRightRadius: 14 },
  conseils: { gap: 10 },
  conseil: { flexDirection: 'row', alignItems: 'center', gap: 12 },
});
