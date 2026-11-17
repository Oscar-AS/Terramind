<p align="center"><img src="../../docs/assets/readme/donnees.svg" alt="scripts/donnees/ : la collecte des données" width="100%"></p>

<p align="center">
  <img src="https://img.shields.io/badge/sources-publiques-1f4d3a?style=for-the-badge" alt="Sources publiques">
  <img src="https://img.shields.io/badge/reproductible-oui-3f8f5f?style=for-the-badge" alt="Reproductible">
</p>

Chaque jeu de données du projet est téléchargé par un script, depuis sa source publique, pour que tout soit reproductible (règle du concours : rien d'inventé, provenance documentée).

| Script | Rôle |
|---|---|
| `telecharger_sources.py` | Télécharge les jeux publics (sols, météo, FAOSTAT, documents agricoles…) dans `data/raw/` et tient `data/raw/MANIFESTE.csv`. |
| `telecharger_images.py` | Télécharge les photos de feuilles utiles au diagnostic (PlantVillage, PlantDoc, TOM2024…), sans tout rapatrier. |
| `extraire_rapports.py` | Extrait les tableaux des rapports publics vers `data/extraits/`. |
| `comparer_zones.py` | Compare le climat et le sol des Niayes aux zones dont on utilise les fiches techniques. |
| `tester_modeles_prevention.py` | Fait tourner les règles d'alerte météo sur 2020-2025 aux 4 points pilotes, pour vérifier qu'elles ne sonnent ni tout le temps ni jamais. |
