import { router } from 'expo-router';
import { useState } from 'react';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { FeuilleGlissante } from '@/components/FeuilleGlissante';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 1b : expliquer AVANT la fenêtre d'autorisation du système, avec un plan B.
export default function Position() {
  const [carteOuverte, setCarteOuverte] = useState(false);
  const suivant = () => {
    setCarteOuverte(false);
    router.push('/bienvenue/champ');
  };
  return (
    <Ecran titre="Où est ton champ ?" avecAccueil={false} etape={{ actuelle: 2, total: 3 }}>
      <AVenir texte="Explication vocale : la position sert seulement à connaître ton sol et ta météo. Puis fenêtre d'autorisation GPS du téléphone." />
      <GrosBouton icone="📍" libelle="Je suis dans mon champ" onPress={suivant} />
      <GrosBouton
        icone="🗺️"
        libelle="Choisir sur la carte"
        onPress={() => setCarteOuverte(true)}
        variante="clair"
      />
      <FeuilleGlissante
        visible={carteOuverte}
        onFermer={() => setCarteOuverte(false)}
        titre="Choisis ta zone">
        <AVenir texte="Carte de la zone pilote : toucher l'endroit du champ." />
        <GrosBouton icone="✅" libelle="C'est ici" onPress={suivant} />
      </FeuilleGlissante>
    </Ecran>
  );
}
