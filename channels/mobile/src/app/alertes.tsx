import { router } from 'expo-router';
import type { Icon } from 'phosphor-react-native';
import { Bug } from 'phosphor-react-native/src/icons/Bug';
import { CalendarCheck } from 'phosphor-react-native/src/icons/CalendarCheck';
import { CloudRain } from 'phosphor-react-native/src/icons/CloudRain';
import { CloudSun } from 'phosphor-react-native/src/icons/CloudSun';
import { Eye } from 'phosphor-react-native/src/icons/Eye';
import { EyeSlash } from 'phosphor-react-native/src/icons/EyeSlash';
import { Leaf } from 'phosphor-react-native/src/icons/Leaf';
import { SealCheck } from 'phosphor-react-native/src/icons/SealCheck';
import { useEffect, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { type Alertes, demanderAlertes, envoyerRetour, type PhraseWolof, type Reponse } from '@/api';
import { Ecran } from '@/components/Ecran';
import { Chargement, Erreur, Sources } from '@/components/Etat';
import { Apparition, Badge, Bouton, Carte, Pastille, T } from '@/components/ui';
import { BlocWolof, BoutonEcouter } from '@/components/Voix';
import { dateFr } from '@/format';
import { couleurs } from '@/theme';

// Étape 6 : risques météo de la semaine (POST /v1/alert) et retour de l'agriculteur (POST /v1/feedback).
const RISQUES: Record<string, { Icone: Icon; nom: string }> = {
  late_blight: { Icone: CloudRain, nom: 'Mildiou' },
  alternaria: { Icone: Leaf, nom: 'Alternariose' },
  tuta_absoluta: { Icone: Bug, nom: 'Mineuse de la tomate' },
  plutella_xylostella: { Icone: Bug, nom: 'Teigne du chou' },
  carrot_alternaria: { Icone: Leaf, nom: 'Alternariose de la carotte' },
  onion_downy_mildew: { Icone: CloudRain, nom: "Mildiou de l'oignon" },
  helicoverpa_armigera: { Icone: Bug, nom: 'Noctuelle (ver des fruits)' },
  date_requise: { Icone: Bug, nom: 'Insectes de ta culture' },
};


export default function AlertesEcran() {
  const [reponse, setReponse] = useState<Reponse<Alertes> | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [retours, setRetours] = useState<Record<string, boolean>>({});
  const [essai, setEssai] = useState(0);
  useEffect(() => {
    let actif = true;
    demanderAlertes().then((r) => (r.statut === 'erreur' ? actif && setErreur(r.message.texte) : actif && setReponse(r)))
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

  const wolof = reponse?.message.wolof;
  // En wolof, l'écran se lit en entier : l'introduction, puis chaque alerte (comme le bot).
  const voix = useMemo<PhraseWolof[] | undefined>(() => (wolof ? [
    ...wolof, ...(reponse?.donnees.alertes ?? []).flatMap((a) => (a.wo ? [a.wo] : [])),
  ] : undefined), [wolof, reponse]);

  if (reponse?.statut === 'culture_requise') {
    return (
      <Ecran titre="Alertes de la semaine">
        <T v="corps">{reponse.message.texte}</T>
        <Bouton libelle="J'ai planté" Icone={CalendarCheck} onPress={() => router.replace('/cultures')} />
      </Ecran>
    );
  }

  const actives = reponse?.donnees.alertes.filter((a) => a.niveau !== 'aucun') ?? [];
  const repondre = (id: string, vu: 'oui' | 'non') => {
    setRetours((r) => ({ ...r, [id]: true }));
    envoyerRetour(id, vu).catch(() => undefined); // un retour perdu ne bloque pas l'agriculteur
  };

  return (
    <Ecran titre="Alertes de la semaine" voix={voix}>
      {erreur ? <Erreur texte={erreur} onReessayer={charger} /> : null}
      {!erreur && !reponse ? <Chargement Icone={CloudSun} texte="Je regarde la météo de ton champ…" /> : null}
      {reponse ? (
        <>
          <Apparition ordre={0} style={styles.periode}>
            <CloudSun size={20} color={couleurs.encreDouce} weight="duotone" />
            <T v="petit">Météo du {dateFr(reponse.donnees.meteo.periode[0], false)} au {dateFr(reponse.donnees.meteo.periode[1], false)}</T>
          </Apparition>
          {wolof?.length && actives.length ? <Apparition ordre={1}><BlocWolof phrases={wolof} /></Apparition> : null}
          {actives.length === 0 ? (
            <Apparition ordre={1}>
              <Carte style={styles.calme}>
                <Pastille Icone={SealCheck} taille={72} />
                <T v="sousTitre" style={{ textAlign: 'center' }}>
                  {reponse.donnees.alertes.length === 0 ? 'Pas encore de surveillance' : 'Tout est calme'}
                </T>
                {wolof?.length ? <BlocWolof phrases={wolof} /> : <T v="corps" style={{ textAlign: 'center' }}>{reponse.message.texte}</T>}
              </Carte>
            </Apparition>
          ) : null}
          {actives.map((a, i) => {
            const r = RISQUES[a.risque] ?? { Icone: Bug, nom: a.risque };
            return (
              <Apparition key={a.id} ordre={i + 1}>
                <Carte>
                  <View style={styles.tete}>
                    <Pastille Icone={r.Icone} couleur={couleurs.terre} fond={couleurs.terreClair} taille={56} />
                    <View style={{ flex: 1, gap: 6 }}>
                      <T v="sousTitre">{r.nom}</T>
                      <Badge Icone={r.Icone} texte={a.niveau === 'favorable' ? 'Conditions favorables'
                        : a.niveau === 'date_requise' ? 'Date de plantation manquante' : 'À surveiller'}
                        couleur={couleurs.terre} fond={couleurs.terreClair} />
                    </View>
                  </View>
                  {a.wo ? (
                    <View style={styles.wolof}>
                      <T v="corpsGras">{a.wo.texte_wo}</T>
                      <BoutonEcouter phrases={[a.wo]} libelle="Écouter" />
                    </View>
                  ) : null}
                  <T v={a.wo ? 'petit' : 'corps'}>{a.conseil}</T>
                  {a.niveau === 'date_requise' ? null : retours[a.id] ? <T v="corpsGras" style={{ color: couleurs.feuille }}>{'Merci pour ta réponse.'}</T> : (
                    <>
                      <T v="petit">As-tu vu des signes dans ton champ ?</T>
                      <View style={styles.boutons}>
                        <View style={{ flex: 1 }}><Bouton libelle="Oui, j'ai vu" Icone={Eye} onPress={() => repondre(a.id, 'oui')} /></View>
                        <View style={{ flex: 1 }}><Bouton libelle="Rien vu" Icone={EyeSlash} onPress={() => repondre(a.id, 'non')} variante="clair" /></View>
                      </View>
                    </>
                  )}
                </Carte>
              </Apparition>
            );
          })}
          <Sources sources={reponse.sources} />
        </>
      ) : null}
    </Ecran>
  );
}

const styles = StyleSheet.create({
  periode: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  calme: { alignItems: 'center', paddingVertical: 28 },
  tete: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  boutons: { flexDirection: 'row', gap: 8 },
  wolof: { gap: 8, backgroundColor: couleurs.sable, borderRadius: 14, padding: 12 },
});
