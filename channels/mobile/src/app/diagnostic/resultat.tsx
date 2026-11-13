import { router, useLocalSearchParams } from 'expo-router';
import { ArrowsClockwise, FirstAidKit, Question, SealCheck, ShieldCheck, Warning } from 'phosphor-react-native';
import { useEffect, useState } from 'react';
import { Animated, Easing, Image, StyleSheet, View } from 'react-native';

import { type Diagnostic, diagnostiquer, type Reponse } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Erreur, Sources } from '@/components/Etat';
import { Apparition, Bouton, Carte, Pastille, T } from '@/components/ui';
import { couleurs, polices } from '@/theme';

/** Ligne de balayage qui parcourt la photo pendant l'analyse. */
function Balayage() {
  const [v] = useState(() => new Animated.Value(0));
  const [hauteur, setHauteur] = useState(0);
  useEffect(() => {
    const boucle = Animated.loop(Animated.timing(v, { toValue: 1, duration: 1500, easing: Easing.inOut(Easing.quad), useNativeDriver: true }));
    boucle.start();
    return () => boucle.stop();
  }, [v]);
  return (
    <View style={StyleSheet.absoluteFill} onLayout={(e) => setHauteur(e.nativeEvent.layout.height)}>
      <View style={[StyleSheet.absoluteFill, { backgroundColor: 'rgba(31,77,58,0.25)' }]} />
      <Animated.View style={[styles.ligne, { transform: [{ translateY: v.interpolate({ inputRange: [0, 1], outputRange: [0, Math.max(hauteur - 4, 0)] }) }] }]} />
    </View>
  );
}

function Jauge({ valeur }: { valeur: number }) {
  return (
    <View style={{ gap: 6 }}>
      <View style={styles.jaugeTete}>
        <T v="petit">Confiance du modèle</T>
        <T v="corpsGras">{Math.round(valeur * 100)} %</T>
      </View>
      <View style={styles.jauge}><View style={[styles.jaugeRemplie, { width: `${Math.round(valeur * 100)}%` }]} /></View>
    </View>
  );
}

// Étape 5b : résultat. Sous le seuil de confiance, on le dit et on n'annonce aucune maladie.
export default function Resultat() {
  const { uri, type } = useLocalSearchParams<{ uri: string; type?: string }>();
  const [reponse, setReponse] = useState<Reponse<Diagnostic> | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [essai, setEssai] = useState(0);
  useEffect(() => {
    let actif = true;
    diagnostiquer(uri, type || null)
      .then((r) => (r.statut === 'erreur' ? actif && setErreur(r.message.texte) : actif && setReponse(r)))
      .catch((e: Error) => actif && setErreur(e.message));
    return () => {
      actif = false;
    };
  }, [essai, uri, type]);
  const analyser = () => {
    setErreur(null);
    setReponse(null);
    setEssai((e) => e + 1);
  };

  const incertain = reponse?.statut === 'incertain';
  const top = reponse?.donnees.predictions?.[0];
  const sain = top?.categorie === 'sain';
  const etat = incertain
    ? { Icone: Question, titre: 'Je ne suis pas sûr', fond: couleurs.soleilClair, couleur: '#7A5A12' }
    : sain ? { Icone: SealCheck, titre: top?.libelle ?? '', fond: couleurs.pousse, couleur: couleurs.foret }
      : { Icone: Warning, titre: top?.libelle ?? '', fond: couleurs.terreClair, couleur: couleurs.terre };
  const enCours = !erreur && !reponse;

  return (
    <Ecran titre={enCours ? 'J’examine ta feuille…' : 'Résultat'}>
      <View style={styles.cadrePhoto}>
        <Image source={{ uri }} style={styles.photo} accessibilityLabel="Ta photo" />
        {enCours ? <Balayage /> : null}
      </View>
      {erreur ? <Erreur texte={erreur} onReessayer={analyser} /> : null}
      {reponse && top ? (
        <>
          <Apparition ordre={0}>
            <View style={[styles.verdict, { backgroundColor: etat.fond }]}>
              <Pastille Icone={etat.Icone} couleur={etat.couleur} fond={couleurs.carte} taille={56} />
              <View style={{ flex: 1 }}>
                <T v="etiquette" style={{ color: etat.couleur }}>{incertain ? 'Résultat incertain' : sain ? 'Bonne nouvelle' : 'Cela ressemble à'}</T>
                <T style={[styles.verdictTitre, { color: couleurs.encre }]}>{etat.titre}</T>
              </View>
            </View>
          </Apparition>
          <Apparition ordre={1}><T v="corps">{reponse.message.texte}</T></Apparition>
          {!incertain && !sain ? <Apparition ordre={2}><Carte><Jauge valeur={top.confiance} /></Carte></Apparition> : null}
          {reponse.donnees.conseils ? (
            <Apparition ordre={3}>
              <Carte>
                <View style={styles.conseilsTete}>
                  <Pastille Icone={ShieldCheck} taille={40} />
                  <T v="sousTitre" style={{ flex: 1 }}>Ce que tu peux faire</T>
                </View>
                {reponse.donnees.conseils.texte.split('\n').map((l) => (
                  <T key={l} v="corps" style={{ fontSize: 17 }}>{l.replace(/^-\s*/, '• ')}</T>
                ))}
              </Carte>
            </Apparition>
          ) : null}
          {!sain ? (
            <Apparition ordre={4} style={styles.agent}>
              <FirstAidKit size={24} color={couleurs.terre} weight="duotone" />
              <T v="petit" style={{ flex: 1 }}>Pour un traitement, montre ta plante à un agent agricole. TerraMind ne donne ni produit ni dose.</T>
            </Apparition>
          ) : null}
          <Sources sources={reponse.sources} />
        </>
      ) : null}
      <Bouton libelle="Reprendre la photo" Icone={ArrowsClockwise} onPress={() => router.back()} variante="clair" />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  cadrePhoto: { borderRadius: 28, overflow: 'hidden', backgroundColor: couleurs.pousse },
  photo: { width: '100%', aspectRatio: 1.15 },
  ligne: { position: 'absolute', left: 0, right: 0, height: 4, backgroundColor: couleurs.soleil, shadowColor: couleurs.soleil, shadowOpacity: 0.9, shadowRadius: 10 },
  verdict: { flexDirection: 'row', alignItems: 'center', gap: 14, borderRadius: 24, padding: 16 },
  verdictTitre: { fontFamily: polices.titre, fontSize: 26, letterSpacing: -0.4 },
  jaugeTete: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  jauge: { height: 10, borderRadius: 5, backgroundColor: couleurs.sableFonce, overflow: 'hidden' },
  jaugeRemplie: { height: 10, borderRadius: 5, backgroundColor: couleurs.soleil },
  conseilsTete: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  agent: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 4 },
});
