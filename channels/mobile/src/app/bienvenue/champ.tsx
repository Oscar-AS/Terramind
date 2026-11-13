import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { type OuiNon, profil } from '@/profil';
import { couleurs, tailles } from '@/theme';

// Étape 1c : les deux questions de /v1/plan (eau_puits_salee, champ_en_bas_fond).
const QUESTIONS = [
  { cle: 'eauSalee', icone: '💧', texte: "L'eau de ton puits est-elle salée ?" },
  { cle: 'basFond', icone: '⛰️', texte: 'Ton champ est-il dans un bas-fond ?' },
] as const;
const CHOIX: { valeur: OuiNon; icone: string; libelle: string }[] = [
  { valeur: 'oui', icone: '👍', libelle: 'Oui' },
  { valeur: 'non', icone: '👎', libelle: 'Non' },
  { valeur: 'ne_sait_pas', icone: '🤷🏿', libelle: 'Je ne sais pas' },
];

export default function Champ() {
  const depart = profil.lire();
  const [reponses, setReponses] = useState<Record<string, OuiNon | undefined>>({
    eauSalee: depart.eauSalee, basFond: depart.basFond,
  });

  const terminer = () => {
    profil.ecrire({ eauSalee: reponses.eauSalee ?? 'ne_sait_pas', basFond: reponses.basFond ?? 'ne_sait_pas' });
    router.replace('/accueil');
  };

  return (
    <Ecran titre="Ton champ" avecAccueil={false} etape={{ actuelle: 3, total: 3 }}>
      {QUESTIONS.map((q) => (
        <View key={q.cle} style={styles.question}>
          <Text style={styles.icone}>{q.icone}</Text>
          <Text style={styles.texte}>{q.texte}</Text>
          <View style={styles.reponses}>
            {CHOIX.map((c) => {
              const choisi = reponses[q.cle] === c.valeur;
              return (
                <Pressable
                  key={c.valeur}
                  accessibilityRole="radio"
                  accessibilityState={{ selected: choisi }}
                  accessibilityLabel={c.libelle}
                  onPress={() => setReponses((r) => ({ ...r, [q.cle]: c.valeur }))}
                  style={[styles.choix, choisi && styles.choisi]}>
                  <Text style={styles.choixIcone}>{c.icone}</Text>
                  <Text style={[styles.choixTexte, choisi && styles.choisiTexte]}>{c.libelle}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ))}
      <GrosBouton icone="✅" libelle="C'est bon" onPress={terminer} />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  question: { backgroundColor: couleurs.blanc, borderRadius: tailles.rayon, padding: 16, gap: 12, alignItems: 'center' },
  icone: { fontSize: 48 },
  texte: { fontSize: tailles.corps, fontWeight: '600', color: couleurs.texte, textAlign: 'center' },
  reponses: { flexDirection: 'row', gap: 8, alignSelf: 'stretch' },
  choix: {
    flex: 1, minHeight: tailles.boutonMin * 1.3, borderRadius: tailles.rayon, alignItems: 'center',
    justifyContent: 'center', backgroundColor: couleurs.vertClair, borderWidth: 3, borderColor: 'transparent', gap: 4,
  },
  choisi: { borderColor: couleurs.vert, backgroundColor: couleurs.vert },
  choixIcone: { fontSize: 28 },
  choixTexte: { fontSize: 15, fontWeight: '700', color: couleurs.texte, textAlign: 'center' },
  choisiTexte: { color: couleurs.blanc },
});
