import { router } from 'expo-router';
import { CalendarBlank } from 'phosphor-react-native/src/icons/CalendarBlank';
import { CheckCircle } from 'phosphor-react-native/src/icons/CheckCircle';
import { Hourglass } from 'phosphor-react-native/src/icons/Hourglass';
import { MinusCircle } from 'phosphor-react-native/src/icons/MinusCircle';
import { Plant } from 'phosphor-react-native/src/icons/Plant';
import { Warning } from 'phosphor-react-native/src/icons/Warning';
import { WarningCircle } from 'phosphor-react-native/src/icons/WarningCircle';
import { useEffect, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { type Adaptation, type CulturePlan, demanderPlan, type PhraseWolof, type Plan, type Reponse } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Erreur, Sources } from '@/components/Etat';
import { Apparition, Badge, Bouton, Carte, T } from '@/components/ui';
import { BlocWolof, BoutonEcouter } from '@/components/Voix';
import { CULTURES } from '@/profil';
import { nombreFr } from '@/format';
import { couleurs } from '@/theme';

// Étape 3 : que planter ici, et quand (POST /v1/plan).
const BADGES: Record<Adaptation, { Icone: typeof CheckCircle; mot: string; couleur: string; fond: string }> = {
  conseillee: { Icone: CheckCircle, mot: 'Conseillée', couleur: couleurs.foret, fond: couleurs.pousse },
  possible: { Icone: WarningCircle, mot: 'Possible', couleur: '#7A5A12', fond: couleurs.soleilClair },
  deconseillee: { Icone: MinusCircle, mot: 'Pas maintenant', couleur: couleurs.encreDouce, fond: couleurs.sableFonce },
};

function Ligne({ Icone, texte }: { Icone: typeof CheckCircle; texte: string }) {
  return (
    <View style={styles.ligne}>
      <Icone size={20} color={couleurs.encreDouce} weight="duotone" />
      <T v="corps" style={{ flex: 1, fontSize: 16 }}>{texte}</T>
    </View>
  );
}

function CarteCulture({ c, ordre }: { c: CulturePlan; ordre: number }) {
  const b = BADGES[c.adaptation];
  const icone = CULTURES.find((x) => x.id === c.culture)?.icone ?? '🌱';
  const eteinte = c.adaptation === 'deconseillee';
  return (
    <Apparition ordre={ordre}>
      <Carte style={eteinte && styles.eteinte}>
        <View style={styles.tete}>
          <View style={[styles.vignette, { backgroundColor: b.fond }]}><T style={{ fontSize: 34 }}>{icone}</T></View>
          <View style={{ flex: 1, gap: 6 }}>
            <T v="sousTitre">{c.libelle}</T>
            <Badge Icone={b.Icone} texte={b.mot} couleur={b.couleur} fond={b.fond} />
          </View>
        </View>
        {c.wo ? (
          <View style={styles.wolof}>
            <T v="corpsGras">{c.wo.texte_wo}</T>
            <BoutonEcouter phrases={[c.wo]} libelle="Écouter" />
          </View>
        ) : null}
        {!eteinte ? (
          <>
            <Ligne Icone={CalendarBlank} texte={c.periode_semis} />
            <Ligne Icone={Hourglass} texte={`${c.cycle_jours[0]} à ${c.cycle_jours[1]} jours au champ`} />
            {c.raisons.slice(1).map((r) => <T key={r} v="petit">{r}</T>)}
          </>
        ) : <T v="petit">{c.periode_semis}</T>}
        {c.avertissements.map((a) => (
          <View key={a} style={styles.avertissement}>
            <Warning size={20} color={couleurs.terre} weight="duotone" />
            <T v="corps" style={{ flex: 1, fontSize: 16 }}>{a}</T>
          </View>
        ))}
      </Carte>
    </Apparition>
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

  const sol = reponse?.donnees.sol;
  const cultures = reponse?.donnees.cultures ?? [];
  const wolof = reponse?.message.wolof;
  // Tout l'écran à l'écoute, comme le bot : l'introduction, puis chaque culture conseillée ou possible.
  const voix = useMemo<PhraseWolof[] | undefined>(() => (wolof ? [
    ...wolof.slice(0, 1),
    ...(reponse?.donnees.cultures ?? []).filter((c) => c.adaptation !== 'deconseillee' && c.wo).map((c) => c.wo as PhraseWolof),
    ...wolof.slice(1),
  ] : undefined), [wolof, reponse]);
  return (
    <Ecran titre="Que planter ?" voix={voix}>
      {erreur ? <Erreur texte={erreur} onReessayer={charger} /> : null}
      {!erreur && !reponse ? <Chargement Icone={Plant} texte="Je regarde ton sol et la saison…" /> : null}
      {reponse ? (
        <>
          {sol?.texture ? (
            <Apparition ordre={0}>
              <View style={styles.sol}>
                <View style={{ flex: 1 }}>
                  <T v="etiquette" style={{ color: '#F3E3CF' }}>Ton sol</T>
                  <T v="sousTitre" style={{ color: couleurs.blanc }}>{nombreFr(sol.sable_pct, 0)} % de sable</T>
                </View>
                <View style={styles.solChiffre}>
                  <T v="etiquette" style={{ color: '#F3E3CF' }}>pH</T>
                  <T v="sousTitre" style={{ color: couleurs.blanc }}>{nombreFr(sol.ph, 1)}</T>
                  {sol.ph_mots ? <T v="etiquette" style={{ color: '#F3E3CF', textAlign: 'right' }}>{sol.ph_mots}</T> : null}
                </View>
              </View>
            </Apparition>
          ) : null}
          <Apparition ordre={1}>
            {wolof?.length ? <BlocWolof phrases={wolof} /> : <T v="corpsGras">{reponse.message.texte}</T>}
          </Apparition>
          {cultures.map((c, i) => <CarteCulture key={c.culture} c={c} ordre={i + 2} />)}
          <Bouton libelle="J'ai planté" sousTitre="Pour recevoir les alertes" Icone={Plant} onPress={() => router.push('/cultures')} />
          <Sources sources={reponse.sources} />
        </>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  sol: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#7A4A2B', borderRadius: 24, padding: 18, gap: 12 },
  solChiffre: { alignItems: 'flex-end' },
  tete: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  vignette: { width: 64, height: 64, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  eteinte: { opacity: 0.75 },
  ligne: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  wolof: { gap: 8, backgroundColor: couleurs.sable, borderRadius: 14, padding: 12 },
  avertissement: { flexDirection: 'row', gap: 10, backgroundColor: couleurs.terreClair, borderRadius: 14, padding: 12 },
});
