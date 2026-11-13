import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { couleurs, tailles } from '@/theme';

// Étape 1c : les deux questions de /v1/plan (eau_puits_salee, champ_en_bas_fond).
const QUESTIONS = [
  { icone: '💧', texte: "L'eau de ton puits est-elle salée ?" },
  { icone: '⛰️', texte: 'Ton champ est-il dans un bas-fond ?' },
];

export default function Champ() {
  return (
    <Ecran titre="Ton champ" avecAccueil={false} etape={{ actuelle: 3, total: 3 }}>
      {QUESTIONS.map((q) => (
        <View key={q.texte} style={styles.question}>
          <Text style={styles.icone}>{q.icone}</Text>
          <Text style={styles.texte}>{q.texte}</Text>
          <View style={styles.reponses}>
            <View style={styles.reponse}>
              <GrosBouton icone="👍" libelle="Oui" variante="clair" />
            </View>
            <View style={styles.reponse}>
              <GrosBouton icone="👎" libelle="Non" variante="clair" />
            </View>
          </View>
        </View>
      ))}
      <GrosBouton icone="✅" libelle="C'est bon" onPress={() => router.replace('/accueil')} />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  question: {
    backgroundColor: couleurs.blanc,
    borderRadius: tailles.rayon,
    padding: 16,
    gap: 12,
    alignItems: 'center',
  },
  icone: { fontSize: 48 },
  texte: { fontSize: tailles.corps, fontWeight: '600', color: couleurs.texte, textAlign: 'center' },
  reponses: { flexDirection: 'row', gap: 12, alignSelf: 'stretch' },
  reponse: { flex: 1 },
});
