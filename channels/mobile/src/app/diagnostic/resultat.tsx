import { router, useLocalSearchParams } from 'expo-router';
import {
  CameraPlus, FirstAidKit, FrameCorners, type Icon, Info, Leaf, Question, SealCheck, ShieldCheck, Sun, Warning,
} from 'phosphor-react-native';
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

/** Consignes pour une meilleure photo : une icône, une phrase courte. */
const CONSIGNES: { Icone: Icon; texte: string }[] = [
  { Icone: Leaf, texte: 'Une seule feuille malade' },
  { Icone: FrameCorners, texte: 'De près : la feuille remplit la photo' },
  { Icone: Sun, texte: 'À la lumière du jour, sans ombre' },
];

// Étape 5b : résultat. Le verdict d'abord, puis ce que l'agriculteur doit faire maintenant.
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
  const reprendre = () => router.back();

  // Pendant l'analyse : la photo en grand, balayée (on montre que ça travaille).
  if (!erreur && !reponse) {
    return (
      <Ecran titre="J’examine ta feuille…">
        <View style={styles.cadrePhoto}>
          <Image source={{ uri }} style={styles.photo} accessibilityLabel="Ta photo" />
          <Balayage />
        </View>
      </Ecran>
    );
  }

  const incertain = reponse?.statut === 'incertain';
  const top = reponse?.donnees.predictions?.[0];
  const sain = top?.categorie === 'sain';
  const etat = incertain
    ? { Icone: Question, sur: 'Je n’ai pas pu lire ta photo', titre: 'Reprends la photo', fond: couleurs.soleilClair, couleur: '#7A5A12' }
    : sain ? { Icone: SealCheck, sur: 'Bonne nouvelle', titre: top?.libelle ?? '', fond: couleurs.pousse, couleur: couleurs.foret }
      : { Icone: Warning, sur: 'Cela ressemble à', titre: top?.libelle ?? '', fond: couleurs.terreClair, couleur: couleurs.terre };

  return (
    <Ecran titre="Résultat">
      {erreur ? <Erreur texte={erreur} onReessayer={analyser} /> : null}
      {reponse && top ? (
        <>
          {/* 1. Le verdict sur sa propre photo, en grand : l'agriculteur reconnaît sa feuille. */}
          <Apparition ordre={0}>
            <View style={[styles.verdict, { backgroundColor: etat.fond }]}>
              <View>
                <Image source={{ uri }} style={styles.photoVerdict} resizeMode="cover" accessibilityLabel="Ta photo" />
                <View style={[styles.badgeVignette, { backgroundColor: etat.couleur }]}>
                  <etat.Icone size={22} color={couleurs.blanc} weight="bold" />
                </View>
              </View>
              <View style={{ gap: 2, paddingHorizontal: 4 }}>
                <T v="etiquette" style={{ color: etat.couleur }}>{etat.sur}</T>
                <T style={styles.verdictTitre}>{etat.titre}</T>
              </View>
            </View>
          </Apparition>

          {/* 2a. Incertain : comment faire une meilleure photo, puis le bouton pour recommencer. */}
          {incertain ? (
            <>
              <Apparition ordre={1}>
                <Carte>
                  <T v="corpsGras">Pour que je puisse t’aider :</T>
                  {CONSIGNES.map((c) => (
                    <View key={c.texte} style={styles.consigne}>
                      <Pastille Icone={c.Icone} taille={44} />
                      <T v="corps" style={{ flex: 1 }}>{c.texte}</T>
                    </View>
                  ))}
                </Carte>
              </Apparition>
              <Apparition ordre={2}><Bouton libelle="Reprendre la photo" Icone={CameraPlus} onPress={reprendre} /></Apparition>
              <Apparition ordre={3} style={styles.agent}>
                <FirstAidKit size={24} color={couleurs.terre} weight="duotone" />
                <T v="petit" style={{ flex: 1 }}>Si la plante va mal, montre-la aussi à un agent agricole (ANCAR, service de l’agriculture).</T>
              </Apparition>
            </>
          ) : (
            <>
              {/* 2b. Reconnu : ce que c'est en mots simples, la confiance, puis ce qu'il faut faire. */}
              {!sain ? (
                <Apparition ordre={1}>
                  <Carte>
                    <View style={styles.conseilsTete}>
                      <Pastille Icone={Info} taille={40} />
                      <T v="sousTitre" style={{ flex: 1 }}>C’est quoi ?</T>
                    </View>
                    {reponse.donnees.explication ? (
                      reponse.donnees.explication.texte.split('\n').map((l) => (
                        <T key={l} v="corps" style={{ fontSize: 17 }}>{l.replace(/^-\s*/, '')}</T>
                      ))
                    ) : (
                      <T v="corps" style={{ fontSize: 17 }}>Je n’ai pas encore d’explication simple sur ce problème. Montre ta plante à un agent agricole.</T>
                    )}
                  </Carte>
                </Apparition>
              ) : null}
              {!sain ? (
                <Apparition ordre={1}>
                  <Carte>
                    <T v="corps">Ce n’est qu’une première indication, pas un diagnostic sûr.</T>
                    <Jauge valeur={top.confiance} />
                  </Carte>
                </Apparition>
              ) : <Apparition ordre={1}><T v="corps">{reponse.message.texte}</T></Apparition>}
              {reponse.donnees.conseils ? (
                <Apparition ordre={2}>
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
                <Apparition ordre={3} style={styles.agent}>
                  <FirstAidKit size={24} color={couleurs.terre} weight="duotone" />
                  <T v="petit" style={{ flex: 1 }}>Pour un traitement, montre ta plante à un agent agricole. TerraMind ne donne ni produit ni dose.</T>
                </Apparition>
              ) : null}
              <Bouton libelle="Photographier une autre feuille" Icone={CameraPlus} onPress={reprendre} variante="clair" />
            </>
          )}
          <Sources sources={reponse.sources} />
        </>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  cadrePhoto: { borderRadius: 28, overflow: 'hidden', backgroundColor: couleurs.pousse },
  photo: { width: '100%', aspectRatio: 1 },
  ligne: { position: 'absolute', left: 0, right: 0, height: 4, backgroundColor: couleurs.soleil, shadowColor: couleurs.soleil, shadowOpacity: 0.9, shadowRadius: 10 },
  verdict: { gap: 14, borderRadius: 24, padding: 12, paddingBottom: 16 },
  photoVerdict: { width: '100%', aspectRatio: 4 / 3, borderRadius: 18, backgroundColor: couleurs.carte },
  badgeVignette: {
    position: 'absolute', right: 10, bottom: 10, width: 40, height: 40, borderRadius: 20, alignItems: 'center',
    justifyContent: 'center', borderWidth: 3, borderColor: couleurs.sable,
  },
  verdictTitre: { fontFamily: polices.titre, fontSize: 25, letterSpacing: -0.4, color: couleurs.encre },
  consigne: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  jaugeTete: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  jauge: { height: 10, borderRadius: 5, backgroundColor: couleurs.sableFonce, overflow: 'hidden' },
  jaugeRemplie: { height: 10, borderRadius: 5, backgroundColor: couleurs.soleil },
  conseilsTete: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  agent: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 4 },
});
