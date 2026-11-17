# Architecture

TODO : détailler l'architecture « un moteur, deux façades » (schéma dans le [README](../README.md)).

## Déploiement

- Le moteur se déploie automatiquement **depuis `main` uniquement**, après une CI verte, ou depuis une étiquette `v*` ([deploy.yml](../.github/workflows/deploy.yml)). Jamais depuis une branche.
- Chaque déploiement passe par l'environnement GitHub `production`, avec l'approbation d'un autre membre que celui qui a poussé.
- Après déploiement, `/health` doit répondre `status: ok` et aucune réponse ne doit contenir `"mock": true`.
- Retour arrière : redéployer l'étiquette précédente (onglet Actions : relancer l'exécution « Deploy » de cette étiquette).
- Hébergeur : TODO (choix de Salam) ; le workflow reste désactivé (`if: false`) d'ici là.
