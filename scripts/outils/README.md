# scripts/outils/ : les outils de l'équipe

| Script | Rôle |
|---|---|
| `creer_catalogue_wolof.py` | Crée `content/voix/messages_wolof.csv` : toutes les phrases que le bot dit en wolof. |
| `traduire_par_consensus.py` | Traduction français → wolof par 3 systèmes (Gemini, NLLB-200, Teranga) et juge local (Qwen3-4B). Reprend après une coupure (`--reprendre`) et attend la remise à zéro du quota Gemini. |
| `traduire_catalogue_wolof.py` | Premiers brouillons de traduction par Gemini (D9). |
| `generer_audios_wolof.py` | Notes vocales wolof avec la voix de synthèse d'Octopus, seulement pour les phrases relues ou validées. |
| `controle_voix.py`, `essai_voix_wolof.py` | Contrôle « aller-retour » : voix de synthèse → transcription → comparaison. |
| `telecharger_modeles.py` | Télécharge les modèles wolof locaux dans `modeles/` (hors Git). |
| `generer_bannieres.py` | Génère les bannières des README (`docs/assets/readme/`). |

Modèles locaux utilisés par la concordance (servis par `llama-server`) :

```bash
llama-server -m modeles/teranga/Teranga-Wolof-4B-MT-Q4_K_M.gguf --port 8090 -c 4096 -ngl 99
llama-server -m modeles/juge/Qwen3-4B-Instruct-2507-Q4_K_M.gguf --port 8091 -c 4096 -ngl 99
```
