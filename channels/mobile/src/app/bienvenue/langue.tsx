import { router } from 'expo-router';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 1a : choix de la langue, en tout premier (docs/maquettes/references-ecrans.md).
export default function Langue() {
  const suivant = () => router.push('/bienvenue/position');
  return (
    <Ecran titre="Wolof / Français" avecAccueil={false} etape={{ actuelle: 1, total: 3 }}>
      <GrosBouton icone="🇸🇳" libelle="Wolof" onPress={suivant} />
      <GrosBouton icone="🇫🇷" libelle="Français" onPress={suivant} variante="clair" />
      <AVenir texte="Chaque bouton se présente à voix haute ; le choix est enregistré sur le téléphone." />
    </Ecran>
  );
}
