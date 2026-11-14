# Contribuer à TerraMind Afrique

## Règles de base
- `main` est **toujours fonctionnelle et déployable**.
- Une branche par tâche, courte (1 à 3 jours), créée depuis `main` :
  `feat/…`, `fix/…`, `content/…`, `ml/…`, `docs/…`
- Messages de commit au format [Conventional Commits](https://www.conventionalcommits.org/) : `feat: …`, `fix: …`, `docs: …`, `chore: …`, etc.

## Pull requests
- Chaque PR est relue par **un** autre membre de l'équipe, **sous 24 h**.
- Fusion en **squash and merge**.
- Le modèle de PR (checklist) doit être rempli.

## Push direct sur `main`
Tant que `main` n'est pas protégée techniquement (voir `scripts/protect_main.sh`), toléré **uniquement** pour leur responsable dans :
- `content/`
- `research/`
- `docs/rapports-hebdo/`

Tout le reste passe par une PR.

## Calendrier
- **17 nov 2026, gel des fonctionnalités** : à partir de cette date, corrections de bugs uniquement, par PR.
- **22 nov 2026** : étiquette `v1.0-final` posée sur `main`.

## Jamais dans le dépôt
- Secrets (`.env`, jetons, clés).
- Photos, numéros de téléphone ou positions GPS de vrais agriculteurs, même dans un dépôt privé.
- Données inventées.
- Modèles entraînés et gros jeux de données (voir `.gitignore`).
