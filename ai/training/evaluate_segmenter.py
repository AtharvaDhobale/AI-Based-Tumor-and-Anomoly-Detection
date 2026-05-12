from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from ai.models.unet import UNetSmall


def _dice_iou(pred: np.ndarray, gt: np.ndarray) -> tuple[float, float]:
    pred = (pred > 0.5).astype(np.uint8)
    gt = (gt > 0.5).astype(np.uint8)
    inter = float((pred & gt).sum())
    p = float(pred.sum())
    g = float(gt.sum())
    dice = (2.0 * inter) / max(1.0, (p + g))
    union = float((pred | gt).sum())
    iou = inter / max(1.0, union)
    return float(dice), float(iou)


class SegEvalCSVDataset(Dataset):
    def __init__(self, csv_path: str):
        self.samples: list[tuple[str, str]] = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.samples.append((r["image_path"], r["mask_path"]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        ip, mp = self.samples[idx]
        img = cv2.imread(ip, cv2.IMREAD_GRAYSCALE)
        msk = cv2.imread(mp, cv2.IMREAD_GRAYSCALE)
        if img is None or msk is None:
            raise ValueError(f"Missing image/mask for row: {ip} / {mp}")
        img = cv2.resize(img, (256, 256)).astype(np.float32) / 255.0
        msk = cv2.resize(msk, (256, 256)).astype(np.float32) / 255.0
        x = torch.from_numpy(img[None, ...]).float()
        y = torch.from_numpy(msk[None, ...]).float()
        return x, y


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="ai/weights/segmenter.pt")
    ap.add_argument("--test_csv", required=True, help="CSV with columns: image_path,mask_path")
    ap.add_argument("--out", default="ai/weights/segmenter_eval.json")
    ap.add_argument("--batch_size", type=int, default=8)
    args = ap.parse_args()

    ds = SegEvalCSVDataset(args.test_csv)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = UNetSmall(in_channels=1, out_channels=1).to(device)
    model.load_state_dict(torch.load(args.weights, map_location=device))
    model.eval()

    dices: list[float] = []
    ious: list[float] = []

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            pred = torch.sigmoid(model(x)).detach().cpu().numpy()
            gt = y.detach().cpu().numpy()
            for i in range(pred.shape[0]):
                d, j = _dice_iou(pred[i, 0], gt[i, 0])
                dices.append(d)
                ious.append(j)

    out = {
        "mean_dice": float(np.mean(dices)) if dices else 0.0,
        "mean_iou": float(np.mean(ious)) if ious else 0.0,
        "n": int(len(dices)),
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

