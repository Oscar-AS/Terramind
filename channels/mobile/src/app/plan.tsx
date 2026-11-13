import { router } from 'expo-router';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 3 : que planter ici, et quand.
export default function Plan() {
  return (
    <Ecran titre="Que planter ?">
      <AVenir
        texte="Animation pendant l'analyse du sol, puis une carte par culture : photo, badge conseillée / possible / à éviter (couleur ET icône), période de semis, 🔊 raisons et avertissements."
        api="POST /v1/plan"
      />
      <GrosBouton icone="🌿" libelle="J'ai planté" onPress={() => router.push('/cultures')} />
    </Ecran>
  );
}
