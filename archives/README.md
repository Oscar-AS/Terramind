<p align="center"><img src="../docs/assets/readme/archives.svg" alt="archives/ : le travail mis de côté" width="100%"></p>

## En une phrase

Ce dossier garde le travail **mis de côté mais pas abandonné** : du code qui a fonctionné, débranché du moteur, avec la marche à suivre pour le reprendre.

```mermaid
flowchart LR
    W["Bot WhatsApp<br/>webhook vérifié par Meta"] -->|"envois bloqués par Meta, D12"| A["archives/whatsapp/"]
    A -->|"compte débloqué<br/>et entreprise vérifiée"| R["Retour dans engine/<br/>marche à suivre du README"]
```

| Dossier | Contenu | Pourquoi archivé | Reprendre |
|---|---|---|---|
| [`whatsapp/`](whatsapp/) | Webhook WhatsApp Cloud API (signature vérifiée, journaux de diagnostic), ses tests, ses variables | Meta a bloqué l'envoi des réponses : erreur 131031, compte restreint, entreprise non vérifiée ([docs/difficultes.md](../docs/difficultes.md)) | [whatsapp/README.md](whatsapp/README.md) |

Rien de ce dossier n'est chargé par le moteur ni inclus dans l'image Docker.
