import { router } from 'expo-router';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 5b : résultat du diagnostic.
export default function Resultat() {
  return (
    <Ecran titre="Résultat">
      <AVenir
        texte="Si le modèle est sûr : nom, photo de référence, conseil audio wolof, source. Sinon (sous seuil_incertain) : le dire clairement, proposer de reprendre la photo ou les questions_suivi."
        api="POST /v1/diagnose"
      />
      <GrosBouton icone="🔁" libelle="Reprendre la photo" onPress={() => router.back()} variante="clair" />
    </Ecran>
  );
}
