// L'application tient en un seul écran : la conversation avec TerraMind, comme sur le bot Telegram.
// Un agriculteur qui parle wolof sans lire le français n'a besoin que de ça : les notes vocales se lisent toutes
// seules, et les grands boutons numérotés en bas de l'écran sont ceux que les notes vocales citent.
// La logique (textes, parcours, notes vocales) est dans conversation/bot.ts ; ici, seulement l'affichage.
import {
  RecordingPresets, requestRecordingPermissionsAsync, setAudioModeAsync, useAudioRecorder, useAudioRecorderState,
} from 'expo-audio';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { Camera } from 'phosphor-react-native/src/icons/Camera';
import { Images } from 'phosphor-react-native/src/icons/Images';
import { Leaf } from 'phosphor-react-native/src/icons/Leaf';
import { MapPin } from 'phosphor-react-native/src/icons/MapPin';
import { Microphone } from 'phosphor-react-native/src/icons/Microphone';
import { PaperPlaneRight } from 'phosphor-react-native/src/icons/PaperPlaneRight';
import { Translate } from 'phosphor-react-native/src/icons/Translate';
import { X } from 'phosphor-react-native/src/icons/X';
import { type ComponentRef, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  FlatList, Image, KeyboardAvoidingView, Platform, Pressable, StyleSheet, TextInput, View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ENGINE_URL } from '@/api';
import { TexteRiche } from '@/components/Bulle';
import { T } from '@/components/ui';
import { BulleVocale, useLecteur } from '@/components/Voix';
import {
  B_POSITION, type BoutonEnLigne, clavier, demarrer, type Entree, libelleAction, type Sortie, traiter,
} from '@/conversation/bot';
import { NOTES_VOCALES } from '@/conversation/notes-vocales';
import { conversationGardee, profil } from '@/profil';
import { couleurs, polices } from '@/theme';

type Message = {
  id: string;
  de: 'bot' | 'moi';
  texte?: string;
  boutons?: BoutonEnLigne[][];
  voix?: string; // adresse complète d'une note vocale
  photo?: string;
  position?: boolean;
};

let compteur = 0;
const nouvelId = () => `${Date.now().toString(36)}-${(compteur++).toString(36)}`;
// Mono, 64 kb/s : une minute pèse environ 0,5 Mo, assez pour la reconnaissance vocale et léger sur le réseau mobile.
const ENREGISTREMENT = { ...RecordingPresets.HIGH_QUALITY, numberOfChannels: 1, bitRate: 64000 };
const DUREE_MAX_S = 60;
const minutes = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

export default function Conversation() {
  const marges = useSafeAreaInsets();
  const { ajouter } = useLecteur();
  const [messages, setMessages] = useState<Message[]>(() => conversationGardee.lire<Message>());
  const [langue, setLangue] = useState(() => profil.lire().langue);
  const [occupe, setOccupe] = useState(0);
  const [texte, setTexte] = useState('');
  const [clavierSysteme, setClavierSysteme] = useState(false);
  const [menuPhoto, setMenuPhoto] = useState(false);
  const liste = useRef<FlatList<Message>>(null);
  const champ = useRef<ComponentRef<typeof TextInput>>(null);
  const file = useRef<Promise<void>>(Promise.resolve());

  // Toujours montrer le dernier message (la mise en page d'une bulle peut finir après l'ajout).
  useEffect(() => {
    const t = setTimeout(() => liste.current?.scrollToEnd({ animated: true }), 120);
    return () => clearTimeout(t);
  }, [messages, occupe]);

  useEffect(() => {
    // Les photos du navigateur (blob:) ne survivent pas à un rechargement : on ne les garde pas.
    conversationGardee.ecrire(messages.map((m) => (m.photo?.startsWith('blob:') ? { ...m, photo: undefined, texte: '[photo]' } : m)));
  }, [messages]);

  const poster = useCallback((m: Omit<Message, 'id'>) => {
    const complet = { ...m, id: nouvelId() };
    setMessages((ms) => [...ms, complet]);
    return complet;
  }, []);

  const sortie = useMemo<Sortie>(() => ({
    envoyer: (t, boutons) => {
      poster({ de: 'bot', texte: t, boutons });
      setLangue(profil.lire().langue);
    },
    noteVocale: (cle) => {
      const ext = NOTES_VOCALES[cle];
      if (!ext) return; // pas encore enregistrée : le texte suit de toute façon (comme le bot)
      const m = poster({ de: 'bot', voix: `${ENGINE_URL}/audio/wo/${cle}.${ext}` });
      ajouter([{ id: m.id, adresse: m.voix! }]);
    },
    voix: (adresse) => {
      const m = poster({ de: 'bot', voix: `${ENGINE_URL}${adresse}` });
      ajouter([{ id: m.id, adresse: m.voix! }]);
    },
  }), [poster, ajouter]);

  /** Un message à la fois, dans l'ordre (comme traiter_dans_l_ordre du bot). */
  const envoyer = useCallback((e: Entree) => {
    setOccupe((n) => n + 1);
    file.current = file.current.then(() => traiter(e, sortie)).finally(() => {
      setOccupe((n) => n - 1);
      setLangue(profil.lire().langue);
    });
  }, [sortie]);

  // Première ouverture (ou après /oublier) : la question de la langue, dite aussi en wolof.
  useEffect(() => {
    if (!messages.length) demarrer(sortie);
  }, [messages.length, sortie]);

  const ecrire = (t: string) => {
    if (!t.trim()) return;
    if (t.trim().startsWith('/oublier')) {
      setTexte('');
      profil.oublier();
      setLangue(undefined);
      setMessages([]);
      return;
    }
    poster({ de: 'moi', texte: t.trim() });
    setTexte('');
    champ.current?.blur(); // le clavier du téléphone se ferme : les grands boutons reviennent
    setClavierSysteme(false);
    envoyer({ texte: t });
  };

  const toucherBouton = (libelle: string, bouton: string) => {
    if (bouton === B_POSITION) {
      void partagerPosition();
      return;
    }
    poster({ de: 'moi', texte: libelle });
    envoyer({ texte: bouton });
  };

  const partagerPosition = async () => {
    const { granted } = await Location.requestForegroundPermissionsAsync().catch(() => ({ granted: false }));
    if (!granted) {
      sortie.envoyer(
        "Je n'ai pas pu lire la position de ton champ. Autorise la position pour TerraMind dans les réglages du téléphone, puis touche à nouveau « "
        + B_POSITION + ' ».',
      );
      return;
    }
    try {
      const p = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      poster({ de: 'moi', position: true });
      // Arrondi à 0,01° (environ 1 km), comme le bot : assez pour le sol et la météo, sans localiser la parcelle.
      envoyer({ position: { lat: Math.round(p.coords.latitude * 100) / 100, lon: Math.round(p.coords.longitude * 100) / 100 } });
    } catch {
      sortie.envoyer("Je n'ai pas trouvé ta position. Réessaie dehors, dans ton champ, avec le bouton « " + B_POSITION + ' ».');
    }
  };

  const choisirPhoto = async (source: 'camera' | 'galerie') => {
    setMenuPhoto(false);
    if (source === 'camera' && Platform.OS !== 'web') {
      const { granted } = await ImagePicker.requestCameraPermissionsAsync();
      if (!granted) {
        sortie.envoyer("Sans l'appareil photo, choisis une photo déjà prise dans ta galerie.");
        return;
      }
    }
    const options: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], quality: 0.8 };
    const r = source === 'camera' ? await ImagePicker.launchCameraAsync(options) : await ImagePicker.launchImageLibraryAsync(options);
    if (r.canceled || !r.assets?.[0]) return;
    poster({ de: 'moi', photo: r.assets[0].uri });
    envoyer({ photo: { uri: r.assets[0].uri, type: r.assets[0].mimeType ?? null } });
  };

  // ── Note vocale : garder le doigt appuyé sur le micro, relâcher pour envoyer (comme Telegram) ──
  const enregistreur = useAudioRecorder(ENREGISTREMENT);
  const etatMicro = useAudioRecorderState(enregistreur, 250);
  const [ecoute, setEcoute] = useState(false);
  const ecouteRef = useRef(false);
  const relache = useRef(false);
  const minuterie = useRef<ReturnType<typeof setTimeout> | null>(null);

  const finirVocal = useCallback(async () => {
    if (!ecouteRef.current) return;
    ecouteRef.current = false;
    if (minuterie.current) clearTimeout(minuterie.current);
    const duree = enregistreur.getStatus().durationMillis / 1000;
    setEcoute(false);
    await enregistreur.stop();
    await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true }).catch(() => {});
    const uri = enregistreur.uri;
    if (!uri || duree < 1) return; // appui trop court : rien n'est envoyé
    poster({ de: 'moi', voix: uri });
    envoyer({ vocal: { uri, duree } });
  }, [enregistreur, envoyer, poster]);

  const commencerVocal = async () => {
    relache.current = false;
    const permission = await requestRecordingPermissionsAsync().catch(() => ({ granted: false, canAskAgain: false }));
    if (!permission.granted) {
      sortie.envoyer('TerraMind a besoin du micro pour écouter ta question. Autorise-le dans les réglages du téléphone, ou écris ta question.');
      return;
    }
    if (relache.current) return; // la fenêtre d'autorisation a interrompu l'appui : il faudra appuyer à nouveau
    try {
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await enregistreur.prepareToRecordAsync();
      enregistreur.record();
      ecouteRef.current = true;
      setEcoute(true);
      if (relache.current) void finirVocal();
      // Une minute au plus (limite du moteur) : envoi automatique à 59 secondes.
      minuterie.current = setTimeout(() => void finirVocal(), (DUREE_MAX_S - 1) * 1000);
    } catch {
      sortie.envoyer("Je n'arrive pas à utiliser le micro de ce téléphone. Écris ta question.");
    }
  };

  const boutons = langue ? clavier(langue) : [];
  const afficherClavier = !clavierSysteme && !menuPhoto && boutons.length > 0;

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={[styles.entete, { paddingTop: marges.top + 10 }]}>
        <View style={styles.logo}><Leaf size={24} color={couleurs.foret} weight="fill" /></View>
        <View style={{ flex: 1 }}>
          <T style={styles.nom}>TerraMind</T>
          <T style={styles.statut}>{occupe ? 'écrit…' : 'Assistant maraîchage des Niayes'}</T>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel="Changer de langue" hitSlop={8}
          onPress={() => envoyer({ texte: '/langue' })} style={styles.boutonEntete}>
          <Translate size={22} color={couleurs.blanc} weight="bold" />
        </Pressable>
      </View>

      <FlatList
        ref={liste}
        style={styles.fil}
        contentContainerStyle={styles.filContenu}
        data={messages}
        keyExtractor={(m) => m.id}
        onContentSizeChange={() => liste.current?.scrollToEnd({ animated: true })}
        renderItem={({ item }) => (
          <Bulle m={item} onAction={(action) => {
            poster({ de: 'moi', texte: libelleAction(item.boutons, action) });
            envoyer({ action });
          }} />
        )}
        ListFooterComponent={occupe ? <View style={[styles.bulle, styles.bulleBot, styles.attente]}><T style={styles.points}>• • •</T></View> : undefined}
      />

      <View style={[styles.bas, { paddingBottom: (afficherClavier ? 8 : 10) + (clavierSysteme ? 0 : marges.bottom) }]}>
        <View style={styles.saisie}>
          <Pressable accessibilityRole="button" accessibilityLabel="Envoyer une photo de ma plante"
            onPress={() => setMenuPhoto((v) => !v)} style={[styles.rondSaisie, styles.rondPhoto]}>
            {menuPhoto ? <X size={24} color={couleurs.foret} weight="bold" /> : <Camera size={26} color={couleurs.foret} weight="fill" />}
          </Pressable>
          {ecoute ? (
            <View style={[styles.champ, styles.enregistrement]}>
              <View style={styles.pointRouge} />
              <T style={styles.texteEnregistrement}>{minutes(etatMicro.durationMillis / 1000)}  ·  Relâche pour envoyer</T>
            </View>
          ) : (
            <TextInput ref={champ} value={texte} submitBehavior="blurAndSubmit" numberOfLines={1} onChangeText={setTexte} placeholder="Message" placeholderTextColor={couleurs.encreDouce}
              style={styles.champ} multiline maxLength={2000} accessibilityLabel="Écrire un message"
              onFocus={() => { setClavierSysteme(true); setMenuPhoto(false); }} onBlur={() => setClavierSysteme(false)}
              onSubmitEditing={() => ecrire(texte)}
              onKeyPress={(e) => {
                // Navigateur : Entrée envoie (Maj + Entrée va à la ligne), comme dans une messagerie.
                const ev = e.nativeEvent as { key: string; shiftKey?: boolean };
                if (Platform.OS === 'web' && ev.key === 'Enter' && !ev.shiftKey) {
                  e.preventDefault();
                  ecrire(texte);
                }
              }} />
          )}
          {texte.trim() ? (
            <Pressable accessibilityRole="button" accessibilityLabel="Envoyer" onPress={() => ecrire(texte)} style={styles.rondSaisie}>
              <PaperPlaneRight size={24} color={couleurs.blanc} weight="fill" />
            </Pressable>
          ) : (
            <Pressable accessibilityRole="button" accessibilityLabel="Garder le doigt appuyé pour parler en wolof"
              onPressIn={() => void commencerVocal()} onPressOut={() => { relache.current = true; void finirVocal(); }}
              style={[styles.rondSaisie, ecoute && styles.microActif]}>
              <Microphone size={26} color={couleurs.blanc} weight="fill" />
            </Pressable>
          )}
        </View>

        {menuPhoto ? (
          <View style={styles.menuPhoto}>
            <Pressable accessibilityRole="button" onPress={() => void choisirPhoto('camera')} style={styles.choixPhoto}>
              <Camera size={28} color={couleurs.foret} weight="duotone" />
              <T style={styles.texteBouton}>Appareil photo</T>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => void choisirPhoto('galerie')} style={styles.choixPhoto}>
              <Images size={28} color={couleurs.foret} weight="duotone" />
              <T style={styles.texteBouton}>Galerie</T>
            </Pressable>
          </View>
        ) : null}

        {afficherClavier ? (
          <View style={styles.clavier}>
            {boutons.map((b) => (
              <Pressable key={b.bouton} accessibilityRole="button" onPress={() => toucherBouton(b.texte, b.bouton)}
                style={({ pressed }) => [styles.grandBouton, pressed && { backgroundColor: couleurs.pousse }]}>
                <T style={styles.texteBouton} numberOfLines={2}>{b.texte}</T>
              </Pressable>
            ))}
          </View>
        ) : null}
      </View>
    </KeyboardAvoidingView>
  );
}

function Bulle({ m, onAction }: { m: Message; onAction: (action: string) => void }) {
  const moi = m.de === 'moi';
  return (
    <View style={{ alignSelf: moi ? 'flex-end' : 'flex-start', maxWidth: '88%', gap: 4 }}>
      <View style={[styles.bulle, moi ? styles.bulleMoi : styles.bulleBot, m.photo ? styles.bullePhoto : null]}>
        {m.photo ? <Image source={{ uri: m.photo }} style={styles.photo} accessibilityLabel="Photo envoyée" /> : null}
        {m.voix ? <BulleVocale id={m.id} adresse={m.voix} moi={moi} /> : null}
        {m.position ? (
          <View style={styles.position}>
            <MapPin size={26} color={couleurs.terre} weight="fill" />
            <T style={styles.texteBulle}>Position de mon champ</T>
          </View>
        ) : null}
        {m.texte ? <TexteRiche texte={m.texte} style={styles.texteBulle} /> : null}
      </View>
      {m.boutons?.map((ligne, i) => (
        <View key={i} style={styles.ligneBoutons}>
          {ligne.map((b) => (
            <Pressable key={b.action} accessibilityRole="button" onPress={() => onAction(b.action)}
              style={({ pressed }) => [styles.boutonEnLigne, pressed && { opacity: 0.75 }]}>
              <T style={styles.texteBoutonEnLigne}>{b.texte}</T>
            </Pressable>
          ))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  entete: {
    flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 16, paddingBottom: 12,
    backgroundColor: couleurs.foret,
  },
  logo: { width: 42, height: 42, borderRadius: 21, backgroundColor: couleurs.pousse, alignItems: 'center', justifyContent: 'center' },
  nom: { fontFamily: polices.titreMoyen, fontSize: 19, color: couleurs.blanc },
  statut: { fontFamily: polices.texte, fontSize: 13, color: '#CFE3D3' },
  boutonEntete: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.14)' },
  fil: { flex: 1, backgroundColor: couleurs.sable },
  filContenu: { padding: 10, gap: 6 },
  bulle: { borderRadius: 18, paddingHorizontal: 13, paddingVertical: 9, gap: 8 },
  bulleBot: { backgroundColor: couleurs.carte, borderTopLeftRadius: 6, borderWidth: 1, borderColor: couleurs.trait },
  bulleMoi: { backgroundColor: '#D7EBD5', borderTopRightRadius: 6 },
  bullePhoto: { padding: 4 },
  photo: { width: 220, height: 220, borderRadius: 14 },
  attente: { alignSelf: 'flex-start', marginTop: 8 },
  points: { fontSize: 16, color: couleurs.encreDouce, letterSpacing: 2 },
  texteBulle: { fontFamily: polices.texte, fontSize: 16.5, lineHeight: 23, color: couleurs.encre },
  position: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  ligneBoutons: { flexDirection: 'row', gap: 6 },
  boutonEnLigne: {
    flex: 1, minHeight: 44, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 8, alignItems: 'center', justifyContent: 'center',
    backgroundColor: couleurs.feuille,
  },
  texteBoutonEnLigne: { fontFamily: polices.texteGras, fontSize: 15.5, color: couleurs.blanc, textAlign: 'center' },
  bas: { backgroundColor: couleurs.sableFonce, paddingTop: 6, paddingHorizontal: 6, gap: 6, borderTopWidth: 1, borderColor: couleurs.trait },
  saisie: { flexDirection: 'row', alignItems: 'flex-end', gap: 8 },
  rondSaisie: { width: 46, height: 46, borderRadius: 23, backgroundColor: couleurs.foret, alignItems: 'center', justifyContent: 'center' },
  rondPhoto: { backgroundColor: couleurs.carte, borderWidth: 1.5, borderColor: couleurs.trait },
  microActif: { backgroundColor: couleurs.terre, transform: [{ scale: 1.15 }] },
  champ: {
    flex: 1, minHeight: 46, maxHeight: 120, borderRadius: 23, backgroundColor: couleurs.carte, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 11,
    fontFamily: polices.texte, fontSize: 16.5, color: couleurs.encre, borderWidth: 1.5, borderColor: couleurs.trait,
  },
  enregistrement: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingTop: 0, paddingBottom: 0 },
  pointRouge: { width: 12, height: 12, borderRadius: 6, backgroundColor: couleurs.terre },
  texteEnregistrement: { fontFamily: polices.texteGras, fontSize: 15, color: couleurs.terre },
  menuPhoto: { flexDirection: 'row', gap: 8 },
  choixPhoto: {
    flex: 1, alignItems: 'center', gap: 6, paddingVertical: 14, borderRadius: 14, backgroundColor: couleurs.carte,
    borderWidth: 1.5, borderColor: couleurs.trait,
  },
  clavier: { gap: 5 },
  grandBouton: {
    minHeight: 40, borderRadius: 11, paddingHorizontal: 10, paddingVertical: 6, alignItems: 'center', justifyContent: 'center',
    backgroundColor: couleurs.carte, borderWidth: 1.5, borderColor: couleurs.trait,
  },
  texteBouton: { fontFamily: polices.texteGras, fontSize: 14.5, lineHeight: 19, color: couleurs.foret, textAlign: 'center' },
});
