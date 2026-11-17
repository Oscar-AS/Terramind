import { router } from 'expo-router';
import { Check, Minus, Plus } from 'phosphor-react-native';
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Apparition, Bouton, Carte, T } from '@/components/ui';
import { CULTURES, profil } from '@/profil';
import { couleurs, ombre, polices, tailles } from '@/theme';

// Étape 4 : la culture et sa date de repiquage, qui déclenchent les alertes.
const COURT = ['janv.', 'févr.', 'mars', 'avril', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

function Compteur({ valeur, libelle, onMoins, onPlus }: { valeur: string; libelle: string; onMoins: () => void; onPlus: () => void }) {
  return (
    <View style={styles.compteur}>
      <T v="etiquette">{libelle}</T>
      <View style={styles.compteurLigne}>
        <Pressable accessibilityRole="button" accessibilityLabel={`${libelle} moins`} onPress={onMoins} style={styles.rond} hitSlop={6}>
          <Minus size={26} color={couleurs.foret} weight="bold" />
        </Pressable>
        <T style={styles.valeur} accessibilityLabel={`${libelle} : ${valeur}`}>{valeur}</T>
        <Pressable accessibilityRole="button" accessibilityLabel={`${libelle} plus`} onPress={onPlus} style={styles.rond} hitSlop={6}>
          <Plus size={26} color={couleurs.foret} weight="bold" />
        </Pressable>
      </View>
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
  // Mois en cours : pas au-delà d'aujourd'hui (une plantation n'est jamais dans le futur).
  const joursDuMois = mois === aujourdhui.getMonth() && annee === aujourdhui.getFullYear()
    ? aujourdhui.getDate() : new Date(annee, mois + 1, 0).getDate();
  const j = Math.min(jour, joursDuMois);
  const date = `${annee}-${String(mois + 1).padStart(2, '0')}-${String(j).padStart(2, '0')}`;

  const enregistrer = () => {
    profil.ecrire({ culture, dateRepiquage: date });
    // Pas d'écran « Je te préviens ? » : aucune notification n'est encore envoyée (règle « rien de factice »).
    router.dismissTo('/accueil');
  };

  return (
    <Ecran titre="Mes cultures">
      <T v="corps" style={{ color: couleurs.encreDouce }}>{"Qu'est-ce que tu as planté ?"}</T>
      <View style={styles.grille}>
        {CULTURES.map((c, i) => {
          const choisi = culture === c.id;
          return (
            <Apparition key={c.id} ordre={i} style={styles.case}>
              <Pressable accessibilityRole="radio" accessibilityState={{ selected: choisi }} accessibilityLabel={c.libelle}
                onPress={() => setCulture(c.id)} style={[styles.tuile, choisi && styles.tuileChoisie]}>
                {choisi ? <View style={styles.coche}><Check size={16} color={couleurs.blanc} weight="bold" /></View> : null}
                <T style={{ fontSize: 44 }}>{c.icone}</T>
                <T style={[styles.tuileTexte, choisi && { color: couleurs.foret }]}>{c.libelle}</T>
              </Pressable>
            </Apparition>
          );
        })}
      </View>
      {culture ? (
        <Apparition>
          <Carte>
            <T v="sousTitre">{"Tu l'as plantée quand ?"}</T>
            <View style={styles.date}>
              <Compteur valeur={String(j)} libelle="Jour"
                onMoins={() => setJour(j <= 1 ? joursDuMois : j - 1)} onPlus={() => setJour(j >= joursDuMois ? 1 : j + 1)} />
              <Compteur valeur={COURT[mois]} libelle="Mois"
                onMoins={() => setMois((mois + 11) % 12)} onPlus={() => setMois((mois + 1) % 12)} />
            </View>
            <T v="corpsGras" style={{ textAlign: 'center', color: couleurs.foret }}>Le {j} {MOIS[mois]} {annee}</T>
          </Carte>
          <View style={{ height: 16 }} />
          <Bouton libelle="C'est noté" Icone={Check} onPress={enregistrer} />
        </Apparition>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  grille: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -6 },
  case: { width: '33.33%', padding: 6 },
  tuile: {
    aspectRatio: 0.9, borderRadius: tailles.rayon, backgroundColor: couleurs.carte, alignItems: 'center', justifyContent: 'center',
    gap: 6, borderWidth: 2, borderColor: couleurs.trait, ...ombre,
  },
  tuileChoisie: { borderColor: couleurs.feuille, backgroundColor: couleurs.pousse },
  coche: { position: 'absolute', top: 8, right: 8, width: 24, height: 24, borderRadius: 12, backgroundColor: couleurs.feuille, alignItems: 'center', justifyContent: 'center' },
  tuileTexte: { fontFamily: polices.texteGras, fontSize: 14, color: couleurs.encre, textAlign: 'center' },
  date: { flexDirection: 'row', gap: 12 },
  compteur: { flex: 1, alignItems: 'center', gap: 8, backgroundColor: couleurs.sable, borderRadius: 18, padding: 12 },
  compteurLigne: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  rond: { width: 48, height: 48, borderRadius: 24, backgroundColor: couleurs.carte, borderWidth: 1, borderColor: couleurs.trait, alignItems: 'center', justifyContent: 'center' },
  valeur: { fontFamily: polices.titre, fontSize: 26, color: couleurs.encre, minWidth: 56, textAlign: 'center' },
});
