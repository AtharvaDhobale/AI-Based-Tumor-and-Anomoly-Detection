from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import torch
from albumentations.pytorch import ToTensorV2
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch.utils.data import DataLoader, Dataset

from ai.models.classifier import ResNet18Classifier


class EvalCSVDataset(Dataset):
    def __init__(self, csv_path: str):
        self.samples: list[tuple[str, int]] = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                y = 1 if str(r["label"]).strip().lower() == "malignant" else 0
                self.samples.append((r["image_path"], y))
        self.transform = A.Compose(
            [
                A.Normalize(mean=(0.5,), std=(0.5,), max_pixel_value=255.0),
                ToTensorV2(transpose_mask=False),
            ]
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, y = self.samples[idx]
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (256, 256))
        x = self.transform(image=img)["image"]
        return x, y


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="ai/weights/classifier.pt")
    ap.add_argument("--test_csv", required=True)
    ap.add_argument("--out", default="ai/weights/classifier_eval.json")
    ap.add_argument("--batch_size", type=int, default=16)
    args = ap.parse_args()

    ds = EvalCSVDataset(args.test_csv)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = ResNet18Classifier(num_classes=2, pretrained=False).to(device)
    model.load_state_dict(torch.load(args.weights, map_location=device))
    model.eval()

    y_true: list[int] = []
    y_prob: list[float] = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            probs = torch.softmax(model(x), dim=1)[:, 1].detach().cpu().numpy()
            y_true.extend(list(y))
            y_prob.extend(probs.tolist())
    y_pred = [1 if p >= 0.5 else 0 for p in y_prob]
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": float(tn / max(1, tn + fp)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(set(y_true)) > 1 else 0.0,
        "false_negatives": int(fn),
        "false_positives": int(fp),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

