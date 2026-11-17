"""Exporte le meilleur modèle de diagnostic en ONNX (léger à servir, sans PyTorch).

Usage : .venv/bin/python ml/training/exporter_onnx.py
Entrée : modeles/diagnostic/meilleur.pth et etiquettes.json ; sortie : terramind_diag_v0.onnx.
Vérifie que les sorties ONNX et PyTorch concordent.
"""

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from torch import nn
from torchvision import models

DOSSIER = Path(__file__).resolve().parents[2] / "modeles" / "diagnostic"


def main():
    n = len(json.loads((DOSSIER / "etiquettes.json").read_text()))
    modele = models.mobilenet_v3_large()
    modele.classifier[3] = nn.Linear(modele.classifier[3].in_features, n)
    modele.load_state_dict(torch.load(DOSSIER / "meilleur.pth", map_location="cpu"))
    modele.eval()
    x = torch.randn(1, 3, 224, 224)
    sortie = DOSSIER / "terramind_diag_v0.onnx"
    torch.onnx.export(modele, x, str(sortie), input_names=["image"], output_names=["logits"],
                      opset_version=17, dynamo=False)
    attendu = modele(x).detach().numpy()
    obtenu = ort.InferenceSession(str(sortie)).run(None, {"image": x.numpy()})[0]
    ecart = float(np.abs(attendu - obtenu).max())
    print(f"ok {sortie.name} ({sortie.stat().st_size // 1024} Ko), écart max PyTorch/ONNX {ecart:.2e}")
    assert ecart < 1e-3


if __name__ == "__main__":
    main()
