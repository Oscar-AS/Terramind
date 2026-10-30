# Journal des décisions

Format : une entrée par décision. On ne réécrit pas une décision passée : on en ajoute une nouvelle qui la remplace.

---

### D1. Un moteur, deux façades
- Date : TODO
- Décision : un seul moteur Python/FastAPI porte toute la logique ; le bot WhatsApp et la PWA ne sont que des façades.
- Pourquoi : un seul endroit à tester et à faire évoluer.

### D2. WhatsApp + PWA, la PWA comme plan B
- Date : TODO
- Décision : deux canaux, WhatsApp et appli web installable (PWA). Si l'API WhatsApp n'est pas utilisable à temps, la PWA porte la démo.
- Pourquoi : dépendance à la validation par Meta.

### D3. Système général, culture en paramètre
- Date : TODO
- Décision : la culture est un paramètre dans tous les modules ; aucun nom de culture en dur dans les noms de dossiers ou de fichiers. La liste des cultures prises en charge par le diagnostic est fermée et fixée le 4 nov 2026 (provisoire : tomate, pomme de terre, poivron, maïs).
- Pourquoi : pouvoir étendre sans restructurer ; le diagnostic dépend des données disponibles.

### D4. Réponses par gabarits validés + audio wolof pré-enregistré
- Date : TODO
- Décision : les réponses aux agriculteurs viennent de gabarits FR/wolof validés ; l'audio wolof est pré-enregistré.
- Pourquoi : maîtriser le contenu agronomique et la qualité du wolof.

### D5. Pas de YOLOv8 / Ultralytics tant que la licence AGPL n'est pas tranchée
- Date : TODO
- Décision : modèle de vision basé sur EfficientNet ou MobileNet.
- Pourquoi : la licence AGPL d'Ultralytics peut imposer des contraintes de publication du code.

### D6. Aucune donnée inventée
- Date : TODO
- Décision : toute donnée est réelle, sourcée et inscrite dans [data/README.md](../data/README.md).
- Pourquoi : règle du concours et crédibilité des résultats.

### D7. Nettoyage de CCMT (Raw Data) avant tout entraînement
- Date : 2026-10-30 (validée par Oscar)
- Décision : sur les 25 220 images de CCMT Raw Data (DOI 10.17632/bwh3zbpkpv.1), exclure 1 149 fichiers, listés dans [data/exclusions/ccmt_raw.csv](../data/exclusions/ccmt_raw.csv). Il reste 24 071 images.
  - 94 images illisibles (JPEG corrompus à la source), toutes chez le maïs et la tomate.
  - 604 copies en trop de doublons exacts dans une même classe : on garde une seule copie, la première par ordre alphabétique du chemin.
  - 451 images de 224 groupes de doublons exacts portant des étiquettes différentes : toutes exclues, car au moins une étiquette est fausse et on ne sait pas laquelle (dont 219 groupes chez le maïs : leaf blight, leaf spot, streak virus).
- Pourquoi : des images cassées faussent l'entraînement ; un doublon peut se retrouver à la fois en entraînement et en test et gonfler la précision ; une même image sous deux maladies apprend au modèle à les confondre.
- Conséquences : le découpage entraînement / validation / test se fait APRÈS ces exclusions. Les 451 images en conflit peuvent être réintégrées si un agronome les réétiquette (nouvelle décision à inscrire ici).
- Méthode de détection : ouverture complète de chaque image avec Pillow ; doublons = empreinte SHA-256 identique.
