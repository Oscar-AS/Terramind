import * as Location from 'expo-location';
import { router } from 'expo-router';
import { Crosshair, MapPin, MapTrifold } from 'phosphor-react-native';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Ecran } from '@/components/Ecran';
import { Chargement } from '@/components/Etat';
import { FeuilleGlissante } from '@/components/FeuilleGlissante';
import { Apparition, Bouton, Carte, Pastille, T } from '@/components/ui';
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
      setMessage('Pas de souci : choisis ta zone dans la liste.');
      setZonesOuvertes(true);
      return;
    }
    setRecherche(true);
    try {
      const p = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      // Arrondi à 0,01° (environ 1 km) : assez pour le sol et la météo, sans localiser la parcelle.
      profil.ecrire({ position: { lat: Math.round(p.coords.latitude * 100) / 100, lon: Math.round(p.coords.longitude * 100) / 100 } });
      suivant();
    } catch {
      setMessage("Je n'ai pas trouvé ta position. Choisis ta zone dans la liste.");
      setZonesOuvertes(true);
    } finally {
      setRecherche(false);
    }
  };

  return (
    <Ecran titre="Où est ton champ ?" avecRetour={false} etape={{ actuelle: 2, total: 3 }}>
      {recherche ? <Chargement Icone={Crosshair} texte="Je cherche ta position…" /> : (
        <>
          <Apparition ordre={1}>
            <Carte style={styles.explication}>
              <Pastille Icone={MapPin} taille={56} />
              <T v="corps" style={{ flex: 1 }}>Ta position sert seulement à connaître ton sol et ta météo. Mets-toi dans ton champ.</T>
            </Carte>
          </Apparition>
          {message ? <T v="corpsGras" style={{ color: couleurs.terre }}>{message}</T> : null}
          <Apparition ordre={2}><Bouton libelle="Je suis dans mon champ" sousTitre="Utiliser le GPS" Icone={Crosshair} onPress={gps} /></Apparition>
          <Apparition ordre={3}><Bouton libelle="Choisir ma zone" sousTitre="Rufisque, Thiès, Tivaouane, Kébémer" Icone={MapTrifold} onPress={() => setZonesOuvertes(true)} variante="clair" /></Apparition>
        </>
      )}
      <FeuilleGlissante visible={zonesOuvertes} onFermer={() => setZonesOuvertes(false)} titre="Choisis ta zone">
        <View style={{ gap: 10 }}>
          {ZONES.map((z) => (
            <Bouton key={z.nom} libelle={z.nom} Icone={MapPin} variante="clair"
              onPress={() => { profil.ecrire({ position: { lat: z.lat, lon: z.lon, nom: z.nom } }); suivant(); }} />
          ))}
        </View>
      </FeuilleGlissante>
    </Ecran>
  );
}

const styles = StyleSheet.create({
  explication: { flexDirection: 'row', alignItems: 'center', gap: 14 },
});
