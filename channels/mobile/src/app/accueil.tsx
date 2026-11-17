import { LinearGradient } from 'expo-linear-gradient';
import { router, useFocusEffect } from 'expo-router';
import { Bell, CalendarCheck, Camera, ChatCircleText, type Icon, MapPin, Plant, Translate } from 'phosphor-react-native';
import { useCallback, useState } from 'react';
import { ImageBackground, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Apparition, Pastille, T } from '@/components/ui';
import { CULTURES, profil } from '@/profil';
import { couleurs, ombre, tailles } from '@/theme';
import { dateFr } from '@/format';

const PHOTO = require('../../assets/illustrations/accueil.jpg');

function Tuile({ Icone, titre, sous, onPress, fond = couleurs.carte }: { Icone: Icon; titre: string; sous: string; onPress: () => void; fond?: string }) {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={titre} onPress={onPress}
      style={({ pressed }) => [styles.tuile, { backgroundColor: fond }, pressed && { transform: [{ scale: 0.97 }] }]}>
      <Pastille Icone={Icone} />
      <T v="corpsGras" style={{ fontSize: 19 }}>{titre}</T>
      <T v="petit">{sous}</T>
    </Pressable>
  );
}

// Accueil : l'action principale (photo de la plante) en grand, le reste en tuiles.
export default function Accueil() {
  const [p, setP] = useState(profil.lire());
  useFocusEffect(useCallback(() => setP(profil.lire()), []));
  const culture = CULTURES.find((c) => c.id === p.culture);

  return (
    <SafeAreaView style={styles.page}>
      <ScrollView contentContainerStyle={styles.contenu} showsVerticalScrollIndicator={false}>
        <Apparition ordre={0} style={styles.haut}>
          <View style={{ flex: 1, gap: 6 }}>
            <T v="titre">{p.langue === 'wo' ? 'Na nga def ?' : 'Bonjour'}</T>
            <View style={styles.zone}>
              <MapPin size={16} color={couleurs.encreDouce} weight="fill" />
              <T v="petit">{p.position?.nom ?? 'Ton champ'}</T>
            </View>
          </View>
          {/* Changer de langue à tout moment (en wolof, les réponses se lisent à voix haute). */}
          <Pressable accessibilityRole="button" accessibilityLabel={p.langue === 'wo' ? 'Passer en français' : 'Passer en wolof'}
            onPress={() => setP(profil.ecrire({ langue: p.langue === 'wo' ? 'fr' : 'wo' }))} style={styles.langue} hitSlop={8}>
            <Translate size={22} color={couleurs.foret} weight="duotone" />
            <T v="etiquette" style={{ color: couleurs.foret }}>{p.langue === 'wo' ? 'Français' : 'Wolof'}</T>
          </Pressable>
        </Apparition>

        <Apparition ordre={1}>
          <Pressable accessibilityRole="button" accessibilityLabel="Ma plante est malade : prendre une photo"
            onPress={() => router.push('/diagnostic')} style={({ pressed }) => pressed && { transform: [{ scale: 0.98 }] }}>
            <ImageBackground source={PHOTO} style={styles.hero} imageStyle={styles.heroImage} resizeMode="cover">
              <LinearGradient colors={['rgba(31,77,58,0.05)', 'rgba(31,77,58,0.92)']} locations={[0.1, 0.75]} style={StyleSheet.absoluteFill} />
              <View style={styles.heroBas}>
                <T v="etiquette" style={{ color: couleurs.pousse }}>Diagnostic</T>
                <T v="titre" style={{ color: couleurs.blanc, fontSize: 30 }}>Voir si ma plante est malade</T>
                <View style={styles.heroBouton}>
                  <Camera size={26} color={couleurs.foret} weight="duotone" />
                  <T v="corpsGras" style={{ color: couleurs.foret }}>Prendre ma plante en photo</T>
                </View>
              </View>
            </ImageBackground>
          </Pressable>
        </Apparition>

        {culture ? (
          <Apparition ordre={2}>
            <Pressable accessibilityRole="button" accessibilityLabel={`Alertes pour ${culture.libelle}`} onPress={() => router.push('/alertes')}
              style={({ pressed }) => [styles.alerte, pressed && { opacity: 0.85 }]}>
              <Pastille Icone={Bell} couleur={couleurs.terre} fond={couleurs.carte} />
              <View style={{ flex: 1 }}>
                <T v="corpsGras">Que dois-je retenir de la météo de cette semaine ?</T>
                <T v="petit">{culture.icone} {culture.libelle} · météo de ton champ</T>
              </View>
            </Pressable>
          </Apparition>
        ) : null}

        <Apparition ordre={3} style={styles.grille}>
          <Tuile Icone={Plant} titre="Que planter dans mon champ ?" sous="Selon ton sol et la saison" onPress={() => router.push('/plan')} />
          <Tuile Icone={ChatCircleText} titre="J'ai une question à te poser" sous="Réponse tirée des fiches" onPress={() => router.push('/question')} />
        </Apparition>
        <Apparition ordre={4}>
          <Tuile Icone={CalendarCheck} titre={culture ? 'Changer ma culture' : "J'ai planté"}
            sous={culture ? `${culture.libelle}, plantée le ${dateFr(p.dateRepiquage)}` : 'Pour recevoir les alertes'}
            onPress={() => router.push('/cultures')} fond={couleurs.pousse} />
        </Apparition>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: couleurs.sable },
  contenu: { padding: tailles.marge, gap: 16, paddingBottom: 40 },
  haut: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingTop: 8 },
  zone: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  langue: { flexDirection: 'row', gap: 6, paddingHorizontal: 14, height: 52, borderRadius: 26, backgroundColor: couleurs.carte, borderWidth: 1, borderColor: couleurs.trait, alignItems: 'center', justifyContent: 'center' },
  hero: { height: 340, justifyContent: 'flex-end', borderRadius: 28, overflow: 'hidden', ...ombre },
  heroImage: { borderRadius: 28 },
  heroBas: { padding: 20, gap: 8 },
  heroBouton: {
    flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: couleurs.carte, borderRadius: 18,
    paddingVertical: 16, paddingHorizontal: 16, marginTop: 8,
  },
  alerte: {
    flexDirection: 'row', alignItems: 'center', gap: 14, backgroundColor: couleurs.terreClair, borderRadius: tailles.rayon,
    padding: 14, borderWidth: 1, borderColor: '#EBC2AA',
  },
  grille: { flexDirection: 'row', gap: 12 },
  tuile: {
    flex: 1, minHeight: 150, borderRadius: tailles.rayon, padding: 16, gap: 8, borderWidth: 1, borderColor: couleurs.trait,
    justifyContent: 'flex-end', ...ombre,
  },
});
