import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { type Alertes, demanderAlertes, envoyerRetour, type Reponse } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Erreur, Sources } from '@/components/Etat';
import { GrosBouton } from '@/components/GrosBouton';
import { couleurs, tailles } from '@/theme';

// Étape 6 : risques météo de la semaine (POST /v1/alert) et retour de l'agriculteur (POST /v1/feedback).
const RISQUES: Record<string, { icone: string; nom: string }> = {
  late_blight: { icone: '🌧️', nom: 'Mildiou' },
  alternaria: { icone: '🍂', nom: 'Alternariose' },
  tuta_absoluta: { icone: '🐛', nom: 'Mineuse de la tomate' },
  plutella_xylostella: { icone: '🐛', nom: 'Teigne du chou' },
};

export default function AlertesEcran() {
  const [reponse, setReponse] = useState<Reponse<Alertes> | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [retours, setRetours] = useState<Record<string, boolean>>({});

  const [essai, setEssai] = useState(0);
  useEffect(() => {
    let actif = true;
    demanderAlertes().then((r) => (r.statut === 'erreur' ? actif && setErreur(r.message.texte) : actif && setReponse(r)))
      .catch((e: Error) => actif && setErreur(e.message));
    return () => {
      actif = false;
    };
  }, [essai]);
  const charger = () => {
    setErreur(null);
    setReponse(null);
    setEssai((e) => e + 1);
  };

  if (reponse?.statut === 'culture_requise') {
    return (
      <Ecran titre="Alertes de la semaine">
        <Text style={styles.texte}>{reponse.message.texte}</Text>
        <GrosBouton icone="🌿" libelle="J'ai planté" onPress={() => router.replace('/cultures')} />
      </Ecran>
    );
  }

  const actives = reponse?.donnees.alertes.filter((a) => a.niveau !== 'aucun') ?? [];
  const repondre = (id: string, vu: 'oui' | 'non') => {
    setRetours((r) => ({ ...r, [id]: true }));
    envoyerRetour(id, vu).catch(() => undefined); // un retour perdu ne bloque pas l'agriculteur
  };

  return (
    <Ecran titre="Alertes de la semaine">
      {erreur ? <Erreur texte={erreur} onReessayer={charger} /> : null}
      {!erreur && !reponse ? <Chargement icone="🌦️" texte="Je regarde la météo de ton champ…" /> : null}
      {reponse ? (
        <>
          {actives.length === 0 ? (
            <View style={[styles.carte, { alignItems: 'center' }]}>
              <Text style={styles.grandeIcone}>😌</Text>
              <Text style={styles.texte}>{reponse.message.texte}</Text>
            </View>
          ) : null}
          {actives.map((a) => (
            <View key={a.id} style={styles.carte}>
              <View style={styles.haut}>
                <Text style={styles.grandeIcone}>{RISQUES[a.risque]?.icone ?? '⚠️'}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.nom}>{RISQUES[a.risque]?.nom ?? a.risque}</Text>
                  <Text style={styles.niveau}>{a.niveau === 'favorable' ? 'Conditions favorables' : 'À surveiller'}</Text>
                </View>
              </View>
              <Text style={styles.texte}>{a.conseil}</Text>
              {retours[a.id] ? (
                <Text style={styles.merci}>{"Merci, c'est noté."}</Text>
              ) : (
                <View style={styles.boutons}>
                  <View style={{ flex: 1 }}><GrosBouton icone="👀" libelle="J'ai vu" onPress={() => repondre(a.id, 'oui')} /></View>
                  <View style={{ flex: 1 }}><GrosBouton icone="🙈" libelle="Rien vu" onPress={() => repondre(a.id, 'non')} variante="clair" /></View>
                </View>
              )}
            </View>
          ))}
          <Text style={styles.periode}>
            Météo du {reponse.donnees.meteo.periode[0]} au {reponse.donnees.meteo.periode[1]} (NASA POWER).
          </Text>
          <Sources sources={reponse.sources} />
        </>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  carte: { backgroundColor: couleurs.blanc, borderRadius: tailles.rayon, padding: 16, gap: 12 },
  haut: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  grandeIcone: { fontSize: 48 },
  nom: { fontSize: 22, fontWeight: '800', color: couleurs.texte },
  niveau: { fontSize: 16, fontWeight: '700', color: couleurs.ocre },
  texte: { fontSize: 19, color: couleurs.texte, lineHeight: 27, textAlign: 'center' },
  boutons: { flexDirection: 'row', gap: 8 },
  merci: { fontSize: 17, color: couleurs.vert, fontWeight: '700', textAlign: 'center' },
  periode: { fontSize: 14, color: couleurs.texteDoux, textAlign: 'center' },
});
