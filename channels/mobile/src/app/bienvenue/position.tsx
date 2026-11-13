import * as Location from 'expo-location';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Chargement } from '@/components/Etat';
import { FeuilleGlissante } from '@/components/FeuilleGlissante';
import { GrosBouton } from '@/components/GrosBouton';
import { profil, ZONES } from '@/profil';
import { couleurs } from '@/theme';

// Étape 1b : expliquer AVANT la fenêtre d'autorisation du système, avec un plan B (zones pilotes).
export default function Position() {
  const [zonesOuvertes, setZonesOuvertes] = useState(false);
  const [recherche, setRecherche] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const suivant = () => {
    setZonesOuvertes(false);
    router.push('/bienvenue/champ');
  };

  const gps = async () => {
    setMessage(null);
    const { granted } = await Location.requestForegroundPermissionsAsync();
    if (!granted) {
      setMessage("Pas de souci : choisis ta zone dans la liste.");
      setZonesOuvertes(true);
      return;
    }
    setRecherche(true);
    try {
      const p = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      // Arrondi à 0,01° (environ 1 km) : assez pour le sol et la météo, sans localiser la parcelle.
      profil.ecrire({ position: { lat: Math.round(p.coords.latitude * 100) / 100,
                                  lon: Math.round(p.coords.longitude * 100) / 100 } });
      suivant();
    } catch {
      setMessage("Je n'ai pas trouvé ta position. Choisis ta zone dans la liste.");
      setZonesOuvertes(true);
    } finally {
      setRecherche(false);
    }
  };

  if (recherche) {
    return (
      <Ecran titre="Où est ton champ ?" avecAccueil={false} etape={{ actuelle: 2, total: 3 }}>
        <Chargement icone="📍" texte="Je cherche ta position…" />
      </Ecran>
    );
  }

  return (
    <Ecran titre="Où est ton champ ?" avecAccueil={false} etape={{ actuelle: 2, total: 3 }}>
      <Text style={styles.explication}>
        Ta position sert seulement à connaître ton sol et ta météo. Mets-toi dans ton champ.
      </Text>
      {message ? <Text style={styles.message}>{message}</Text> : null}
      <GrosBouton icone="📍" libelle="Je suis dans mon champ" onPress={gps} />
      <GrosBouton icone="🗺️" libelle="Choisir ma zone" onPress={() => setZonesOuvertes(true)} variante="clair" />
      <FeuilleGlissante visible={zonesOuvertes} onFermer={() => setZonesOuvertes(false)} titre="Choisis ta zone">
        {ZONES.map((z) => (
          <GrosBouton
            key={z.nom}
            icone="📌"
            libelle={z.nom}
            variante="clair"
            onPress={() => {
              profil.ecrire({ position: { lat: z.lat, lon: z.lon, nom: z.nom } });
              suivant();
            }}
          />
        ))}
      </FeuilleGlissante>
    </Ecran>
  );
}

const styles = StyleSheet.create({
  explication: { fontSize: 20, color: couleurs.texte, textAlign: 'center', lineHeight: 28 },
  message: { fontSize: 17, color: couleurs.ocre, textAlign: 'center' },
});
