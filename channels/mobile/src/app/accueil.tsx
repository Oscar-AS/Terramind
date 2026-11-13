import { router } from 'expo-router';

import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 2 : trois grandes tuiles, rien de plus.
export default function Accueil() {
  return (
    <Ecran titre="TerraMind" avecAccueil={false}>
      {/* Bandeau d'alerte : n'apparaît que s'il y a une alerte cette semaine. */}
      <GrosBouton icone="🔔" libelle="Alertes de la semaine" onPress={() => router.push('/alertes')} variante="clair" />
      <GrosBouton icone="🌱" libelle="Que planter ?" onPress={() => router.push('/plan')} />
      <GrosBouton icone="📷" libelle="Ma plante est malade" onPress={() => router.push('/diagnostic')} />
      <GrosBouton icone="🎤" libelle="Poser une question" onPress={() => router.push('/question')} />
      <AVenir texte="Le bandeau d'alertes ne s'affichera que s'il y a une alerte (pas d'élément grisé)." />
    </Ecran>
  );
}
