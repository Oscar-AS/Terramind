// Configuration Tailwind v3 du site vitrine. Compiler : voir README.md (npx tailwindcss@3 …).
module.exports = {
  content: ['./index.html'],
  theme: {
    extend: {
      colors: {
        foret: '#1F4D3A', feuille: '#3F8F5F', vert: '#2F6B4A', pousse: '#DCEBD9', sable: '#F5EFE3', sablef: '#EADFC9',
        carte: '#FFFCF6', soleil: '#E3A72F', soleilc: '#FBEFCF', terre: '#B4532A', encre: '#1B2620', encred: '#4E5A52',
        trait: '#E2D8C4', clair: '#CFE3D3', sombre2: '#2C3A32', fondimg: '#F7F1E4',
      },
      fontFamily: { titre: ['Outfit', 'system-ui', 'sans-serif'], corps: ['"Work Sans"', 'system-ui', 'sans-serif'] },
    },
  },
};
