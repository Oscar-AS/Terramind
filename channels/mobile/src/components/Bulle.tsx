// Texte d'un message du bot : <b>gras</b> et <i>italique</i>, comme le HTML de Telegram.
import { type ReactNode } from 'react';
import { type StyleProp, Text, type TextStyle } from 'react-native';

import { polices } from '@/theme';

export function TexteRiche({ texte, style }: { texte: string; style?: StyleProp<TextStyle> }) {
  const morceaux: ReactNode[] = [];
  let gras = false;
  let italique = false;
  texte.split(/(<\/?[bi]>)/).forEach((m, i) => {
    if (m === '<b>' || m === '</b>') gras = m === '<b>';
    else if (m === '<i>' || m === '</i>') italique = m === '<i>';
    else if (m) {
      morceaux.push(
        <Text key={i} style={[gras && { fontFamily: polices.texteGras }, italique && { fontStyle: 'italic' }]}>{m}</Text>,
      );
    }
  });
  return <Text style={style}>{morceaux}</Text>;
}
