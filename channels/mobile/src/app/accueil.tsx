import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';
import { CULTURES, profil } from '@/profil';
import { couleurs } from '@/theme';

// Étape 2 : trois grandes tuiles. La tuile « Alertes » n'apparaît que si une culture est déclarée
// (pas d'élément grisé, cf. références d'écrans).
export default function Accueil() {
  const [p, setP] = useState(profil.lire());
  useFocusEffect(useCallback(() => setP(profil.lire()), []));
  const culture = CULTURES.find((c) => c.id === p.culture);

  return (
    <Ecran titre="TerraMind" avecAccueil={false}>
      {p.position?.nom ? <Text style={styles.zone}>📌 {p.position.nom}</Text> : null}
      {culture ? (
        <GrosBouton
          icone="🔔"
          libelle={`Alertes : ${culture.libelle.toLowerCase()}`}
          onPress={() => router.push('/alertes')}
          variante="clair"
        />
      ) : null}
      <GrosBouton icone="🌱" libelle="Que planter ?" onPress={() => router.push('/plan')} />
      <GrosBouton icone="📷" libelle="Ma plante est malade" onPress={() => router.push('/diagnostic')} />
      <GrosBouton icone="🎤" libelle="Poser une question" onPress={() => router.push('/question')} />
      <GrosBouton icone="🌿" libelle={culture ? 'Changer ma culture' : "J'ai planté"} onPress={() => router.push('/cultures')} variante="clair" />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  zone: { fontSize: 16, color: couleurs.texteDoux, textAlign: 'center' },
});
