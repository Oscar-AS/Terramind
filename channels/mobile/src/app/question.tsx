import { BookOpenText, ChatCircleText, PaperPlaneRight } from 'phosphor-react-native';
import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { poserQuestion, type Reponse, type Source } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Sources } from '@/components/Etat';
import { Apparition, Carte, Pastille, T } from '@/components/ui';
import { couleurs, polices, tailles } from '@/theme';

// Étape 7 : question libre (POST /v1/chat). Le moteur ne répond qu'à partir des fiches (D8).
// La note vocale arrivera avec la reconnaissance vocale wolof ; en attendant, la question s'écrit.
const EXEMPLES = ['Ma tomate a des taches brunes avec des cercles', "Quand semer l'oignon ?", "L'eau de mon puits est salée"];

export default function Question() {
  const [texte, setTexte] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [reponse, setReponse] = useState<{ texte: string; ok: boolean; sources: Source[] } | null>(null);

  const envoyer = async (q = texte) => {
    if (!q.trim()) return;
    setTexte(q);
    setEnvoi(true);
    setReponse(null);
    try {
      const r: Reponse<unknown> = await poserQuestion(q.trim());
      setReponse({ texte: r.message.texte, ok: r.statut === 'ok', sources: r.sources });
    } catch (e) {
      setReponse({ texte: (e as Error).message, ok: false, sources: [] });
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <Ecran titre="Poser une question">
      <View style={styles.saisie}>
        <TextInput value={texte} onChangeText={setTexte} placeholder="Écris ta question ici" placeholderTextColor={couleurs.encreDouce}
          multiline maxLength={2000} style={styles.champ} accessibilityLabel="Ta question" />
        <Pressable accessibilityRole="button" accessibilityLabel="Envoyer" onPress={() => envoyer()} disabled={envoi}
          style={({ pressed }) => [styles.envoyer, (pressed || envoi) && { opacity: 0.7 }]}>
          <PaperPlaneRight size={26} color={couleurs.blanc} weight="fill" />
        </Pressable>
      </View>
      {!reponse && !envoi ? (
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
      {envoi ? <Chargement Icone={BookOpenText} texte="Je cherche dans les fiches…" /> : null}
      {reponse ? (
        <Apparition>
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
  exemple: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 14, borderRadius: 16, backgroundColor: couleurs.carte, borderWidth: 1, borderColor: couleurs.trait },
  tete: { flexDirection: 'row', alignItems: 'center', gap: 10 },
});
