import { AVenir } from '@/components/AVenir';
import { Ecran } from '@/components/Ecran';
import { GrosBouton } from '@/components/GrosBouton';

// Étape 7 : question vocale, même geste qu'une note vocale WhatsApp.
export default function Question() {
  return (
    <Ecran titre="Poser une question">
      <AVenir
        texte="Garder le micro appuyé pour parler, lâcher pour envoyer, glisser à gauche pour annuler, vers le haut pour verrouiller. Option : un toucher pour démarrer, un pour arrêter. Réponse en audio, texte français en dessous."
        api="POST /v1/chat"
      />
      <GrosBouton icone="🎤" libelle="Parler" />
    </Ecran>
  );
}
