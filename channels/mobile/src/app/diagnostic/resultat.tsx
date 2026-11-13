import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

import { type Diagnostic, diagnostiquer, type Reponse } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Erreur, Sources } from '@/components/Etat';
import { GrosBouton } from '@/components/GrosBouton';
import { couleurs, tailles } from '@/theme';

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

  return (
    <Ecran titre="Résultat">
      <Image source={{ uri }} style={styles.photo} accessibilityLabel="Ta photo" />
      {erreur ? <Erreur texte={erreur} onReessayer={analyser} /> : null}
      {!erreur && !reponse ? <Chargement icone="🔎" texte="J'examine ta feuille…" /> : null}
      {reponse && top ? (
        <>
          <View style={[styles.bandeau, { backgroundColor: incertain ? couleurs.ocre : sain ? couleurs.vert : couleurs.rouge }]}>
            <Text style={styles.bandeauIcone}>{incertain ? '🤔' : sain ? '✅' : '⚠️'}</Text>
            <Text style={styles.bandeauTexte}>{incertain ? 'Je ne suis pas sûr' : top.libelle}</Text>
          </View>
          <Text style={styles.texte}>{reponse.message.texte}</Text>
          {!incertain && !sain ? (
            <Text style={styles.confiance}>Confiance du modèle : {Math.round(top.confiance * 100)} %</Text>
          ) : null}
          <Sources sources={reponse.sources} />
        </>
      ) : null}
      <GrosBouton icone="🔁" libelle="Reprendre la photo" onPress={() => router.back()} variante="clair" />
    </Ecran>
  );
}

const styles = StyleSheet.create({
  photo: { width: '100%', aspectRatio: 1, borderRadius: tailles.rayon, backgroundColor: couleurs.vertClair },
  bandeau: { flexDirection: 'row', alignItems: 'center', gap: 12, borderRadius: tailles.rayon, padding: 16 },
  bandeauIcone: { fontSize: 36 },
  bandeauTexte: { flex: 1, fontSize: 24, fontWeight: '800', color: couleurs.blanc },
  texte: { fontSize: 19, color: couleurs.texte, lineHeight: 27 },
  confiance: { fontSize: 15, color: couleurs.texteDoux },
});
