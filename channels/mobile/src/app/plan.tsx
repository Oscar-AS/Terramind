import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { type Adaptation, type CulturePlan, demanderPlan, type Plan, type Reponse } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Erreur, Sources } from '@/components/Etat';
import { GrosBouton } from '@/components/GrosBouton';
import { CULTURES } from '@/profil';
import { couleurs, tailles } from '@/theme';

// Étape 3 : que planter ici, et quand (POST /v1/plan).
// Badge = couleur ET icône ET mot (jamais la couleur seule).
const BADGES: Record<Adaptation, { icone: string; mot: string; fond: string; texte: string }> = {
  conseillee: { icone: '✅', mot: 'Conseillée', fond: couleurs.vert, texte: couleurs.blanc },
  possible: { icone: '⚠️', mot: 'Possible', fond: couleurs.ocre, texte: couleurs.blanc },
  deconseillee: { icone: '⛔', mot: 'Pas maintenant', fond: couleurs.vertClair, texte: couleurs.texte },
};

function Carte({ c }: { c: CulturePlan }) {
  const b = BADGES[c.adaptation];
  const icone = CULTURES.find((x) => x.id === c.culture)?.icone ?? '🌱';
  return (
    <View style={[styles.carte, c.adaptation === 'deconseillee' && styles.carteEteinte]}>
      <View style={styles.carteHaut}>
        <Text style={styles.carteIcone}>{icone}</Text>
        <View style={{ flex: 1, gap: 6 }}>
          <Text style={styles.carteNom}>{c.libelle}</Text>
          <View style={[styles.badge, { backgroundColor: b.fond }]}>
            <Text style={[styles.badgeTexte, { color: b.texte }]}>{b.icone} {b.mot}</Text>
          </View>
        </View>
      </View>
      <Text style={styles.ligne}>🗓️ {c.periode_semis}</Text>
      <Text style={styles.ligne}>⏳ {c.cycle_jours[0]} à {c.cycle_jours[1]} jours au champ</Text>
      {c.raisons.map((r) => <Text key={r} style={styles.raison}>{r}</Text>)}
      {c.avertissements.map((a) => <Text key={a} style={styles.avertissement}>⚠️ {a}</Text>)}
    </View>
  );
}

export default function PlanEcran() {
  const [reponse, setReponse] = useState<Reponse<Plan> | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  const [essai, setEssai] = useState(0);
  useEffect(() => {
    let actif = true;
    demanderPlan().then((r) => (r.statut === 'erreur' ? actif && setErreur(r.message.texte) : actif && setReponse(r)))
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

  return (
    <Ecran titre="Que planter ?">
      {erreur ? <Erreur texte={erreur} onReessayer={charger} /> : null}
      {!erreur && !reponse ? <Chargement icone="🌱" texte="Je regarde ton sol et la saison…" /> : null}
      {reponse ? (
        <>
          <Text style={styles.resume}>{reponse.message.texte}</Text>
          {reponse.donnees.sol.texture ? (
            <Text style={styles.sol}>
              🟫 Ton sol : {reponse.donnees.sol.sable_pct} % de sable, pH {reponse.donnees.sol.ph}
            </Text>
          ) : null}
          {reponse.donnees.cultures.map((c) => <Carte key={c.culture} c={c} />)}
          <GrosBouton icone="🌿" libelle="J'ai planté" onPress={() => router.push('/cultures')} />
          <Sources sources={reponse.sources} />
        </>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  resume: { fontSize: 20, fontWeight: '700', color: couleurs.texte },
  sol: { fontSize: 16, color: couleurs.texteDoux },
  carte: { backgroundColor: couleurs.blanc, borderRadius: tailles.rayon, padding: 16, gap: 8 },
  carteEteinte: { opacity: 0.7 },
  carteHaut: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  carteIcone: { fontSize: 44 },
  carteNom: { fontSize: 22, fontWeight: '800', color: couleurs.texte },
  badge: { alignSelf: 'flex-start', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4 },
  badgeTexte: { fontSize: 15, fontWeight: '700' },
  ligne: { fontSize: 16, color: couleurs.texte },
  raison: { fontSize: 16, color: couleurs.texteDoux },
  avertissement: { fontSize: 16, color: couleurs.rouge },
});
