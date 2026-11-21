// Décor du bas de l'écran : les dunes et les champs des Niayes, dessinés (pas de photo, pas d'image générée).
import Svg, { Circle, Ellipse, Path } from 'react-native-svg';

import { couleurs } from '@/theme';

/** decor : plants et fleurs (retirés derrière les grands boutons, où ils dépasseraient entre deux boutons). */
export function Paysage({ hauteur = 190, decor = true }: { hauteur?: number; decor?: boolean }) {
  return (
    <Svg width="100%" height={hauteur} viewBox="0 0 400 190" preserveAspectRatio="xMidYMax slice">
      {/* dune du fond */}
      <Path d="M0 96 C70 62 130 70 200 88 C270 106 330 66 400 74 L400 190 L0 190 Z" fill="#E3D3B4" />
      {/* colline verte */}
      <Path d="M0 120 C60 96 120 100 190 116 C260 132 330 104 400 108 L400 190 L0 190 Z" fill="#BCD8B2" />
      {/* champ du premier plan */}
      <Path d="M0 146 C80 128 160 134 230 142 C300 150 350 136 400 138 L400 190 L0 190 Z" fill="#9FC795" />
      {decor ? <>
      {/* sillons */}
      <Path d="M90 168 C170 156 260 160 380 158" stroke="#86B67B" strokeWidth={2} fill="none" />
      <Path d="M0 182 C120 168 240 172 400 170" stroke="#86B67B" strokeWidth={2} fill="none" />
      {/* plants */}
      {[86, 118, 150, 182, 214, 246, 278, 310, 342, 374].map((x, i) => (
        <Ellipse key={x} cx={x} cy={i % 2 ? 160 : 164} rx={5} ry={3.5} fill={couleurs.feuille} opacity={0.75} />
      ))}
      {/* quelques fleurs */}
      {[[48, 150], [104, 156], [140, 146], [206, 152], [268, 152], [310, 158], [336, 146], [376, 152]].map(([x, y], i) => (
        <Circle key={x} cx={x} cy={y} r={3} fill={i % 3 === 1 ? couleurs.blanc : couleurs.soleil} />
      ))}
      {[[10, 172], [26, 180], [388, 174]].map(([x, y]) => (
        <Circle key={`b${x}`} cx={x} cy={y} r={3.5} fill={couleurs.soleil} stroke={couleurs.blanc} strokeWidth={1} />
      ))}
      </> : null}
    </Svg>
  );
}
