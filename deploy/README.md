<p align="center"><img src="../docs/assets/readme/deploy.svg" alt="deploy/ : la mise en ligne" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/image-ghcr.io%2Faliounekane%2Fterramind--moteur-1f4d3a?logo=docker&logoColor=white&style=for-the-badge" alt="Image ghcr.io">
  <img src="https://img.shields.io/badge/hébergement-Render%20(gratuit)-3f8f5f?style=for-the-badge" alt="Render">
  <img src="https://img.shields.io/badge/plateforme-linux%2Famd64-d08a2e?style=for-the-badge" alt="linux/amd64">
</p>

## En une phrase

Le [`Dockerfile`](Dockerfile) emballe le moteur (`engine/`), les fiches (`content/fiches/`), le lexique wolof et le modèle de diagnostic dans une image publiée sur ghcr.io, que Render fait tourner.

## Ce que contient l'image

| Contenu | D'où il vient | Pourquoi |
|---|---|---|
| `engine/` | ce dépôt | le moteur FastAPI (bot Telegram + points d'entrée `/v1`) |
| `content/fiches/` | ce dépôt | les fiches sourcées que le RAG lit (D8) |
| `content/audio/wo/`, `content/voix/lexique_wolof.csv` | ce dépôt | les notes vocales et le lexique wolof |
| `modeles/diagnostic/` | produit par `ml/training/`, **hors Git** | le modèle ONNX, ses étiquettes et sa calibration |

**Aucun secret dans l'image** : les jetons (Telegram, Gemini, Octopus…) sont des variables d'environnement de Render. La liste des variables est dans [`.env.example`](../.env.example).

## Publier une nouvelle version

```bash
# depuis la racine du dépôt
docker buildx build --platform linux/amd64 -f deploy/Dockerfile \
  -t ghcr.io/aliounekane/terramind-moteur:latest \
  -t ghcr.io/aliounekane/terramind-moteur:$(git rev-parse --short HEAD) --push .
curl -X POST "$RENDER_DEPLOY_HOOK"   # lien privé, rangé dans .env, jamais commité
```

Puis vérifier `https://terramind-moteur.onrender.com/sante` : la réponse doit contenir `"mock": false`.

## Limites connues

- L'offre gratuite de Render met le serveur en veille : la première demande après une pause prend environ une minute.
- 512 Mo de mémoire : c'est pourquoi le modèle de diagnostic reste un MobileNetV3 léger (voir [`ml/eval/`](../ml/eval/)).
- Pour l'ouverture au grand public, il faudra un forfait d'hébergement payant.
