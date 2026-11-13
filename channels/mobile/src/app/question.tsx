import { useState } from 'react';
import { StyleSheet, Text, TextInput } from 'react-native';

import { poserQuestion } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement } from '@/components/Etat';
import { GrosBouton } from '@/components/GrosBouton';
import { couleurs, tailles } from '@/theme';

// Étape 7 : question libre (POST /v1/chat). La note vocale arrivera avec la reconnaissance vocale
// wolof ; en attendant, la question s'écrit. Le moteur ne répond qu'à partir des fiches validées (D8).
export default function Question() {
  const [texte, setTexte] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [reponse, setReponse] = useState<string | null>(null);

  const envoyer = async () => {
    if (!texte.trim()) return;
    setEnvoi(true);
    setReponse(null);
    try {
      setReponse((await poserQuestion(texte.trim())).message.texte);
    } catch (e) {
      setReponse((e as Error).message);
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <Ecran titre="Poser une question">
      <TextInput
        value={texte}
        onChangeText={setTexte}
        placeholder="Écris ta question ici"
        multiline
        style={styles.champ}
        accessibilityLabel="Ta question"
      />
      <GrosBouton icone="📨" libelle="Envoyer" onPress={envoyer} />
      {envoi ? <Chargement icone="💬" texte="Je cherche dans les fiches…" /> : null}
      {reponse ? <Text style={styles.reponse}>{reponse}</Text> : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  champ: {
    minHeight: 120, borderRadius: tailles.rayon, backgroundColor: couleurs.blanc, padding: 16,
    fontSize: 19, color: couleurs.texte, textAlignVertical: 'top', borderWidth: 2, borderColor: couleurs.vertClair,
  },
  reponse: { fontSize: 19, color: couleurs.texte, lineHeight: 27, backgroundColor: couleurs.vertClair, borderRadius: tailles.rayon, padding: 16 },
});
