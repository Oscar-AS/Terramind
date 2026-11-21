// L'application tient en un seul écran : la conversation avec TerraMind, comme sur le bot Telegram.
// Un agriculteur qui parle wolof sans lire le français n'a besoin que de ça : les notes vocales se lisent toutes
// seules, et les grands boutons numérotés sous la case « Message » sont ceux que les notes vocales citent
// (« le petit bouton rond tout à gauche de la case Message », « le micro en bas à droite »).
// Logique (textes, parcours, notes vocales) : conversation/bot.ts ; ici, seulement l'affichage.
import {
  RecordingPresets, requestRecordingPermissionsAsync, setAudioModeAsync, useAudioRecorder, useAudioRecorderState,
} from 'expo-audio';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import * as Location from 'expo-location';
import { Camera } from 'phosphor-react-native/src/icons/Camera';
import { CaretDown } from 'phosphor-react-native/src/icons/CaretDown';
import { ChatText } from 'phosphor-react-native/src/icons/ChatText';
import { Images } from 'phosphor-react-native/src/icons/Images';
import { Leaf } from 'phosphor-react-native/src/icons/Leaf';
import { MapPin } from 'phosphor-react-native/src/icons/MapPin';
import { Microphone } from 'phosphor-react-native/src/icons/Microphone';
import { PaperPlaneTilt } from 'phosphor-react-native/src/icons/PaperPlaneTilt';
import { SpeakerHigh } from 'phosphor-react-native/src/icons/SpeakerHigh';
import { Translate } from 'phosphor-react-native/src/icons/Translate';
import { X } from 'phosphor-react-native/src/icons/X';
import { type ComponentRef, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Animated, FlatList, Image, KeyboardAvoidingView, Platform, Pressable, StyleSheet, TextInput, View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';

import { ENGINE_URL } from '@/api';
import { insecables, TexteRiche } from '@/components/Bulle';
import { Paysage } from '@/components/Paysage';
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
  heure: number;
  texte?: string;
  boutons?: BoutonEnLigne[][];
  voix?: string; // adresse complète d'une note vocale
  photo?: string;
  position?: boolean;
};

// Couleurs propres à la conversation, tirées de la palette (theme.ts).
const C = {
  bulleBot: '#F3EDE1',
  bulleMoi: couleurs.pousse,
  heure: '#6E776F',
  pastilleJour: '#EFE8DA',
  bordDoux: '#E6DDCB',
};

let compteur = 0;
const nouvelId = () => `${Date.now().toString(36)}-${(compteur++).toString(36)}`;
// Mono, 64 kb/s : une minute pèse environ 0,5 Mo, assez pour la reconnaissance vocale et léger sur le réseau mobile.
const ENREGISTREMENT = { ...RecordingPresets.HIGH_QUALITY, numberOfChannels: 1, bitRate: 64000 };
const DUREE_MAX_S = 60;
const minutes = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const heureFr = (t: number) => {
  const d = new Date(t);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};
const memeJour = (a: number, b: number) => new Date(a).toDateString() === new Date(b).toDateString();
const jourFr = (t: number) => {
  if (memeJour(t, Date.now())) return "Aujourd'hui";
  if (memeJour(t, Date.now() - 86_400_000)) return 'Hier';
  const d = new Date(t);
  return `${d.getDate()}/${String(d.getMonth() + 1).padStart(2, '0')}`;
};

export default function Conversation() {
  const marges = useSafeAreaInsets();
  const { ajouter, basculer } = useLecteur();
  const [messages, setMessages] = useState<Message[]>(() => conversationGardee.lire<Message>().filter((m) => m.de && m.heure));
  const [langue, setLangue] = useState(() => profil.lire().langue);
  const [occupe, setOccupe] = useState(0);
  const [texte, setTexte] = useState('');
  const [clavierSysteme, setClavierSysteme] = useState(false);
  const [menuPhoto, setMenuPhoto] = useState(false);
  const liste = useRef<FlatList<Message>>(null);
  const champ = useRef<ComponentRef<typeof TextInput>>(null);
  const file = useRef<Promise<void>>(Promise.resolve());

  // Montrer le dernier message quand il arrive (sa mise en page peut finir un peu après l'ajout). Seulement dans
  // les 2 secondes qui suivent : si l'agriculteur remonte relire une réponse, une photo qui se charge ne doit pas le
  // ramener en bas.
  // Quand TerraMind répond, la liste s'arrête sur le DÉBUT de sa réponse (ses notes vocales d'abord), pas sur la
  // fin : une note vocale reste visible et réécoutable même si le texte qui suit est long.
  const suivreLaFin = useRef(false);
  const defiler = useCallback(() => {
    const dernierMoi = messages.map((m) => m.de).lastIndexOf('moi');
    const debutReponse = dernierMoi + 1;
    if (debutReponse < messages.length && !occupe) {
      liste.current?.scrollToIndex({ index: debutReponse, viewPosition: 0, viewOffset: 12, animated: true });
    } else {
      liste.current?.scrollToEnd({ animated: true });
    }
  }, [messages, occupe]);
  useEffect(() => {
    suivreLaFin.current = true;
    const t = setTimeout(defiler, 120);
    const fin = setTimeout(() => { suivreLaFin.current = false; }, 2000);
    return () => { clearTimeout(t); clearTimeout(fin); };
  }, [defiler]);

  useEffect(() => {
    // Les photos du navigateur (blob:) ne survivent pas à un rechargement : on ne les garde pas.
    conversationGardee.ecrire(messages.map((m) => (m.photo?.startsWith('blob:') ? { ...m, photo: undefined, texte: '[photo]' } : m)));
  }, [messages]);

  const poster = useCallback((m: Omit<Message, 'id' | 'heure'>) => {
    const complet = { ...m, id: nouvelId(), heure: Date.now() };
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
    setTexte('');
    champ.current?.blur(); // le clavier du téléphone se ferme : les grands boutons reviennent
    setClavierSysteme(false);
    if (t.trim().startsWith('/oublier')) {
      profil.oublier();
      setLangue(undefined);
      setMessages([]);
      return;
    }
    poster({ de: 'moi', texte: t.trim() });
    envoyer({ texte: t });
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

  const toucherBouton = (libelle: string, bouton: string) => {
    setMenuPhoto(false);
    if (bouton === B_POSITION) {
      void partagerPosition();
      return;
    }
    poster({ de: 'moi', texte: libelle });
    envoyer({ texte: bouton });
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
    const photo = r.canceled ? null : r.assets?.[0];
    if (!photo) return;
    poster({ de: 'moi', photo: photo.uri });
    envoyer({ photo: { uri: photo.uri, type: photo.mimeType ?? null } });
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
    const permission = await requestRecordingPermissionsAsync().catch(() => ({ granted: false }));
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
  const afficherBoutons = !clavierSysteme && !menuPhoto && boutons.length > 0;
  // Écran d'accueil (maquette, écran du milieu) tant que la langue n'est pas choisie et que rien n'a été envoyé.
  const accueil = !langue && !messages.some((m) => m.de === 'moi');
  const derniereVoix = [...messages].reverse().find((m) => m.voix);

  const choisirLangue = (action: 'langue:wo' | 'langue:fr') => {
    poster({ de: 'moi', texte: action === 'langue:wo' ? 'Wolof' : 'Français' });
    envoyer({ action });
  };

  const champSaisie = ecoute ? (
    <View style={styles.enregistrement}>
      <View style={styles.pointRouge} />
      <T style={styles.texteEnregistrement}>{minutes(etatMicro.durationMillis / 1000)}  ·  Relâche pour envoyer</T>
    </View>
  ) : (
    <TextInput ref={champ} value={texte} onChangeText={setTexte} placeholder={accueil ? 'Écris ici…' : 'Message'} placeholderTextColor="#857F72"
      style={[styles.champ, accueil && styles.champAccueil]} multiline maxLength={2000} accessibilityLabel="Écrire un message"
      submitBehavior="blurAndSubmit" numberOfLines={Platform.OS === 'web' ? 1 : undefined}
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
  );
  const boutonEnvoi = texte.trim() ? (
    <Pressable accessibilityRole="button" accessibilityLabel="Envoyer" onPress={() => ecrire(texte)}>
      <RondVert taille={accueil ? 44 : 40}><PaperPlaneTilt size={21} color={couleurs.blanc} weight="fill" /></RondVert>
    </Pressable>
  ) : (
    <Pressable accessibilityRole="button" accessibilityLabel="Garder le doigt appuyé pour parler en wolof"
      onPressIn={() => void commencerVocal()} onPressOut={() => { relache.current = true; void finirVocal(); }}>
      <RondVert actif={ecoute} taille={accueil ? 44 : 40}><Microphone size={22} color={couleurs.blanc} weight="fill" /></RondVert>
    </Pressable>
  );
  const boutonPhoto = (taille: number) => (
    <Pressable accessibilityRole="button" accessibilityLabel="Envoyer une photo de ma plante" hitSlop={6}
      onPress={() => setMenuPhoto((v) => !v)}
      style={[styles.outil, { width: taille, height: taille, borderRadius: taille / 2 }, accueil && styles.outilAccueil, menuPhoto && styles.outilActif]}>
      {menuPhoto ? <X size={20} color={couleurs.foret} weight="bold" /> : <Camera size={22} color={couleurs.foret} />}
    </Pressable>
  );

  const basDeLEcran = (
    <View style={[styles.bas, { paddingBottom: (clavierSysteme ? 8 : 12) + (clavierSysteme ? 0 : marges.bottom) }]}>
      {accueil ? (
        <>
          <View style={styles.puces}>
            {([['langue:wo', 'Wolof', SpeakerHigh], ['langue:fr', 'Français', ChatText]] as const).map(([action, nom, Icone]) => (
              <Pressable key={action} accessibilityRole="button" onPress={() => choisirLangue(action)}
                style={({ pressed }) => [styles.puce, pressed && styles.piluleAppuyee]}>
                <Icone size={18} color={couleurs.foret} weight="duotone" />
                <T style={styles.textePuce}>{nom}</T>
              </Pressable>
            ))}
          </View>
          <View style={styles.ligneAccueil}>
            {boutonPhoto(48)}
            <View style={styles.piluleSaisie}>{champSaisie}{boutonEnvoi}</View>
          </View>
        </>
      ) : (
        <View style={styles.carteSaisie}>
          {champSaisie}
          <View style={styles.ligneOutils}>
            {boutonPhoto(36)}
            <View style={{ flex: 1 }} />
            {boutonEnvoi}
          </View>
        </View>
      )}

      {menuPhoto ? (
        <View style={styles.menuPhoto}>
          <Pressable accessibilityRole="button" onPress={() => void choisirPhoto('camera')} style={styles.choixPhoto}>
            <Camera size={26} color={couleurs.foret} weight="duotone" />
            <T style={styles.texteBouton}>Appareil photo</T>
          </Pressable>
          <Pressable accessibilityRole="button" onPress={() => void choisirPhoto('galerie')} style={styles.choixPhoto}>
            <Images size={26} color={couleurs.foret} weight="duotone" />
            <T style={styles.texteBouton}>Galerie</T>
          </Pressable>
        </View>
      ) : null}

      {afficherBoutons && !accueil ? (
        <View style={styles.boutons}>
          {/* Un bouton par ligne, dans l'ordre des numéros (demande de Salam, 21 nov) : la note vocale dit
              « le deux », l'agriculteur compte les lignes. */}
          {boutons.map((b, i) => (
            <Pressable key={b.bouton} accessibilityRole="button" onPress={() => toucherBouton(b.texte, b.bouton)}
              style={({ pressed }) => [styles.pilule, i === 0 && styles.piluleTest, pressed && styles.piluleAppuyee]}>
              <T style={styles.texteBouton} numberOfLines={2}>{b.texte}</T>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
  );

  return (
    <KeyboardAvoidingView style={styles.ecran} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      {/* Fond : dégradé vert tendre → crème → sable, paysage des Niayes en bas */}
      <LinearGradient colors={accueil ? [couleurs.pousse, couleurs.carte, couleurs.carte, couleurs.soleilClair] : [couleurs.pousse, '#EDF2E2', couleurs.sable]}
        locations={accueil ? [0, 0.32, 0.62, 1] : [0, 0.45, 1]} style={StyleSheet.absoluteFill} />
      {accueil ? <View style={styles.paysage} pointerEvents="none"><Paysage hauteur={180} /></View> : null}

      {accueil ? (
        <View style={[styles.enteteAccueil, { paddingTop: marges.top + 12 }]}>
          <View style={{ width: 46 }} />
          <T style={styles.nomCentre}>TerraMind</T>
          <Pressable accessibilityRole="button" accessibilityLabel="Réécouter le message vocal" hitSlop={8}
            onPress={() => derniereVoix && basculer(derniereVoix.id, derniereVoix.voix!)} style={styles.rondEntete}>
            <SpeakerHigh size={22} color={couleurs.foret} weight="bold" />
          </Pressable>
        </View>
      ) : (
        <View style={[styles.entete, { paddingTop: marges.top + 12 }]}>
          <Avatar taille={46} />
          <View style={{ flex: 1 }}>
            <T style={styles.nom}>TerraMind</T>
            <View style={styles.ligneStatut}>
              <View style={styles.pointVert} />
              <T style={styles.statut} numberOfLines={1}>{occupe ? 'écrit…' : 'Assistant maraîchage'}</T>
            </View>
          </View>
          {/* Langue : explicite (le mot, pas seulement une icône) ; touche → la question de la langue, dite en wolof. */}
          <Pressable accessibilityRole="button" accessibilityLabel="Changer de langue" hitSlop={6}
            onPress={() => { poster({ de: 'moi', texte: '/langue' }); envoyer({ texte: '/langue' }); }} style={styles.piluleLangue}>
            <Translate size={18} color={couleurs.foret} weight="bold" />
            <T style={styles.texteLangue}>{langue === 'wo' ? 'Wolof' : 'Français'}</T>
            <CaretDown size={13} color={couleurs.foret} weight="bold" />
          </Pressable>
        </View>
      )}

      {accueil ? (
        <View style={styles.centreAccueil}>
          <Pressable accessibilityRole="button" accessibilityLabel="Réécouter le message vocal"
            onPress={() => derniereVoix && basculer(derniereVoix.id, derniereVoix.voix!)} style={styles.halo}>
            <Halo />
            <Avatar taille={96} />
          </Pressable>
          <T style={styles.titreAccueil}>Ton assistant{'\n'}pour le maraîchage</T>
          <T style={styles.sousTitreAccueil}>{insecables('Choisis ta langue : touche « Wolof » ou « Français ».')}</T>
          {/* La question de la langue, dite en wolof : visible et réécoutable (elle se lit seule à l'arrivée). */}
          {derniereVoix ? (
            <View style={styles.vocalAccueil}><BulleVocale id={derniereVoix.id} adresse={derniereVoix.voix!} /></View>
          ) : null}
        </View>
      ) : (
        <View style={styles.feuille}>
          <View style={styles.paysageFeuille} pointerEvents="none"><Paysage hauteur={290} decor={false} /></View>
          <FlatList
            ref={liste}
            contentContainerStyle={styles.filContenu}
            data={messages}
            keyExtractor={(m) => m.id}
            onContentSizeChange={() => { if (suivreLaFin.current) defiler(); }}
            initialNumToRender={150}
            onScrollToIndexFailed={() => liste.current?.scrollToEnd({ animated: true })}
            renderItem={({ item, index }) => (
              <>
                {index === 0 || !memeJour(messages[index - 1].heure, item.heure)
                  ? <View style={styles.jour}><T style={styles.texteJour}>{jourFr(item.heure)}</T></View> : null}
                <Bulle m={item} suivant={messages[index + 1]} onAction={(action) => {
                  poster({ de: 'moi', texte: libelleAction(item.boutons, action) });
                  envoyer({ action });
                }} />
              </>
            )}
            ListFooterComponent={occupe ? <Ecrit /> : undefined}
          />
          {/* fondu sous l'en-tête : les messages ne sont pas coupés net */}
          <LinearGradient colors={[couleurs.carte, 'rgba(255,252,246,0)']} style={styles.fondu} pointerEvents="none" />
          {basDeLEcran}
        </View>
      )}

      {accueil ? basDeLEcran : null}
    </KeyboardAvoidingView>
  );
}

/** Halo diffus autour de l'orbe de l'accueil : dégradé radial, sans bord. */
function Halo() {
  return (
    <Svg width={240} height={240} style={styles.svgHalo} pointerEvents="none">
      <Defs>
        <RadialGradient id="halo" cx="50%" cy="50%" r="50%">
          <Stop offset="0" stopColor={couleurs.pousse} stopOpacity={0.95} />
          <Stop offset="0.45" stopColor={couleurs.pousse} stopOpacity={0.55} />
          <Stop offset="0.75" stopColor={couleurs.soleilClair} stopOpacity={0.25} />
          <Stop offset="1" stopColor={couleurs.soleilClair} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Rect x={0} y={0} width={240} height={240} fill="url(#halo)" />
    </Svg>
  );
}

/** Avatar de TerraMind : une feuille sur un rond dégradé (vert tendre → soleil). */
function Avatar({ taille }: { taille: number }) {
  return (
    <LinearGradient colors={[couleurs.blanc, couleurs.pousse, couleurs.soleilClair]} start={{ x: 0.1, y: 0 }} end={{ x: 0.9, y: 1 }}
      style={[styles.avatar, { width: taille, height: taille, borderRadius: taille / 2 }]}>
      <Leaf size={taille * 0.5} color={couleurs.foret} weight="duotone" />
    </LinearGradient>
  );
}

function RondVert({ children, actif, taille = 44 }: { children: ReactNode; actif?: boolean; taille?: number }) {
  return (
    <LinearGradient colors={actif ? [couleurs.terre, '#8F3F1E'] : [couleurs.feuille, couleurs.foret]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
      style={[styles.rondVert, { width: taille, height: taille, borderRadius: taille / 2 }, actif && { transform: [{ scale: 1.12 }] }]}>
      {children}
    </LinearGradient>
  );
}

/** « TerraMind écrit » : trois points qui respirent. */
function Ecrit() {
  const [v] = useState(() => new Animated.Value(0));
  useEffect(() => {
    const boucle = Animated.loop(Animated.timing(v, { toValue: 1, duration: 1100, useNativeDriver: true }));
    boucle.start();
    return () => boucle.stop();
  }, [v]);
  return (
    <View style={[styles.ligneBot, { marginTop: 10 }]}>
      <Avatar taille={34} />
      <View style={[styles.bulle, styles.bulleBot, styles.points]}>
        {[0, 1, 2].map((i) => (
          <Animated.View key={i} style={[styles.point, {
            opacity: v.interpolate({ inputRange: [0, (i + 0.5) / 4, (i + 1.5) / 4, 1], outputRange: [0.3, 1, 0.3, 0.3], extrapolate: 'clamp' }),
          }]} />
        ))}
      </View>
    </View>
  );
}

function Bulle({ m, suivant, onAction }: { m: Message; suivant?: Message; onAction: (action: string) => void }) {
  const moi = m.de === 'moi';
  // Heure et avatar seulement sous le dernier message d'une suite du même côté, comme dans la maquette.
  const finDeSuite = !suivant || suivant.de !== m.de || suivant.heure - m.heure > 60_000;
  const contenu = (
    <View style={[styles.bulle, moi ? styles.bulleMoi : styles.bulleBot, m.photo ? styles.bullePhoto : null]}>
      {m.photo ? <Image source={{ uri: m.photo }} style={styles.photo} accessibilityLabel="Photo envoyée" /> : null}
      {m.voix ? <BulleVocale id={m.id} adresse={m.voix} moi={moi} /> : null}
      {m.position ? (
        <View style={styles.position}>
          <View style={styles.pastillePosition}><MapPin size={18} color={couleurs.blanc} weight="fill" /></View>
          <T style={styles.texteBulle}>Position de mon champ</T>
        </View>
      ) : null}
      {m.texte ? <TexteRiche texte={m.texte} style={styles.texteBulle} /> : null}
    </View>
  );
  return (
    <View style={[styles.message, finDeSuite && { marginBottom: 10 }]}>
      {moi ? <View style={styles.ligneMoi}>{contenu}</View> : (
        <>
          <View style={styles.ligneBot}>
            {finDeSuite ? <Avatar taille={34} /> : <View style={{ width: 34 }} />}
            <View style={{ flex: 1, alignItems: 'flex-start' }}>{contenu}</View>
          </View>
          {m.boutons?.length ? (
            <View style={styles.reponses}>
              {m.boutons.flat().map((b) => (
                <Pressable key={b.action} accessibilityRole="button" onPress={() => onAction(b.action)}
                  style={({ pressed }) => [styles.reponse, pressed && styles.piluleAppuyee]}>
                  <T style={styles.texteReponse}>{b.texte}</T>
                </Pressable>
              ))}
            </View>
          ) : null}
        </>
      )}
      {finDeSuite ? <T style={[styles.heure, moi ? { alignSelf: 'flex-end' } : { marginLeft: 44 }]}>{heureFr(m.heure)}</T> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  ecran: { flex: 1, backgroundColor: couleurs.sable },
  paysage: { position: 'absolute', left: 0, right: 0, bottom: 0 },
  entete: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 18, paddingBottom: 18 },
  avatar: {
    alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: couleurs.blanc,
    shadowColor: couleurs.foret, shadowOpacity: 0.15, shadowRadius: 6, shadowOffset: { width: 0, height: 2 }, elevation: 2,
  },
  nom: { fontFamily: polices.titreDemi, fontSize: 20, lineHeight: 23, color: couleurs.encre, letterSpacing: -0.2 },
  ligneStatut: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 1 },
  pointVert: { width: 8, height: 8, borderRadius: 4, backgroundColor: couleurs.feuille },
  statut: { fontFamily: polices.texte, fontSize: 12.5, color: couleurs.encreDouce },
  enteteAccueil: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 18, paddingBottom: 12 },
  nomCentre: { flex: 1, textAlign: 'center', fontFamily: polices.titreDemi, fontSize: 21, color: couleurs.encre },
  piluleLangue: {
    flexDirection: 'row', alignItems: 'center', gap: 5, height: 44, paddingHorizontal: 12, borderRadius: 22, backgroundColor: couleurs.blanc,
    shadowColor: couleurs.foret, shadowOpacity: 0.08, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2,
  },
  texteLangue: { fontFamily: polices.texteGras, fontSize: 14.5, color: couleurs.foret },
  centreAccueil: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32, paddingBottom: 30 },
  vocalAccueil: {
    marginTop: 18, backgroundColor: couleurs.blanc, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 10,
    shadowColor: couleurs.foret, shadowOpacity: 0.08, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2,
  },
  halo: { width: 96, height: 96, alignItems: 'center', justifyContent: 'center' },
  svgHalo: { position: 'absolute', left: -72, top: -72 },
  titreAccueil: { marginTop: 24, fontFamily: polices.titreDemi, fontSize: 28, lineHeight: 33, color: couleurs.encre, textAlign: 'center', letterSpacing: -0.5 },
  sousTitreAccueil: { marginTop: 12, maxWidth: 300, fontFamily: polices.texte, fontSize: 16, lineHeight: 22, color: couleurs.encreDouce, textAlign: 'center' },
  puces: { flexDirection: 'row', gap: 8, justifyContent: 'center' },
  puce: {
    flexDirection: 'row', alignItems: 'center', gap: 8, height: 48, paddingHorizontal: 22, borderRadius: 24,
    backgroundColor: 'rgba(255,255,255,0.9)', borderWidth: 1, borderColor: couleurs.blanc,
    shadowColor: couleurs.foret, shadowOpacity: 0.08, shadowRadius: 6, shadowOffset: { width: 0, height: 2 }, elevation: 2,
  },
  textePuce: { fontFamily: polices.texte, fontSize: 16, color: couleurs.foret },
  ligneAccueil: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 8 },
  outilAccueil: { backgroundColor: couleurs.blanc, borderColor: couleurs.blanc, elevation: 2,
    shadowColor: couleurs.foret, shadowOpacity: 0.08, shadowRadius: 6, shadowOffset: { width: 0, height: 2 } },
  piluleSaisie: {
    flex: 1, flexDirection: 'row', alignItems: 'center', minHeight: 52, borderRadius: 26, backgroundColor: couleurs.blanc,
    paddingLeft: 18, paddingRight: 5, borderWidth: 3, borderColor: 'rgba(220,235,217,0.8)',
  },
  champAccueil: { flex: 1, minHeight: 40, paddingTop: 10, paddingBottom: 8 },
  rondEntete: {
    width: 46, height: 46, borderRadius: 23, backgroundColor: couleurs.blanc, alignItems: 'center', justifyContent: 'center',
    shadowColor: couleurs.foret, shadowOpacity: 0.08, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2,
  },
  feuille: {
    flex: 1, backgroundColor: couleurs.carte, borderTopLeftRadius: 30, borderTopRightRadius: 30, overflow: 'hidden',
  },
  paysageFeuille: { position: 'absolute', left: 0, right: 0, bottom: 0, opacity: 0.9 },
  fondu: { position: 'absolute', top: 0, left: 0, right: 0, height: 32 },
  filContenu: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8 },
  jour: { alignSelf: 'center', backgroundColor: C.pastilleJour, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 5, marginVertical: 8 },
  texteJour: { fontFamily: polices.texte, fontSize: 13, color: couleurs.encreDouce },
  message: { marginBottom: 4 },
  ligneMoi: { alignItems: 'flex-end', paddingLeft: 48 },
  ligneBot: { flexDirection: 'row', alignItems: 'flex-end', gap: 10, paddingRight: 30 },
  bulle: { borderRadius: 16, paddingHorizontal: 14, paddingVertical: 10, gap: 8, maxWidth: '100%' },
  bulleBot: { backgroundColor: C.bulleBot, borderBottomLeftRadius: 6 },
  bulleMoi: { backgroundColor: C.bulleMoi, borderBottomRightRadius: 6, paddingHorizontal: 12 },
  bullePhoto: { padding: 4 },
  photo: { width: 210, height: 210, borderRadius: 16 },
  texteBulle: { fontFamily: polices.texte, fontSize: 16, lineHeight: 22.5, color: couleurs.encre },
  heure: { fontFamily: polices.texte, fontSize: 12, lineHeight: 14, color: C.heure, marginTop: 4 },
  position: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  pastillePosition: { width: 30, height: 30, borderRadius: 15, backgroundColor: couleurs.terre, alignItems: 'center', justifyContent: 'center' },
  reponses: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginLeft: 44, marginTop: 8, paddingRight: 10 },
  reponse: {
    minHeight: 44, borderRadius: 999, paddingHorizontal: 18, justifyContent: 'center', backgroundColor: couleurs.blanc,
    borderWidth: 1.5, borderColor: couleurs.pousse,
  },
  texteReponse: { fontFamily: polices.texteGras, fontSize: 15, color: couleurs.foret },
  points: { flexDirection: 'row', gap: 5, paddingVertical: 14 },
  point: { width: 8, height: 8, borderRadius: 4, backgroundColor: couleurs.feuille },
  bas: { paddingHorizontal: 8, paddingTop: 6, gap: 8 },
  carteSaisie: {
    backgroundColor: couleurs.blanc, borderRadius: 26, paddingHorizontal: 12, paddingTop: 8, paddingBottom: 10, minHeight: 112,
    justifyContent: 'space-between',
    borderWidth: 4, borderColor: 'rgba(220,235,217,0.75)', // halo vert tendre autour de la carte, comme la maquette
    shadowColor: couleurs.foret, shadowOpacity: 0.12, shadowRadius: 16, shadowOffset: { width: 0, height: 4 }, elevation: 4,
  },
  champ: {
    minHeight: 34, maxHeight: 110, paddingHorizontal: 4, paddingTop: 8, paddingBottom: 2,
    fontFamily: polices.texte, fontSize: 16, color: couleurs.encre,
  },
  enregistrement: { flexDirection: 'row', alignItems: 'center', gap: 10, minHeight: 38, paddingHorizontal: 4 },
  pointRouge: { width: 10, height: 10, borderRadius: 5, backgroundColor: couleurs.terre },
  texteEnregistrement: { fontFamily: polices.texteGras, fontSize: 15, color: couleurs.terre },
  ligneOutils: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  outil: { width: 40, height: 40, borderRadius: 20, borderWidth: 1.5, borderColor: C.bordDoux, alignItems: 'center', justifyContent: 'center' },
  outilActif: { backgroundColor: couleurs.pousse, borderColor: couleurs.pousse },
  rondVert: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  menuPhoto: { flexDirection: 'row', gap: 8 },
  choixPhoto: {
    flex: 1, alignItems: 'center', gap: 6, paddingVertical: 14, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.92)',
    borderWidth: 1, borderColor: couleurs.blanc,
  },
  boutons: { gap: 8, paddingHorizontal: 4 },
  pilule: {
    minHeight: 46, borderRadius: 23, paddingHorizontal: 12, paddingVertical: 5, alignItems: 'center', justifyContent: 'center',
    backgroundColor: couleurs.blanc, borderWidth: 1, borderColor: C.bordDoux,
    shadowColor: couleurs.foret, shadowOpacity: 0.06, shadowRadius: 4, shadowOffset: { width: 0, height: 1 }, elevation: 1,
  },
  piluleTest: { backgroundColor: couleurs.soleilClair, borderColor: '#F0D99A' },
  piluleAppuyee: { backgroundColor: couleurs.pousse },
  texteBouton: { fontFamily: polices.texteGras, fontSize: 14, lineHeight: 18, color: couleurs.foret, textAlign: 'center' },
});
