import { router } from 'expo-router';
import { Translate } from 'phosphor-react-native';
import { Pressable, StyleSheet, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Apparition, Pastille, T } from '@/components/ui';
import { profil } from '@/profil';
import { couleurs, ombre, tailles } from '@/theme';

const LANGUES = [
  { id: 'wo' as const, nom: 'Wolof', dit: 'Réponses vocales bientôt', drapeau: '🇸🇳' },
  { id: 'fr' as const, nom: 'Français', dit: 'Disponible maintenant', drapeau: '🇫🇷' },
];

// Étape 1a : choix de la langue, en tout premier (docs/maquettes/references-ecrans.md).
export default function Langue() {
  const choisir = (langue: 'fr' | 'wo') => {
    profil.ecrire({ langue });
    router.push('/bienvenue/position');
  };
  return (
    <Ecran titre="Wolof ou français ?" avecRetour={false} etape={{ actuelle: 1, total: 3 }}>
      {LANGUES.map((l, i) => (
        <Apparition key={l.id} ordre={i + 1}>
          <Pressable accessibilityRole="button" accessibilityLabel={l.nom} onPress={() => choisir(l.id)}
            style={({ pressed }) => [styles.choix, pressed && { transform: [{ scale: 0.98 }], borderColor: couleurs.feuille }]}>
            <T style={styles.drapeau}>{l.drapeau}</T>
            <View style={{ flex: 1 }}>
              <T v="sousTitre">{l.nom}</T>
              <T v="petit">{l.dit}</T>
            </View>
          </Pressable>
        </Apparition>
      ))}
      <Apparition ordre={3} style={styles.note}>
        <Pastille Icone={Translate} taille={40} />
        <T v="petit" style={{ flex: 1 }}>{"Les réponses en wolof arrivent bientôt. Pour l'instant, TerraMind répond en français."}</T>
      </Apparition>
    </Ecran>
  );
}

const styles = StyleSheet.create({
  choix: {
    flexDirection: 'row', alignItems: 'center', gap: 16, padding: 20, borderRadius: tailles.rayon,
    backgroundColor: couleurs.carte, borderWidth: 2, borderColor: couleurs.trait, ...ombre,
  },
  drapeau: { fontSize: 44 },
  note: { flexDirection: 'row', alignItems: 'center', gap: 12 },
});
