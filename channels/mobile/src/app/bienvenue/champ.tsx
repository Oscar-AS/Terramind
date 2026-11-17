import { router } from 'expo-router';
import { ArrowRight, Drop, type Icon, Mountains, Question, ThumbsDown, ThumbsUp } from 'phosphor-react-native';
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Apparition, Bouton, Carte, Pastille, T } from '@/components/ui';
import { type OuiNon, profil } from '@/profil';
import { couleurs, polices, tailles } from '@/theme';

// Étape 1c : les deux questions de /v1/plan (eau_puits_salee, champ_en_bas_fond).
const QUESTIONS: { cle: 'eauSalee' | 'basFond'; Icone: Icon; texte: string }[] = [
  { cle: 'eauSalee', Icone: Drop, texte: "L'eau de ton puits est-elle salée ?" },
  { cle: 'basFond', Icone: Mountains, texte: 'Ton champ est-il dans un bas-fond ?' },
];
const CHOIX: { valeur: OuiNon; Icone: Icon; libelle: string }[] = [
  { valeur: 'oui', Icone: ThumbsUp, libelle: 'Oui' },
  { valeur: 'non', Icone: ThumbsDown, libelle: 'Non' },
  { valeur: 'ne_sait_pas', Icone: Question, libelle: 'Je ne sais pas' },
];

export default function Champ() {
  const depart = profil.lire();
  const [rep, setRep] = useState<Record<string, OuiNon | undefined>>({ eauSalee: depart.eauSalee, basFond: depart.basFond });
  const terminer = () => {
    profil.ecrire({ eauSalee: rep.eauSalee ?? 'ne_sait_pas', basFond: rep.basFond ?? 'ne_sait_pas' });
    router.replace('/accueil');
  };

  return (
    <Ecran titre="Ton champ" avecRetour={false} etape={{ actuelle: 3, total: 3 }}>
      {QUESTIONS.map((q, i) => (
        <Apparition key={q.cle} ordre={i + 1}>
          <Carte>
            <View style={styles.tete}>
              <Pastille Icone={q.Icone} taille={52} />
              <T v="corpsGras" style={{ flex: 1, fontSize: 19 }}>{q.texte}</T>
            </View>
            <View style={styles.reponses}>
              {CHOIX.map((c) => {
                const choisi = rep[q.cle] === c.valeur;
                return (
                  <Pressable key={c.valeur} accessibilityRole="radio" accessibilityState={{ selected: choisi }} accessibilityLabel={c.libelle}
                    onPress={() => setRep((r) => ({ ...r, [q.cle]: c.valeur }))}
                    style={[styles.choix, choisi && styles.choisi]}>
                    <c.Icone size={28} color={choisi ? couleurs.blanc : couleurs.foret} weight={choisi ? 'fill' : 'duotone'} />
                    <T style={[styles.choixTexte, choisi && { color: couleurs.blanc }]}>{c.libelle}</T>
                  </Pressable>
                );
              })}
            </View>
          </Carte>
        </Apparition>
      ))}
      <Apparition ordre={3}><Bouton libelle="C'est bon" Icone={ArrowRight} onPress={terminer} /></Apparition>
    </Ecran>
  );
}

const styles = StyleSheet.create({
  tete: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  reponses: { flexDirection: 'row', gap: 8, marginTop: 4 },
  choix: {
    flex: 1, minHeight: 84, borderRadius: tailles.rayonPetit, alignItems: 'center', justifyContent: 'center', gap: 6,
    backgroundColor: couleurs.sable, borderWidth: 2, borderColor: couleurs.trait, paddingHorizontal: 4,
  },
  choisi: { backgroundColor: couleurs.foret, borderColor: couleurs.foret },
  choixTexte: { fontFamily: polices.texteGras, fontSize: 15, color: couleurs.encre, textAlign: 'center' },
});
