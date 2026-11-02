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
