// Messages vocaux wolof de la conversation. Un seul lecteur pour toute l'application : les nouvelles notes
// vocales du bot se lisent toutes seules, l'une après l'autre (pour qui ne lit pas) ; toucher une bulle la lit
// (ou l'arrête) et vide la file.
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { Pause } from 'phosphor-react-native/src/icons/Pause';
import { Play } from 'phosphor-react-native/src/icons/Play';
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { T } from '@/components/ui';
import { couleurs, polices } from '@/theme';

type Lecteur = {
  /** Ajoute des notes à la file (lecture automatique). */
  ajouter: (ids: { id: string; adresse: string }[]) => void;
  /** Lit une seule note tout de suite (toucher), ou l'arrête si elle est en cours. */
  basculer: (id: string, adresse: string) => void;
  enCours: string | null;
  progression: number; // 0 à 1
  duree: number; // secondes, 0 si inconnue
};
const Contexte = createContext<Lecteur>({ ajouter: () => {}, basculer: () => {}, enCours: null, progression: 0, duree: 0 });

export function LecteurVoix({ children }: { children: ReactNode }) {
  const lecteur = useAudioPlayer(null);
  const etat = useAudioPlayerStatus(lecteur);
  const file = useRef<{ id: string; adresse: string }[]>([]);
  const [enCours, setEnCoursEtat] = useState<string | null>(null);
  // Copie synchrone : deux ajouts dans le même instant ne doivent pas lancer deux lectures.
  const enCoursRef = useRef<string | null>(null);
  const setEnCours = useCallback((id: string | null) => {
    enCoursRef.current = id;
    setEnCoursEtat(id);
  }, []);
  const garde = useRef<ReturnType<typeof setTimeout> | null>(null);
  const suivanteRef = useRef<() => void>(() => {});

  const suivante = useCallback(() => {
    if (garde.current) clearTimeout(garde.current);
    const n = file.current.shift();
    if (!n) {
      setEnCours(null);
      return;
    }
    setEnCours(n.id);
    lecteur.replace({ uri: n.adresse });
    lecteur.play();
    // Note introuvable ou réseau coupé : on ne bloque pas la file, on passe à la suivante.
    garde.current = setTimeout(() => {
      if (!lecteur.playing && lecteur.currentTime === 0) suivanteRef.current();
    }, 12_000);
  }, [lecteur, setEnCours]);
  useEffect(() => {
    suivanteRef.current = suivante;
  }, [suivante]);

  const ajouter = useCallback((notes: { id: string; adresse: string }[]) => {
    if (!notes.length) return;
    file.current.push(...notes);
    if (!enCoursRef.current) suivante();
  }, [suivante]);

  const basculer = useCallback((id: string, adresse: string) => {
    if (enCoursRef.current === id) {
      file.current = [];
      if (garde.current) clearTimeout(garde.current);
      lecteur.pause();
      setEnCours(null);
      return;
    }
    file.current = [{ id, adresse }];
    suivante();
  }, [lecteur, suivante, setEnCours]);

  useEffect(() => {
    if (etat.didJustFinish) suivante();
  }, [etat.didJustFinish, suivante]);

  const valeur = useMemo(() => ({
    ajouter, basculer, enCours,
    duree: etat.duration || 0,
    progression: etat.duration ? Math.min(1, etat.currentTime / etat.duration) : 0,
  }), [ajouter, basculer, enCours, etat.currentTime, etat.duration]);

  return <Contexte.Provider value={valeur}>{children}</Contexte.Provider>;
}

export const useLecteur = () => useContext(Contexte);

const BARRES = [6, 12, 18, 10, 22, 14, 8, 16, 24, 12, 18, 9, 15, 21, 11, 7, 17, 13, 20, 10, 6, 14, 19, 8];
const minutes = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

/** Bulle « message vocal » : gros bouton lecture, ondes qui se remplissent pendant la lecture. */
export function BulleVocale({ id, adresse, moi = false }: { id: string; adresse: string; moi?: boolean }) {
  const { basculer, enCours, progression, duree } = useLecteur();
  const actif = enCours === id;
  const rempli = actif ? Math.round(progression * BARRES.length) : 0;
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={actif ? 'Arrêter le message vocal' : 'Écouter le message vocal'}
      onPress={() => basculer(id, adresse)} style={styles.vocal}>
      <View style={[styles.rond, moi && { backgroundColor: couleurs.feuille }]}>
        {actif ? <Pause size={22} color={couleurs.blanc} weight="fill" /> : <Play size={22} color={couleurs.blanc} weight="fill" />}
      </View>
      <View style={{ flex: 1, gap: 4 }}>
        <View style={styles.ondes}>
          {BARRES.map((h, i) => (
            <View key={i} style={[styles.barre, {
              height: h,
              backgroundColor: i < rempli ? couleurs.foret : moi ? '#A9C9AE' : '#CBD3C4',
            }]} />
          ))}
        </View>
        <T style={styles.duree}>{actif && duree ? minutes(progression * duree) : 'Message vocal'}</T>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  vocal: { flexDirection: 'row', alignItems: 'center', gap: 10, width: 220 },
  rond: { width: 40, height: 40, borderRadius: 20, backgroundColor: couleurs.foret, alignItems: 'center', justifyContent: 'center' },
  ondes: { flexDirection: 'row', alignItems: 'center', gap: 2.5, height: 26 },
  barre: { width: 3, borderRadius: 2 },
  duree: { fontFamily: polices.texte, fontSize: 12, color: couleurs.encreDouce },
});
