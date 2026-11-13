import {
  AndroidImportance,
  getPermissionsAsync,
  requestPermissionsAsync,
  setNotificationChannelAsync,
} from 'expo-notifications';
import { router } from 'expo-router';
import { useState } from 'react';
import { Platform, StyleSheet, Text } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { couleurs, tailles } from '@/theme';

// Autorisation des notifications, demandée au moment où elle a un sens
// (après la date de repiquage) et expliquée AVANT la fenêtre du système.
async function demanderAutorisation(): Promise<boolean> {
  if (Platform.OS === 'web') return false; // expo-notifications : Android et iOS seulement.
  if (Platform.OS === 'android') {
    // Android 13+ : la fenêtre n'apparaît qu'après la création d'au moins un canal.
    await setNotificationChannelAsync('alertes', {
      name: 'Alertes de la semaine',
      importance: AndroidImportance.HIGH,
    });
  }
  const actuel = await getPermissionsAsync();
  if (actuel.granted) return true;
  const reponse = await requestPermissionsAsync();
  return reponse.granted;
}

export default function AutorisationNotifications() {
  const [refus, setRefus] = useState(false);

  const accepter = async () => {
    const ok = await demanderAutorisation();
    if (ok) router.dismissTo('/accueil');
    else setRefus(true);
  };

  return (
    <Ecran titre="Je te préviens ?">
      <Text style={styles.icone}>🔔🍅</Text>
      {/* Phrase dite à voix haute en wolof avant la fenêtre du téléphone. */}
      <Text style={styles.texte}>
        Quand le temps est bon pour le mildiou, ton téléphone sonne pour te prévenir.
      </Text>
      {refus ? (
        <Text style={styles.refus}>
          Pas de souci : tu verras les alertes en ouvrant TerraMind.
        </Text>
      ) : null}
      <GrosBouton icone="👍" libelle="Oui, préviens-moi" onPress={accepter} />
      <GrosBouton
        icone="⏭️"
        libelle="Pas maintenant"
        onPress={() => router.dismissTo('/accueil')}
        variante="clair"
      />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  icone: { fontSize: 64, textAlign: 'center' },
  texte: { fontSize: 22, color: couleurs.texte, textAlign: 'center', lineHeight: 30 },
  refus: { fontSize: tailles.corps, color: couleurs.texteDoux, textAlign: 'center' },
});
