from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.data.datasets.generate_synthetic_mri import generate_mri_image


def _augment_image(img: np.ndarray) -> np.ndarray:
    img = img.astype(np.uint8)
    if random.random() < 0.7:
        alpha = random.uniform(0.85, 1.15)
        beta = random.randint(-15, 15)
        img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    if random.random() < 0.4:
        noise = np.random.normal(0, random.uniform(1, 6), img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    if random.random() < 0.45:
        blur = random.choice([3, 5])
        img = cv2.GaussianBlur(img, (blur, blur), 0)
    if random.random() < 0.35:
        angle = random.randint(-8, 8)
        M = cv2.getRotationMatrix2D((img.shape[1] // 2, img.shape[0] // 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR)
    if random.random() < 0.3:
        tx = random.randint(-8, 8)
        ty = random.randint(-8, 8)
        M = np.float32([[1, 0, tx], [0, 1, ty]])
        img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR)
    return img


def _save_image(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)


def build_rich_dataset(
    source_dir: str,
    output_dir: str,
    train_per_class: int = 350,
    val_per_class: int = 100,
    test_per_class: int = 100,
    seed: int = 42,
) -> dict[str, int]:
    random.seed(seed)
    np.random.seed(seed)

    source = Path(source_dir)
    out_dir = Path(output_dir)
    for split in ("train", "val", "test"):
        for label in ("benign", "malignant"):
            (out_dir / split / label).mkdir(parents=True, exist_ok=True)

    counts = {"train_benign": 0, "train_malignant": 0, "val_benign": 0, "val_malignant": 0, "test_benign": 0, "test_malignant": 0}

    for label in ("benign", "malignant"):
        label_dir = source / label
        images = sorted(label_dir.glob("*.png"))
        if not images:
            raise FileNotFoundError(f"No images found under {label_dir}")

        # Use real images first to preserve realism.
        for split_name, target_count in [("train", train_per_class), ("val", val_per_class), ("test", test_per_class)]:
            split_dir = out_dir / split_name / label
            split_images = images[: max(1, min(len(images), 20))]
            for i, src in enumerate(split_images):
                if i >= target_count:
                    break
                dst = split_dir / f"{label}_{split_name}_{i:03d}{src.suffix.lower()}"
                shutil.copy2(src, dst)
            counts[f"{split_name}_{label}"] += min(len(split_images), target_count)

        # Fill remaining slots with augmented real images and synthetic MRI-like images.
        for split_name, target_count in [("train", train_per_class), ("val", val_per_class), ("test", test_per_class)]:
            split_dir = out_dir / split_name / label
            existing = sorted(split_dir.glob("*"))
            current = len(existing)
            counter = current
            base_images = [p for p in sorted((source / label).glob("*.png"))]
            while current < target_count:
                base = random.choice(base_images)
                img = cv2.imread(str(base), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                img = cv2.resize(img, (256, 256))
                img = _augment_image(img)
                if random.random() < 0.25:
                    synthetic_img, _ = generate_mri_image(size=256, has_tumor=(label == "malignant"), tumor_severity=random.randint(1, 3))
                    img = cv2.addWeighted(img.astype(np.uint8), 0.6, synthetic_img.astype(np.uint8), 0.4, 0)
                _save_image(split_dir / f"{label}_{split_name}_{counter:03d}.png", img)
                current += 1
                counter += 1
            counts[f"{split_name}_{label}"] = current

    stats = {
        "source_dir": str(source),
        "output_dir": str(out_dir),
        "train": counts["train_benign"] + counts["train_malignant"],
        "val": counts["val_benign"] + counts["val_malignant"],
        "test": counts["test_benign"] + counts["test_malignant"],
        "counts": counts,
    }
    with (out_dir / "dataset_stats.json").open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a richer train/val/test MRI dataset from existing images and synthetic augmentations.")
    ap.add_argument("--source_dir", default="ai/data/mri_dataset")
    ap.add_argument("--out_dir", default="ai/data/augmented_mri")
    ap.add_argument("--train_per_class", type=int, default=400)
    ap.add_argument("--val_per_class", type=int, default=120)
    ap.add_argument("--test_per_class", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    counts = build_rich_dataset(
        source_dir=args.source_dir,
        output_dir=args.out_dir,
        train_per_class=args.train_per_class,
        val_per_class=args.val_per_class,
        test_per_class=args.test_per_class,
        seed=args.seed,
    )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
