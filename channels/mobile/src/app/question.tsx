import {
  RecordingPresets, requestRecordingPermissionsAsync, setAudioModeAsync, useAudioRecorder, useAudioRecorderState,
} from 'expo-audio';
import { BookOpenText } from 'phosphor-react-native/src/icons/BookOpenText';
import { ChatCircleText } from 'phosphor-react-native/src/icons/ChatCircleText';
import { Microphone } from 'phosphor-react-native/src/icons/Microphone';
import { PaperPlaneRight } from 'phosphor-react-native/src/icons/PaperPlaneRight';
import { Stop } from 'phosphor-react-native/src/icons/Stop';
import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { type PhraseWolof, poserQuestion, poserQuestionVocale, type Reponse, type Source } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Sources } from '@/components/Etat';
import { Apparition, Carte, Pastille, T } from '@/components/ui';
import { BlocWolof } from '@/components/Voix';
import { couleurs, polices, tailles } from '@/theme';

// Étape 7 : question libre. Écrite (POST /v1/chat) ou dite en wolof (POST /v1/chat/vocal : Octopus transcrit,
// Gemini traduit, la réponse vient des fiches, D8, puis elle est dite en wolof). Le moteur refuse au-delà d'une minute.
const EXEMPLES = ['Ma tomate a des taches brunes avec des cercles', "Quand semer l'oignon ?", "L'eau de mon puits est salée"];
const DUREE_MAX_S = 60;
// Mono, 64 kb/s : une minute pèse environ 0,5 Mo, assez pour la reconnaissance vocale et léger sur le réseau mobile.
const ENREGISTREMENT = { ...RecordingPresets.HIGH_QUALITY, numberOfChannels: 1, bitRate: 64000 };

type Resultat = { texte: string; ok: boolean; sources: Source[]; compris?: string | null; voix?: PhraseWolof | null };

const minutes = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

export default function Question() {
  const [texte, setTexte] = useState('');
  const [envoi, setEnvoi] = useState<'texte' | 'vocal' | null>(null);
  const [reponse, setReponse] = useState<Resultat | null>(null);
  const enregistreur = useAudioRecorder(ENREGISTREMENT);
  const etat = useAudioRecorderState(enregistreur, 250);
  const [ecoute, setEcoute] = useState(false);
  const secondes = etat.durationMillis / 1000;
  const minuterie = useRef<ReturnType<typeof setTimeout> | null>(null);
  const envoyerVocalRef = useRef<() => void>(() => {});

  const envoyer = async (q = texte) => {
    if (!q.trim()) return;
    setTexte(q);
    setEnvoi('texte');
    setReponse(null);
    try {
      const r: Reponse<unknown> = await poserQuestion(q.trim());
      setReponse({ texte: r.message.texte, ok: r.statut === 'ok', sources: r.sources });
    } catch (e) {
      setReponse({ texte: (e as Error).message, ok: false, sources: [] });
    } finally {
      setEnvoi(null);
    }
  };

  const commencerVocal = async () => {
    setReponse(null);
    try {
      const permission = await requestRecordingPermissionsAsync();
      if (!permission.granted) {
        setReponse({ texte: 'TerraMind a besoin du micro pour écouter ta question. Autorise-le dans les réglages du téléphone, ou écris ta question.', ok: false, sources: [] });
        return;
      }
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await enregistreur.prepareToRecordAsync();
      enregistreur.record();
      setEcoute(true);
      // Une minute au plus (limite du moteur) : on envoie tout seul à 59 secondes.
      minuterie.current = setTimeout(() => envoyerVocalRef.current(), (DUREE_MAX_S - 1) * 1000);
    } catch {
      setReponse({ texte: "Je n'arrive pas à utiliser le micro de ce téléphone. Écris ta question.", ok: false, sources: [] });
    }
  };

  const envoyerVocal = async () => {
    if (minuterie.current) clearTimeout(minuterie.current);
    minuterie.current = null;
    const duree = Math.max(secondes, enregistreur.getStatus().durationMillis / 1000);
    setEcoute(false);
    await enregistreur.stop();
    await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true }).catch(() => {});
    const uri = enregistreur.uri;
    if (!uri || duree < 1) {
      setReponse({ texte: "Je n'ai rien entendu. Touche le micro, parle, puis touche à nouveau pour envoyer.", ok: false, sources: [] });
      return;
    }
    setEnvoi('vocal');
    try {
      const r = await poserQuestionVocale(uri, duree);
      setReponse({
        texte: r.message.texte, ok: r.statut === 'ok', sources: r.sources,
        compris: r.donnees?.transcription?.francais ?? null, voix: r.donnees?.voix ?? null,
      });
    } catch (e) {
      setReponse({ texte: (e as Error).message, ok: false, sources: [] });
    } finally {
      setEnvoi(null);
    }
  };

  useEffect(() => {
    envoyerVocalRef.current = envoyerVocal;
  });
  useEffect(() => () => {
    if (minuterie.current) clearTimeout(minuterie.current);
  }, []);

  return (
    <Ecran titre="Poser une question">
      <View style={styles.saisie}>
        <TextInput value={texte} onChangeText={setTexte} placeholder="Écris ta question ici" placeholderTextColor={couleurs.encreDouce}
          multiline maxLength={2000} style={styles.champ} accessibilityLabel="Ta question" editable={!ecoute} />
        <Pressable accessibilityRole="button" accessibilityLabel="Envoyer" onPress={() => envoyer()} disabled={!!envoi || ecoute}
          style={({ pressed }) => [styles.envoyer, (pressed || !!envoi || ecoute) && { opacity: 0.7 }]}>
          <PaperPlaneRight size={26} color={couleurs.blanc} weight="fill" />
        </Pressable>
      </View>

      <Pressable accessibilityRole="button" disabled={!!envoi}
        accessibilityLabel={ecoute ? 'Arrêter et envoyer ma question' : 'Poser ma question à voix haute, en wolof'}
        onPress={() => (ecoute ? envoyerVocal() : commencerVocal())}
        style={({ pressed }) => [styles.micro, ecoute && styles.microActif, (pressed || !!envoi) && { opacity: 0.8 }]}>
        <View style={[styles.rond, ecoute && { backgroundColor: couleurs.blanc }]}>
          {ecoute ? <Stop size={22} color={couleurs.terre} weight="fill" /> : <Microphone size={24} color={couleurs.blanc} weight="fill" />}
        </View>
        <View style={{ flex: 1 }}>
          <T v="corpsGras" style={{ color: ecoute ? couleurs.blanc : couleurs.foret }}>
            {ecoute ? `J'écoute… ${minutes(secondes)}` : 'Ou parle en wolof'}
          </T>
          <T v="petit" style={{ color: ecoute ? couleurs.blanc : couleurs.encreDouce }}>
            {ecoute ? 'Touche encore pour envoyer ta question.' : 'Touche le micro et pose ta question à voix haute (moins d’une minute).'}
          </T>
        </View>
      </Pressable>

      {!reponse && !envoi && !ecoute ? (
        <View style={{ gap: 8 }}>
          <T v="etiquette">Par exemple</T>
          {EXEMPLES.map((e, i) => (
            <Apparition key={e} ordre={i}>
              <Pressable accessibilityRole="button" accessibilityLabel={e} onPress={() => envoyer(e)} style={({ pressed }) => [styles.exemple, pressed && { backgroundColor: couleurs.pousse }]}>
                <ChatCircleText size={20} color={couleurs.feuille} weight="duotone" />
                <T v="corps" style={{ flex: 1, fontSize: 16 }}>{e}</T>
              </Pressable>
            </Apparition>
          ))}
        </View>
      ) : null}
      {envoi === 'texte' ? <Chargement Icone={BookOpenText} texte="Je cherche dans les fiches…" /> : null}
      {envoi === 'vocal' ? <Chargement Icone={Microphone} texte="J'écoute ta note vocale. Cela prend quelques secondes…" /> : null}
      {reponse ? (
        <Apparition>
          {reponse.compris ? (
            <T v="petit" style={styles.compris}>J’ai compris ta question ainsi : « {reponse.compris} »</T>
          ) : null}
          {reponse.voix ? <><BlocWolof phrases={[reponse.voix]} avecFrancais={false} /><View style={{ height: 12 }} /></> : null}
          <Carte style={!reponse.ok && { backgroundColor: couleurs.soleilClair }}>
            <View style={styles.tete}>
              <Pastille Icone={BookOpenText} taille={40} />
              <T v="etiquette" style={{ flex: 1 }}>{reponse.ok ? 'D’après nos fiches' : 'Je ne sais pas'}</T>
            </View>
            <T v="corps">{reponse.texte}</T>
          </Carte>
          <View style={{ height: 12 }} />
          <Sources sources={reponse.sources} />
        </Apparition>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  saisie: { flexDirection: 'row', alignItems: 'flex-end', gap: 10 },
  champ: {
    flex: 1, minHeight: 110, borderRadius: tailles.rayon, backgroundColor: couleurs.carte, padding: 16, fontSize: 18,
    fontFamily: polices.texte, color: couleurs.encre, textAlignVertical: 'top', borderWidth: 1.5, borderColor: couleurs.trait,
  },
  envoyer: { width: 60, height: 60, borderRadius: 30, backgroundColor: couleurs.foret, alignItems: 'center', justifyContent: 'center' },
  micro: {
    flexDirection: 'row', alignItems: 'center', gap: 12, padding: 12, borderRadius: tailles.rayon,
    backgroundColor: couleurs.pousse, borderWidth: 1, borderColor: couleurs.trait,
  },
  microActif: { backgroundColor: couleurs.terre, borderColor: couleurs.terre },
  rond: { width: 48, height: 48, borderRadius: 24, backgroundColor: couleurs.foret, alignItems: 'center', justifyContent: 'center' },
  exemple: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 14, borderRadius: 16, backgroundColor: couleurs.carte, borderWidth: 1, borderColor: couleurs.trait },
  tete: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  compris: { fontStyle: 'italic', color: couleurs.encreDouce, marginBottom: 10 },
});
