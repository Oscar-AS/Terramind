// Décor du bas de l'écran : les dunes et les champs des Niayes, dessinés (pas de photo, pas d'image générée).
import Svg, { Circle, Ellipse, Path } from 'react-native-svg';

import { couleurs } from '@/theme';

export function Paysage({ hauteur = 190 }: { hauteur?: number }) {
  return (
    <Svg width="100%" height={hauteur} viewBox="0 0 400 190" preserveAspectRatio="xMidYMax slice">
      {/* dune du fond */}
      <Path d="M0 96 C70 62 130 70 200 88 C270 106 330 66 400 74 L400 190 L0 190 Z" fill={couleurs.sableFonce} />
      {/* colline verte */}
      <Path d="M0 120 C60 96 120 100 190 116 C260 132 330 104 400 108 L400 190 L0 190 Z" fill={couleurs.pousse} />
      {/* champ du premier plan */}
      <Path d="M0 146 C80 128 160 134 230 142 C300 150 350 136 400 138 L400 190 L0 190 Z" fill="#B7D6AE" />
      {/* sillons */}
      <Path d="M20 170 C110 156 220 160 380 158" stroke="#9CC592" strokeWidth={2} fill="none" />
      <Path d="M0 182 C120 168 240 172 400 170" stroke="#9CC592" strokeWidth={2} fill="none" />
      {/* plants */}
      {[30, 62, 94, 126, 158, 190, 222, 254, 286, 318, 350, 382].map((x, i) => (
        <Ellipse key={x} cx={x} cy={i % 2 ? 160 : 164} rx={5} ry={3.5} fill={couleurs.feuille} opacity={0.75} />
      ))}
      {/* quelques fleurs */}
      {[[48, 150], [140, 146], [268, 152], [336, 146]].map(([x, y]) => (
        <Circle key={x} cx={x} cy={y} r={2.6} fill={couleurs.soleil} />
      ))}
    </Svg>
  );
}
