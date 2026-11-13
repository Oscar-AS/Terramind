import { router } from 'expo-router';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 4 : la culture et sa date de repiquage, qui déclenchent les alertes.
export default function Cultures() {
  return (
    <Ecran titre="Mes cultures">
      <AVenir texte="Choisir la culture en photo, puis la date de repiquage sur un calendrier simple (jour, mois). Aucune saisie de fréquence." />
      {/* Les notifications sont demandées ici : c'est là qu'on comprend à quoi elles servent. */}
      <GrosBouton icone="✅" libelle="C'est noté" onPress={() => router.push('/notifications')} />
    </Ecran>
  );
}
