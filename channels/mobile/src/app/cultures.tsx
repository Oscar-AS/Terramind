import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { CULTURES, profil } from '@/profil';
import { couleurs, tailles } from '@/theme';

// Étape 4 : la culture et sa date de repiquage, qui déclenchent les alertes.
const MOIS = ['janv.', 'févr.', 'mars', 'avril', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];

function Compteur({ valeur, libelle, onMoins, onPlus }: { valeur: string; libelle: string; onMoins: () => void; onPlus: () => void }) {
  return (
    <View style={styles.compteur}>
      <Pressable accessibilityLabel={`${libelle} moins`} onPress={onMoins} style={styles.rond}><Text style={styles.rondTexte}>−</Text></Pressable>
      <Text style={styles.valeur} accessibilityLabel={`${libelle} : ${valeur}`}>{valeur}</Text>
      <Pressable accessibilityLabel={`${libelle} plus`} onPress={onPlus} style={styles.rond}><Text style={styles.rondTexte}>+</Text></Pressable>
    </View>
  );
}

export default function Cultures() {
  const depart = profil.lire();
  const aujourdhui = new Date();
  const initiale = depart.dateRepiquage ? new Date(depart.dateRepiquage) : aujourdhui;
  const [culture, setCulture] = useState(depart.culture);
  const [jour, setJour] = useState(initiale.getDate());
  const [mois, setMois] = useState(initiale.getMonth());

  // Repiquage dans les 12 derniers mois : si le mois choisi est après le mois courant, c'est l'an dernier.
  const annee = mois > aujourdhui.getMonth() ? aujourdhui.getFullYear() - 1 : aujourdhui.getFullYear();
  const joursDuMois = new Date(annee, mois + 1, 0).getDate();
  const jourValide = Math.min(jour, joursDuMois);
  const date = `${annee}-${String(mois + 1).padStart(2, '0')}-${String(jourValide).padStart(2, '0')}`;

  const enregistrer = () => {
    profil.ecrire({ culture, dateRepiquage: date });
    router.push('/notifications');
  };

  return (
    <Ecran titre="Mes cultures">
      <Text style={styles.question}>{"Qu'est-ce que tu as planté ?"}</Text>
      <View style={styles.grille}>
        {CULTURES.map((c) => (
          <Pressable
            key={c.id}
            accessibilityRole="radio"
            accessibilityState={{ selected: culture === c.id }}
            accessibilityLabel={c.libelle}
            onPress={() => setCulture(c.id)}
            style={[styles.tuile, culture === c.id && styles.tuileChoisie]}>
            <Text style={styles.tuileIcone}>{c.icone}</Text>
            <Text style={[styles.tuileTexte, culture === c.id && { color: couleurs.blanc }]}>{c.libelle}</Text>
          </Pressable>
        ))}
      </View>
      {culture ? (
        <>
          <Text style={styles.question}>Quand as-tu repiqué ?</Text>
          <View style={styles.date}>
            <Compteur valeur={String(jourValide)} libelle="Jour"
              onMoins={() => setJour(jourValide <= 1 ? joursDuMois : jourValide - 1)}
              onPlus={() => setJour(jourValide >= joursDuMois ? 1 : jourValide + 1)} />
            <Compteur valeur={MOIS[mois]} libelle="Mois"
              onMoins={() => setMois((mois + 11) % 12)} onPlus={() => setMois((mois + 1) % 12)} />
          </View>
          <Text style={styles.rappel}>{jourValide} {MOIS[mois]} {annee}</Text>
          <GrosBouton icone="✅" libelle="C'est noté" onPress={enregistrer} />
        </>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  question: { fontSize: 20, fontWeight: '700', color: couleurs.texte, textAlign: 'center' },
  grille: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'center' },
  tuile: {
    width: '30%', minWidth: 96, aspectRatio: 1, borderRadius: tailles.rayon, backgroundColor: couleurs.vertClair,
    alignItems: 'center', justifyContent: 'center', gap: 4, borderWidth: 3, borderColor: 'transparent',
  },
  tuileChoisie: { backgroundColor: couleurs.vert, borderColor: couleurs.vert },
  tuileIcone: { fontSize: 40 },
  tuileTexte: { fontSize: 14, fontWeight: '700', color: couleurs.texte, textAlign: 'center' },
  date: { flexDirection: 'row', gap: 12, justifyContent: 'center' },
  compteur: { flex: 1, alignItems: 'center', gap: 8, backgroundColor: couleurs.blanc, borderRadius: tailles.rayon, padding: 12 },
  rond: {
    width: tailles.boutonMin, height: tailles.boutonMin, borderRadius: tailles.boutonMin / 2,
    backgroundColor: couleurs.vertClair, alignItems: 'center', justifyContent: 'center',
  },
  rondTexte: { fontSize: 32, fontWeight: '700', color: couleurs.texte },
  valeur: { fontSize: 26, fontWeight: '800', color: couleurs.texte },
  rappel: { fontSize: 18, color: couleurs.texteDoux, textAlign: 'center' },
});
