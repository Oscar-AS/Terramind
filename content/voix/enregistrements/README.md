# content/voix/enregistrements/ : la prononciation de référence, par un locuteur

Enregistrements de **Salam** (locuteur wolof de l'équipe, 17 nov 2026), qui fixent la bonne prononciation quand la voix de synthèse d'Octopus se trompe.

| Fichier | Ce qui est dit | Ce que ça veut dire | Utilisé comment |
|---|---|---|---|
| `salam_position_recue.m4a` | Dégg naa fi sa tool nekk. | « J'ai compris où se trouve ton champ. » | **Note vocale du bot** (copiée dans `content/audio/wo/position_recue.m4a`, prioritaire sur la synthèse) |
| `salam_reference_saafara.m4a` | Damay bañ a joxe saafara. | « Je refuse de donner un produit (remède). » | Référence de prononciation pour l'accueil |
| `salam_reference_jerejef.m4a` | Jërëjëf. | « Merci. » | Référence de prononciation |

## Comment la voix est calée sur ces enregistrements

Plutôt que de deviner à l'oreille, on compare **ce que la reconnaissance vocale wolof d'Octopus entend** :
1. elle transcrit l'enregistrement de Salam (la référence) ;
2. pour chaque façon d'écrire un mot, la voix de synthèse le dit, puis la même reconnaissance le transcrit ;
3. on garde la graphie dont la transcription ressemble le plus à la référence (score de 0 à 1).

| Mot (écran) | Dit par la voix | Score |
|---|---|---|
| Jërëjëf | Jërë-jëf | 1,00 |
| tool | tôl | 0,91 |
| bañ a joxe | baña djokhé | 0,89 |
| saafara | saaffara | 0,90 (moyenne de 2 tirages) |

Détail de tous les essais : [`calage_prononciation.txt`](calage_prononciation.txt). La table utilisée est [`../prononciation_voix.csv`](../prononciation_voix.csv) ; elle ne change que ce qu'entend la voix d'Octopus, l'écran garde l'orthographe officielle. « benn » reste tel quel (déjà bien dit).

Enregistrer une phrase soi-même : un fichier `.m4a` nommé `<clé>.m4a` dans `content/audio/wo/` remplace la voix de synthèse pour cette clé (le générateur ne l'écrase jamais).
