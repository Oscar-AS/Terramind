import { router } from 'expo-router';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 5a : prise de photo d'une feuille.
export default function Photo() {
  return (
    <Ecran titre="Ma plante est malade">
      <AVenir texte="Appareil photo plein écran, cadre guide « mets une feuille dedans » (voix), flash en haut, galerie en option secondaire." />
      <GrosBouton icone="📸" libelle="Prendre la photo" onPress={() => router.push('/diagnostic/resultat')} />
    </Ecran>
  );
}
