# content/voix/enregistrements/ : la prononciation de référence, par un locuteur

Enregistrements de **Salam** (locuteur wolof de l'équipe, 17 nov 2026), qui fixent la bonne prononciation quand la voix de synthèse d'Octopus se trompe.

| Fichier | Ce qui est dit | Ce que ça veut dire | Utilisé comment |
|---|---|---|---|
| `salam_position_recue.m4a` | Dégg naa fi sa tool nekk. | « J'ai compris où se trouve ton champ. » | **Note vocale du bot** (copiée dans `content/audio/wo/position_recue.m4a`, prioritaire sur la synthèse) |
| `salam_reference_saafara.m4a` | Damay bañ a joxe saafara. | « Je refuse de donner un produit (remède). » | Référence de prononciation pour l'accueil |

Les règles tirées de ces écoutes (« tool » dit « taul », « bañ a » dit « bainia », « joxe » dit « diokhé », « Jërëjëf » dit « Jerejef » ; « benn » reste tel quel, déjà bien dit) sont dans [`../prononciation_voix.csv`](../prononciation_voix.csv). Elles ne changent que ce qu'entend la voix d'Octopus : à l'écran, l'orthographe officielle reste.

Enregistrer une phrase soi-même : un fichier `.m4a` nommé `<clé>.m4a` dans `content/audio/wo/` remplace la voix de synthèse pour cette clé (le générateur ne l'écrase jamais).
