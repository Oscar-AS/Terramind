import {
  AndroidImportance, getPermissionsAsync, requestPermissionsAsync, setNotificationChannelAsync,
} from 'expo-notifications';
import { router } from 'expo-router';
import { BellRinging, ThumbsUp, X } from 'phosphor-react-native';
import { useState } from 'react';
import { Platform, StyleSheet, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Apparition, Bouton, T } from '@/components/ui';
import { couleurs } from '@/theme';

// Autorisation des notifications, demandée au moment où elle a un sens (après la date de
// repiquage) et expliquée AVANT la fenêtre du système.
async function demanderAutorisation(): Promise<boolean> {
  if (Platform.OS === 'web') return false; // expo-notifications : Android et iOS seulement.
  if (Platform.OS === 'android') {
    // Android 13+ : la fenêtre n'apparaît qu'après la création d'au moins un canal.
    await setNotificationChannelAsync('alertes', { name: 'Alertes de la semaine', importance: AndroidImportance.HIGH });
  }
  if ((await getPermissionsAsync()).granted) return true;
  return (await requestPermissionsAsync()).granted;
}

export default function AutorisationNotifications() {
  const [refus, setRefus] = useState(false);
  const accepter = async () => {
    if (await demanderAutorisation()) router.dismissTo('/accueil');
    else setRefus(true);
  };

  return (
    <Ecran titre="Je te préviens ?">
      <Apparition ordre={0} style={styles.illustration}>
        <View style={styles.cloche}><BellRinging size={72} color={couleurs.terre} weight="duotone" /></View>
      </Apparition>
      <Apparition ordre={1}>
        <T v="corps" style={styles.texte}>Quand le temps favorise une maladie ou un ravageur, ton téléphone sonne pour te prévenir.</T>
      </Apparition>
      {refus ? <T v="corpsGras" style={styles.texte}>Pas de souci : tu verras les alertes en ouvrant TerraMind.</T> : null}
      <Apparition ordre={2}><Bouton libelle="Oui, préviens-moi" Icone={ThumbsUp} onPress={accepter} /></Apparition>
      <Apparition ordre={3}><Bouton libelle="Pas maintenant" Icone={X} onPress={() => router.dismissTo('/accueil')} variante="clair" /></Apparition>
    </Ecran>
  );
}

const styles = StyleSheet.create({
  illustration: { alignItems: 'center', paddingVertical: 8 },
  cloche: { width: 150, height: 150, borderRadius: 75, backgroundColor: couleurs.terreClair, alignItems: 'center', justifyContent: 'center' },
  texte: { textAlign: 'center', fontSize: 20, lineHeight: 29 },
});
