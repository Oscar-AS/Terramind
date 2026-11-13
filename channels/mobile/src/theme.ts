// Identité « Terre des Niayes » : sable, vert forêt, terre cuite.
// Références : Plantix (parcours centré sur l'appareil photo, icônes illustrées), Farmer.Chat
// (texte + voix), recommandations « organic biophilic » (formes douces, tons de terre).
// Contrastes vérifiés : texte encre sur sable 14:1, blanc sur forêt 9:1, blanc sur terre cuite 4,6:1.
export const couleurs = {
  // fonds
  sable: '#F5EFE3',
  sableFonce: '#EADFC9',
  carte: '#FFFCF6',
  // marque
  foret: '#1F4D3A',
  feuille: '#3F8F5F',
  pousse: '#DCEBD9',
  // signaux
  terre: '#B4532A',
  terreClair: '#F6DCCB',
  soleil: '#E3A72F',
  soleilClair: '#FBEFCF',
  // texte
  encre: '#1B2620',
  encreDouce: '#4E5A52',
  trait: '#E2D8C4',
  blanc: '#FFFFFF',
} as const;

// Compatibilité avec les anciens noms (à retirer quand tout sera migré).
export const anciens = {
  vert: couleurs.feuille,
  vertClair: couleurs.pousse,
  ocre: couleurs.soleil,
  rouge: couleurs.terre,
  texte: couleurs.encre,
  texteDoux: couleurs.encreDouce,
  fond: couleurs.sable,
  blanc: couleurs.blanc,
};

export const polices = {
  titre: 'BricolageGrotesque_800ExtraBold',
  titreMoyen: 'BricolageGrotesque_700Bold',
  texte: 'Figtree_500Medium',
  texteGras: 'Figtree_700Bold',
} as const;

export const tailles = {
  boutonMin: 64, // cibles tactiles larges (utilisateurs peu habitués aux écrans)
  rayon: 24,
  rayonPetit: 16,
  marge: 20,
  titre: 28,
  corps: 18,
} as const;

export const ombre = {
  shadowColor: '#1F4D3A',
  shadowOpacity: 0.08,
  shadowRadius: 16,
  shadowOffset: { width: 0, height: 6 },
  elevation: 2,
} as const;
