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

### D7. Le travail ne dépend ni d'un agronome, ni des mentors, ni des entretiens
- Date : 2 nov 2026
- Décision : tout le contenu agronomique et toutes les données reposent sur des sources publiées et ouvertes (ISRA, FAO, ANSD, DAPSA, NASA, articles scientifiques), inscrites dans [data/README.md](../data/README.md) et le [journal des sources](sources/journal-recherche-agronomique.md). L'avis d'un agronome, l'aide des mentors, les microdonnées demandées à l'ANADS et les entretiens avec les agriculteurs sont des **bonus** : ils améliorent le contenu s'ils arrivent, mais aucune tâche n'attend après eux. Ce qui n'est pas sourcé reste marqué « à vérifier » ou « à sourcer » et n'entre pas dans le produit.
- Pourquoi : aucun agronome disponible au 2 nov 2026, réponses des institutions incertaines dans les délais du concours. Les données sont rassemblées avant de commencer à construire (voir [data/CATALOGUE.md](../data/CATALOGUE.md)).

### D8. Réponses par RAG sur les fiches, réponses types pour le wolof (remplace D4)
- Date : 2 nov 2026
- Décision : le bot rédige ses réponses avec un modèle de langage en **RAG** : il cherche d'abord les passages utiles dans les fiches validées (`content/fiches/`) et ne répond qu'à partir de ce qu'il y trouve ; s'il ne trouve rien, il répond « je ne sais pas » et oriente vers un agent agricole. Le RAG est **obligatoire dès la v1**. Les **réponses types** (messages écrits à l'avance et envoyés mot pour mot, `content/templates/`, ex-« gabarits ») servent aux cas sensibles (diagnostic incertain, absence de source) et aux réponses en wolof. Wolof : compréhension par des modèles de reconnaissance vocale déjà entraînés au wolof (Kiriku-Wolof-ASR, whosper-large-v2, dofbi/wolof-asr, ressources GalsenAI), à tester puis à affiner sur le vocabulaire agricole (corpus Kallaama, dictionnaire local) ; recherche et rédaction en français ; réponse en wolof par réponses types relues par des locuteurs, lues par synthèse vocale wolof (galsenai/xTTS-v2-wolof) ou enregistrées ; traduction automatique seulement en secours et relue.
- Pourquoi : c'est l'architecture du dossier de conception (sections 08, 11 et 13). D4 l'avait réduite par erreur aux seuls gabarits, ce qui retirait l'intérêt principal de l'outil : répondre aux vraies questions des agriculteurs à partir de sources vérifiées. Les modèles de langage écrivent encore mal le wolof (traduction automatique BLEU 9,17, étude AfroBench) : pas de wolof généré librement pour des conseils agricoles.

### D9. Réponses en wolof rédigées par un modèle qui écrit le wolof, après test (remplace la partie « réponse en wolof » de D8)
- Date : 2 nov 2026
- Décision : en wolof, la réponse est **rédigée par un modèle de langage capable d'écrire le wolof**, à partir de ce que le RAG a trouvé dans les fiches, et non par un outil de traduction automatique classique. Candidats à comparer : Gemini (Google), GPT, Claude, avec Google Traduction (wolof disponible depuis juin 2024) comme point de comparaison. Le choix se fait sur un **test** : une trentaine de questions réelles, réponses notées par au moins deux locuteurs du wolof (compréhensible, correct, fidèle à la fiche). Les **réponses types en wolof**, relues par des locuteurs, restent le filet de sécurité : cas sensibles (diagnostic incertain, alertes, absence de source) et repli si aucun modèle ne passe le test. GalsenAI et les modèles de reconnaissance vocale servent à comprendre la voix (ASR) et à parler (TTS), comme prévu dans D8.
- Pourquoi : l'objectif du projet est un vrai dialogue en wolof, pas seulement des messages préécrits. Les modèles récents écrivent un wolof imparfait mais utilisable (banc communautaire AI4Wolof, traduction : Gemini 2.0 Flash 0,685, Claude 3.5 Sonnet 0,663, GPT-4o 0,658 ; AfroBench classe toutefois le wolof parmi les langues les plus faibles). D'où le test avec des locuteurs avant toute mise en service, et le filet de sécurité.

### D10. En wolof, la voix d'abord
- Date : 2 nov 2026
- Décision : la plupart des agriculteurs qui parlent wolof ne le lisent pas, et ceux qui le lisent lisent aussi le français. Une question en wolof reçoit donc d'abord une **réponse vocale en wolof** (note vocale WhatsApp) ; le texte écrit accompagne la réponse en français. Entrée : la note vocale est transcrite par reconnaissance vocale (voir D8). Sortie : le texte wolof rédigé par le modèle choisi (D9) est lu par la synthèse vocale wolof (galsenai/xTTS-v2-wolof) ; les réponses types sensibles sont de préférence **enregistrées par une voix humaine**. Le test de D9 se fait **à l'écoute** : les locuteurs notent l'audio (compris, correct, naturel), pas le texte. Les textes destinés à être lus à voix haute sont écrits pour l'oreille : phrases courtes, nombres et dates en toutes lettres, pas d'abréviations ni de symboles.
- Pourquoi : un message écrit en wolof n'est utile qu'à une minorité qui lit déjà le français. Point de vigilance repris du dossier : la synthèse vocale wolof a des pauses aléatoires et lit mal les chiffres et les mots français, et le modèle est lourd (plus de 7 Go) : mesurer la qualité et le temps de réponse dès les premiers tests.
- Preuve chiffrée (ajoutée le 4 nov 2026) : selon le recensement de l'horticulture dans les Niayes (Direction de l'Horticulture, données 2012, tableau 10), **71,3 % des exploitants horticoles n'ont aucun niveau d'instruction** (86,3 % des femmes), et ce taux dépasse 95 % à Notto Gouye Diama, Taiba Ndiaye et Thieppe. Fichier : `data/extraits/dhort_2012_niayes_instruction_exploitants.csv`.

### D11. Module Prévention : ravageurs et alternariose en plus du mildiou
- Date : 2 nov 2026 (proposé par Claude, approuvé par Salam)
- Décision : le module Prévention ne se limite plus au mildiou. Il couvre aussi **la mineuse de la tomate** (*Tuta absoluta*) et **la teigne du chou** (*Plutella xylostella*), par des modèles en degrés-jours (date probable de la prochaine génération : « surveillez »), et **l'alternariose** de la tomate et de la pomme de terre (modèle TOMCAST). Le mildiou garde les critères Hutton. Règles, seuils et sources : [sources/seuils-meteo-maladies-ravageurs.md](sources/seuils-meteo-maladies-ravageurs.md).
- Pourquoi : selon l'Enquête agricole annuelle 2022-2023 (DAPSA), 43,9 % des ménages agricoles de Louga et 20,6 % de ceux de Thiès ont subi des ravageurs inhabituels (15,3 % au national), et les insecticides sont utilisés sur 99 % des parcelles de chou, 97 % de la tomate cerise et 78 % de l'oignon. Le rapport STDF/AUMN situe le pic de la teigne du chou en février dans les Niayes. Le besoin principal porte donc sur les ravageurs plus que sur le mildiou.
- Limites : aucun de ces modèles n'est validé au Sénégal. Le bot parle de « conditions favorables » et conseille de surveiller, sans produit ni dose. Le seul test fait (mildiou, février 2026 à Tivaouane) est cohérent mais ne constitue pas une validation.

### D12. Démonstration par Telegram et l'application mobile ; WhatsApp en extension (modifie D2)
- Date : 13 nov 2026 (décision de Salam)
- Décision : les façades présentées au jury sont un **bot Telegram** et l'**application mobile** (Expo : APK Android et version web). Elles appellent le même moteur (`/v1/...`). Le bot WhatsApp devient une extension, réactivée quand Meta lèvera la restriction du compte.
- Pourquoi : envois WhatsApp bloqués par Meta (erreur 131031, compte restreint, vérification d'entreprise requise), sans délai garanti avant la livraison du 22 nov. Telegram ne demande ni vérification d'entreprise ni moyen de paiement. Détails : [difficultes.md](difficultes.md).
- Limite : Telegram est moins utilisé que WhatsApp par les maraîchers des Niayes. C'est un choix pour la démonstration, pas pour le déploiement.

### D13. Chaque problème expliqué en 4 temps, comme pour un malade
- Date : 13 nov 2026 (demande de Salam)
- Décision : après un diagnostic photo, l'agriculteur ne reçoit pas seulement un nom de maladie, mais la fiche en **4 temps**, dans l'ordre où un malade se pose les questions : **ce que c'est**, **pourquoi c'est arrivé**, **que faire maintenant**, **pour que ça ne revienne pas**. Les fiches de `content/fiches/` suivent ces sections (plus « Comment la reconnaître » et, si une source existe, « Au Sénégal »). Chaque étiquette du modèle photo a sa fiche ; quand une source manque (prévention, présence au Sénégal), la fiche le dit au lieu d'inventer. L'app les montre en 4 cartes numérotées, le bot Telegram en 4 blocs.
- Pourquoi : un nom seul (« Fusariose ») n'apprend rien à un agriculteur. Il doit comprendre ce qu'a sa plante, la cause, ce qu'il peut faire tout de suite et comment l'éviter la prochaine fois.
- Garde-fous : aucune fiche ne nomme de produit ni de dose (test automatique) ; 3 passes de vérification indépendante phrase par phrase contre les sources (environ 320 affirmations, 51 corrigées) ; relecture par Rama à faire.
- Point ouvert : la fiche « tache bactérienne » cite la désinfection des graines à l'eau chaude (56 °C pendant 30 minutes, FAO). Ce n'est pas un produit, mais c'est une consigne chiffrée : à garder ou à remplacer par un renvoi vers un agent agricole (décision d'équipe).

### D14. Nettoyage de CCMT (Raw Data) avant tout entraînement
- Date : 30 oct 2026 (validée par Oscar)
- Décision : sur les 25 220 images de CCMT Raw Data (DOI 10.17632/bwh3zbpkpv.1), exclure 1 149 fichiers, listés dans [data/exclusions/terramind_v1.csv](../data/exclusions/terramind_v1.csv) (lignes source = ccmt). Il reste 24 071 images.
  - 94 images illisibles (JPEG corrompus à la source), toutes chez le maïs et la tomate.
  - 604 copies en trop de doublons exacts dans une même classe : on garde une seule copie, la première par ordre alphabétique du chemin.
  - 451 images de 224 groupes de doublons exacts portant des étiquettes différentes : toutes exclues, car au moins une étiquette est fausse et on ne sait pas laquelle (dont 219 groupes chez le maïs : leaf blight, leaf spot, streak virus).
- Pourquoi : des images cassées faussent l'entraînement ; un doublon peut se retrouver à la fois en entraînement et en test et gonfler la précision ; une même image sous deux maladies apprend au modèle à les confondre.
- Conséquences : le découpage entraînement / validation / test se fait APRÈS ces exclusions. Les 451 images en conflit peuvent être réintégrées si un agronome les réétiquette (nouvelle décision à inscrire ici).
- Méthode de détection : ouverture complète de chaque image avec Pillow ; doublons = empreinte SHA-256 identique.
- Intégration : écrite par Oscar sur la branche `ml/dataset-merge` sous le numéro D12 ; renumérotée D14 le 14 nov 2026 (D12 et D13 étaient déjà prises sur la branche principale de travail).

### D15. Base fusionnée terramind_v1 (TOM2024 + CCMT)
- Date : 30 oct 2026 (validée par Oscar)
- Décision : fusionner TOM2024 (raw) et CCMT (Raw Data) en une seule base de 35 448 images, 5 cultures et 40 classes, construite par [ml/training/build_merged_dataset.py](../ml/training/build_merged_dataset.py).
  - Étiquettes uniformisées par [data/label_mapping.csv](../data/label_mapping.csv) : noms en anglais snake_case, coquilles corrigées. Fusions limitées aux cas sûrs : healthy (maïs, tomate) et chenille légionnaire (TOM2024 -a = dégâts, -p = chenille, CCMT all armyworm) en all_armyworm. Les cas douteux restent séparés et marqués « à valider ».
  - Mêmes règles de nettoyage pour les deux jeux (étend D14 à TOM2024) : illisibles (94), petit côté < 64 px (142, tous dans TOM2024), doublons exacts dans une même classe (936 copies), doublons à étiquettes différentes (515 images).
  - Classes de moins de 50 images retirées (167 images, 7 classes, toutes de TOM2024) : coup de soleil (49), excès d'azote (42), pourriture du bulbe (29), fusariose de la tomate (18), Tuta absoluta (17), alternariose et acariens (8), pucerons (4). Seuil abaissé de 100 à 50 pour garder le mildiou de la tomate (72), la rouille du maïs (94) et le trouble abiotique du maïs (76).
  - Images copiées sans réencodage ; liste complète des 1 854 exclusions : [data/exclusions/terramind_v1.csv](../data/exclusions/terramind_v1.csv).
- Pourquoi : une seule base cohérente pour le diagnostic, reproductible à l'identique.
- Conséquences : le diagnostic ne reconnaîtra pas Tuta absoluta tant qu'on n'aura pas au moins 50 images (photos de terrain ou autre jeu sourcé). Le mildiou (72 images) et la rouille du maïs (94) restent les classes les plus petites : leurs résultats seront à surveiller. Les fusions « à valider » sont à revoir avec l'agronome. Le découpage entraînement / validation / test reste à faire sur cette base.
- Intégration : écrite par Oscar sur la branche `ml/dataset-merge` sous le numéro D13 ; renumérotée D15 le 14 nov 2026 (D12 et D13 étaient déjà prises sur la branche principale de travail).
- Statut au 14 nov 2026 : le modèle déployé (MobileNetV3 v1, [ml/eval/diagnostic_v1.md](../ml/eval/diagnostic_v1.md)) n'a **pas** été entraîné sur cette base (PlantVillage, PlantDoc et TOM2024). terramind_v1 sert de point de départ pour ajouter CCMT (tomate du Ghana) et renforcer le mildiou de la tomate.
