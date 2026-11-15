# content/voix/ : ce que le bot dit en wolof

Les phrases que le bot Telegram dit **à voix haute en wolof**, pour les agriculteurs qui ne lisent pas.

## Les fichiers

| Fichier | Contenu |
|---|---|
| [`messages_wolof.csv`](messages_wolof.csv) | Le catalogue : une ligne par phrase (`cle`, `usage`, `voix`, `texte_fr`, `texte_wo`, `statut`, `relu_par`). Créé par `scripts/outils/creer_catalogue_wolof.py`. |
| [`lexique_wolof.csv`](lexique_wolof.csv) | Les mots imposés aux traductions (glossaire : cultures, maladies, boutons). |
| [`controle_voix.csv`](controle_voix.csv) | Le contrôle « aller-retour » : synthèse vocale, puis transcription, comparées au texte de départ. |
| `traductions_concordance.csv` | Le détail de la traduction par concordance (les 3 versions, leurs retraductions et l'avis du juge). |

## Le chemin d'une phrase

```mermaid
flowchart LR
    FR["Phrase française<br/>du bot"] --> C["Concordance<br/>Gemini · NLLB-200 · Teranga"]
    C --> J{"Juge de sens<br/>Qwen3-4B, local"}
    J -->|"les 3 d'accord"| V["valide_concordance"]
    J -->|"désaccord"| R["a_relire"]
    V & R --> L["Relecture<br/>par un locuteur"]
    L --> A["Audio<br/>voix wolof d'Octopus"]
```

**Statuts** : `a_traduire`, `brouillon_gemini`, `a_relire`, `valide_concordance`, `relu` (relu par un locuteur : plus jamais modifié automatiquement).

**Limite constatée le 15 nov 2026** : les retraductions automatiques du wolof vers le français sont trop peu fiables pour valider seules. La concordance sert surtout à proposer 3 versions par phrase au locuteur qui relit. Aucun audio n'est généré pour une phrase qui n'a pas été relue ou validée.
