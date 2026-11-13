import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 6 : risques météo de la semaine et retour de l'agriculteur.
export default function Alertes() {
  return (
    <Ecran titre="Alertes de la semaine">
      <AVenir
        texte="Notification avec message vocal, puis une carte par alerte : pictogramme du risque, conseil, 🔊."
        api="POST /v1/alert"
      />
      <GrosBouton icone="👀" libelle="J'ai vu" />
      <GrosBouton icone="🙈" libelle="Je n'ai pas vu" variante="clair" />
      <AVenir texte="Les deux boutons envoient le retour de l'agriculteur." api="POST /v1/feedback" />
    </Ecran>
  );
}
