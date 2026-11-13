import { router } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { profil } from '@/profil';
import { couleurs } from '@/theme';

// Étape 1a : choix de la langue, en tout premier (docs/maquettes/references-ecrans.md).
export default function Langue() {
  const choisir = (langue: 'fr' | 'wo') => {
    profil.ecrire({ langue });
    router.push('/bienvenue/position');
  };
  return (
    <Ecran titre="Wolof / Français" avecAccueil={false} etape={{ actuelle: 1, total: 3 }}>
      <GrosBouton icone="🇸🇳" libelle="Wolof" onPress={() => choisir('wo')} />
      <GrosBouton icone="🇫🇷" libelle="Français" onPress={() => choisir('fr')} variante="clair" />
      {/* Honnêteté : le wolof (voix et texte) n'est pas encore prêt dans cette version. */}
      <Text style={styles.note}>{"Les réponses en wolof arrivent bientôt. Pour l'instant, TerraMind répond en français."}</Text>
    </Ecran>
  );
}

const styles = StyleSheet.create({
  note: { fontSize: 16, color: couleurs.texteDoux, textAlign: 'center' },
});
