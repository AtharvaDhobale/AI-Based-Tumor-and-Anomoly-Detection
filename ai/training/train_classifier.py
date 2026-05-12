from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import albumentations as A
import numpy as np
import torch
import torch.nn as nn
from albumentations.pytorch import ToTensorV2
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from ai.models.classifier import ResNet18Classifier


class FolderDataset(Dataset):
    """Simple folder dataset:

    data/
      benign/*.png
      malignant/*.png
    """

    def __init__(self, root: str, transform: A.Compose):
        self.root = Path(root)
        self.transform = transform
        self.samples: list[tuple[str, int]] = []
        for label_name, y in [("benign", 0), ("malignant", 1)]:
            for p in (self.root / label_name).glob("*.png"):
                self.samples.append((str(p), y))
        if not self.samples:
            raise RuntimeError(f"No samples found under {self.root}. Expected benign/ and malignant/ with PNG images.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, y = self.samples[idx]
        import cv2

        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (256, 256))
        img = img.astype(np.float32) / 255.0
        img = (img * 255.0).astype(np.uint8)

        aug = self.transform(image=img)
        x = aug["image"]  # 1xHxW
        return x, torch.tensor(y).long()


class CSVDataset(Dataset):
    def __init__(self, csv_path: str, transform: A.Compose):
        self.transform = transform
        self.samples: list[tuple[str, int]] = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                label = 1 if str(r["label"]).strip().lower() == "malignant" else 0
                self.samples.append((r["image_path"], label))
        if not self.samples:
            raise RuntimeError(f"No samples in split file: {csv_path}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, y = self.samples[idx]
        import cv2

        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise RuntimeError(f"Could not read image: {path}")
        img = cv2.resize(img, (256, 256))
        img = img.astype(np.float32) / 255.0
        img = (img * 255.0).astype(np.uint8)
        aug = self.transform(image=img)
        return aug["image"], torch.tensor(y).long()


def _eval_metrics(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> dict[str, float]:
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    y_prob: list[float] = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)[:, 1].detach().cpu().numpy()
            pred = (probs >= 0.5).astype(np.int64)
            y_true.extend(y.numpy().tolist())
            y_pred.extend(pred.tolist())
            y_prob.extend(probs.tolist())
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if len(set(y_true)) > 1:
        out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    else:
        out["roc_auc"] = 0.0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="ai/data/classification", help="Folder containing benign/ malignant/")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--out", default="ai/weights/classifier.pt")
    ap.add_argument("--train_csv", default="", help="Optional split CSV with columns: image_path,label")
    ap.add_argument("--val_csv", default="", help="Optional split CSV with columns: image_path,label")
    ap.add_argument("--metrics_out", default="ai/weights/classifier_metrics.json")
    args = ap.parse_args()

    tfm = A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.ShiftScaleRotate(shift_limit=0.02, scale_limit=0.05, rotate_limit=10, p=0.5),
            A.Normalize(mean=(0.5,), std=(0.5,), max_pixel_value=255.0),
            ToTensorV2(transpose_mask=False),
        ]
    )

    if args.train_csv and args.val_csv:
        train_ds = CSVDataset(args.train_csv, transform=tfm)
        val_ds = CSVDataset(args.val_csv, transform=tfm)
    else:
        ds = FolderDataset(args.data_dir, transform=tfm)
        idx = np.arange(len(ds))
        train_idx, val_idx = train_test_split(idx, test_size=0.2, random_state=42, stratify=[ds.samples[i][1] for i in idx])
        train_ds = torch.utils.data.Subset(ds, train_idx.tolist())
        val_ds = torch.utils.data.Subset(ds, val_idx.tolist())

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ResNet18Classifier(num_classes=2, pretrained=True).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    best_val = 0.0
    best_metrics: dict[str, float] = {}
    for ep in range(1, args.epochs + 1):
        model.train()
        pbar = tqdm(train_loader, desc=f"train ep {ep}")
        for x, y in pbar:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = loss_fn(logits, y)
            loss.backward()
            opt.step()
            pbar.set_postfix(loss=float(loss.item()))

        # val
        metrics = _eval_metrics(model, val_loader, device)
        acc = metrics["accuracy"]
        print(
            "val metrics: "
            f"acc={metrics['accuracy']:.4f} "
            f"f1={metrics['f1']:.4f} "
            f"recall={metrics['recall']:.4f} "
            f"precision={metrics['precision']:.4f} "
            f"auc={metrics['roc_auc']:.4f}"
        )
        if acc > best_val:
            best_val = acc
            best_metrics = metrics
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.out)
            print(f"saved best -> {args.out}")
    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics_out).write_text(json.dumps(best_metrics, indent=2), encoding="utf-8")
    print(f"saved metrics -> {args.metrics_out}")


if __name__ == "__main__":
    main()

