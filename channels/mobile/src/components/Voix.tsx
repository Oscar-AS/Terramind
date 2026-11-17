// Notes vocales wolof (phrases relues par un locuteur, servies par le moteur sur /audio/wo/).
// Un seul lecteur par écran : une nouvelle lecture arrête la précédente ; les phrases s'enchaînent.
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { SpeakerHigh, Stop } from 'phosphor-react-native';
import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { ENGINE_URL, type PhraseWolof } from '@/api';
import { T } from '@/components/ui';
import { couleurs, tailles } from '@/theme';

type Lecteur = { jouer: (phrases: PhraseWolof[]) => void; arreter: () => void; enCours: PhraseWolof[] | null };
const Contexte = createContext<Lecteur>({ jouer: () => {}, arreter: () => {}, enCours: null });

const adresses = (phrases: PhraseWolof[]) =>
  phrases.flatMap((p) => (p.audio_url ? [`${ENGINE_URL}${p.audio_url}`] : []));

export function LecteurVoix({ children }: { children: ReactNode }) {
  const lecteur = useAudioPlayer(null);
  const etat = useAudioPlayerStatus(lecteur);
  const file = useRef<string[]>([]);
  const [enCours, setEnCours] = useState<PhraseWolof[] | null>(null);

  const lire = useCallback((adresse: string) => {
    lecteur.replace({ uri: adresse });
    lecteur.play();
  }, [lecteur]);

  const arreter = useCallback(() => {
    file.current = [];
    lecteur.pause();
    setEnCours(null);
  }, [lecteur]);

  const jouer = useCallback((phrases: PhraseWolof[]) => {
    const liste = adresses(phrases);
    if (!liste.length) return;
    file.current = liste.slice(1);
    setEnCours(phrases);
    lire(liste[0]);
  }, [lire]);

  useEffect(() => {
    if (!etat.didJustFinish) return;
    const suivante = file.current.shift();
    if (suivante) lire(suivante);
    else setEnCours(null);
  }, [etat.didJustFinish, lire]);

  useEffect(() => () => arreter(), [arreter]);

  return <Contexte.Provider value={{ jouer, arreter, enCours }}>{children}</Contexte.Provider>;
}

export const useLecteur = () => useContext(Contexte);

/** Bouton « Écouter » : lit les phrases, ou arrête si elles sont déjà en cours. Rien sans note vocale. */
export function BoutonEcouter({ phrases, libelle = 'Écouter en wolof' }: { phrases: PhraseWolof[]; libelle?: string }) {
  const { jouer, arreter, enCours } = useLecteur();
  if (!adresses(phrases).length) return null;
  const actif = enCours === phrases;
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={actif ? 'Arrêter' : libelle}
      onPress={() => (actif ? arreter() : jouer(phrases))} hitSlop={6}
      style={({ pressed }) => [styles.bouton, actif && styles.boutonActif, pressed && { opacity: 0.8 }]}>
      {actif ? <Stop size={20} color={couleurs.blanc} weight="fill" />
        : <SpeakerHigh size={20} color={couleurs.foret} weight="duotone" />}
      <T v="etiquette" style={{ color: actif ? couleurs.blanc : couleurs.foret }}>{actif ? 'Arrêter' : libelle}</T>
    </Pressable>
  );
}

/** Texte wolof relu, son bouton d'écoute, et le français en petit dessous. */
export function BlocWolof({ phrases, avecFrancais = true }: { phrases: PhraseWolof[]; avecFrancais?: boolean }) {
  if (!phrases.length) return null;
  return (
    <View style={styles.bloc}>
      <BoutonEcouter phrases={phrases} />
      <T v="corpsGras">{phrases.map((p) => p.texte_wo).join(' ')}</T>
      {avecFrancais ? <T v="petit" style={{ color: couleurs.encreDouce }}>{phrases.map((p) => p.texte_fr).join(' ')}</T> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  bouton: {
    alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8,
    paddingHorizontal: 14, borderRadius: 999, backgroundColor: couleurs.pousse,
  },
  boutonActif: { backgroundColor: couleurs.foret },
  bloc: { gap: 8, backgroundColor: couleurs.carte, borderRadius: tailles.rayon, padding: 16, borderWidth: 1, borderColor: couleurs.trait },
});
