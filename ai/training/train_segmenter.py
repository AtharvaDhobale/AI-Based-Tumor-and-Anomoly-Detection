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
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from ai.models.unet import UNetSmall


class SegFolderDataset(Dataset):
    """Folder dataset:

    data/
      images/*.png
      masks/*.png   (0 background, 255 tumor)
    """

    def __init__(self, root: str, transform: A.Compose):
        rootp = Path(root)
        self.images = sorted((rootp / "images").glob("*.png"))
        self.masks = sorted((rootp / "masks").glob("*.png"))
        if len(self.images) != len(self.masks) or not self.images:
            raise RuntimeError(f"Expected equal non-empty images/ and masks/ under {rootp}")
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx: int):
        import cv2

        img = cv2.imread(str(self.images[idx]), cv2.IMREAD_GRAYSCALE)
        msk = cv2.imread(str(self.masks[idx]), cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (256, 256))
        msk = cv2.resize(msk, (256, 256), interpolation=cv2.INTER_NEAREST)

        aug = self.transform(image=img, mask=msk)
        x = aug["image"]  # 1xHxW
        y = (aug["mask"] > 127).astype(np.float32)[None, ...]
        y = torch.from_numpy(y)
        return x, y


class SegCSVDataset(Dataset):
    def __init__(self, csv_path: str, transform: A.Compose):
        self.transform = transform
        self.samples: list[tuple[str, str]] = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.samples.append((r["image_path"], r["mask_path"]))
        if not self.samples:
            raise RuntimeError(f"No samples in split file: {csv_path}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int):
        import cv2

        image_path, mask_path = self.samples[idx]
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        msk = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if img is None or msk is None:
            raise RuntimeError(f"Bad sample image={image_path} mask={mask_path}")
        img = cv2.resize(img, (256, 256))
        msk = cv2.resize(msk, (256, 256), interpolation=cv2.INTER_NEAREST)
        aug = self.transform(image=img, mask=msk)
        x = aug["image"]
        y = (aug["mask"] > 127).astype(np.float32)[None, ...]
        return x, torch.from_numpy(y)


def dice_loss(logits: torch.Tensor, targets: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    num = 2 * (probs * targets).sum(dim=(2, 3)) + eps
    den = (probs + targets).sum(dim=(2, 3)) + eps
    dice = num / den
    return 1.0 - dice.mean()


def dice_score(logits: torch.Tensor, targets: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    pred = (probs > 0.5).float()
    num = 2 * (pred * targets).sum(dim=(2, 3)) + eps
    den = (pred + targets).sum(dim=(2, 3)) + eps
    return (num / den).mean()


def iou_score(logits: torch.Tensor, targets: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    pred = (probs > 0.5).float()
    inter = (pred * targets).sum(dim=(2, 3))
    union = (pred + targets - pred * targets).sum(dim=(2, 3))
    return ((inter + eps) / (union + eps)).mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="ai/data/segmentation", help="Folder containing images/ masks/")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--out", default="ai/weights/segmenter.pt")
    ap.add_argument("--train_csv", default="", help="Optional split CSV with columns: image_path,mask_path")
    ap.add_argument("--val_csv", default="", help="Optional split CSV with columns: image_path,mask_path")
    ap.add_argument("--metrics_out", default="ai/weights/segmenter_metrics.json")
    args = ap.parse_args()

    tfm = A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.02, scale_limit=0.05, rotate_limit=10, p=0.5),
            A.Normalize(mean=(0.5,), std=(0.5,), max_pixel_value=255.0),
            ToTensorV2(transpose_mask=False),
        ]
    )

    if args.train_csv and args.val_csv:
        train_ds = SegCSVDataset(args.train_csv, transform=tfm)
        val_ds = SegCSVDataset(args.val_csv, transform=tfm)
    else:
        ds = SegFolderDataset(args.data_dir, transform=tfm)
        n = len(ds)
        split = int(0.8 * n)
        idx = np.arange(n)
        np.random.seed(42)
        np.random.shuffle(idx)
        train_ds = torch.utils.data.Subset(ds, idx[:split].tolist())
        val_ds = torch.utils.data.Subset(ds, idx[split:].tolist())
    loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = UNetSmall(in_channels=1, out_channels=1).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    bce = nn.BCEWithLogitsLoss()

    best_dice = -1.0
    best_metrics = {"dice": 0.0, "iou": 0.0}
    for ep in range(1, args.epochs + 1):
        model.train()
        pbar = tqdm(loader, desc=f"seg train ep {ep}")
        for x, y in pbar:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = 0.5 * bce(logits, y) + 0.5 * dice_loss(logits, y)
            loss.backward()
            opt.step()
            pbar.set_postfix(loss=float(loss.item()))
        model.eval()
        dice_vals: list[float] = []
        iou_vals: list[float] = []
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                dice_vals.append(float(dice_score(logits, y).item()))
                iou_vals.append(float(iou_score(logits, y).item()))
        mean_dice = float(np.mean(dice_vals)) if dice_vals else 0.0
        mean_iou = float(np.mean(iou_vals)) if iou_vals else 0.0
        print(f"val dice={mean_dice:.4f} iou={mean_iou:.4f}")
        if mean_dice > best_dice:
            best_dice = mean_dice
            best_metrics = {"dice": mean_dice, "iou": mean_iou}
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.out)
            print(f"saved best -> {args.out}")

    Path(args.metrics_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics_out).write_text(json.dumps(best_metrics, indent=2), encoding="utf-8")
    print(f"saved metrics -> {args.metrics_out}")


if __name__ == "__main__":
    main()

