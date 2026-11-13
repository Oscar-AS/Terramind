import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { useState } from 'react';
import { Platform, StyleSheet, Text, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { couleurs, tailles } from '@/theme';

// Étape 5a : photo d'une feuille. Appareil photo du téléphone (cadrage carré), galerie en secours.
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
    const r = source === 'camera'
      ? await ImagePicker.launchCameraAsync(options)
      : await ImagePicker.launchImageLibraryAsync(options);
    if (r.canceled || !r.assets?.[0]) return;
    const a = r.assets[0];
    router.push({ pathname: '/diagnostic/resultat', params: { uri: a.uri, type: a.mimeType ?? '' } });
  };

  return (
    <Ecran titre="Ma plante est malade">
      <View style={styles.cadre}>
        <Text style={styles.cadreIcone}>🍃</Text>
        <Text style={styles.cadreTexte}>Une seule feuille, de près, à la lumière du jour.</Text>
      </View>
      {message ? <Text style={styles.message}>{message}</Text> : null}
      <GrosBouton icone="📸" libelle="Prendre la photo" onPress={() => ouvrir('camera')} />
      <GrosBouton icone="🖼️" libelle="Choisir dans ma galerie" onPress={() => ouvrir('galerie')} variante="clair" />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  cadre: {
    aspectRatio: 1, borderRadius: tailles.rayon, borderWidth: 4, borderStyle: 'dashed', borderColor: couleurs.vert,
    alignItems: 'center', justifyContent: 'center', gap: 12, padding: 24, backgroundColor: couleurs.vertClair,
  },
  cadreIcone: { fontSize: 96 },
  cadreTexte: { fontSize: 20, fontWeight: '600', color: couleurs.texte, textAlign: 'center' },
  message: { fontSize: 17, color: couleurs.ocre, textAlign: 'center' },
});
