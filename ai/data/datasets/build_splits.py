"""
Build Train/Val/Test Splits for MRI Dataset

Creates subject-level splits to prevent data leakage.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
from tqdm import tqdm


def extract_subject_id(filename: str) -> str:
    """Extract subject ID from filename.
    
    Examples:
        BraTS2021_00000_0001.png -> BraTS2021_00000
        patient_P001.png -> patient_P001
    """
    parts = filename.stem.split("_")
    if len(parts) >= 2:
        # Handle BraTS format: BraTS2021_00000_0001
        if parts[0].startswith("BraTS"):
            return f"{parts[0]}_{parts[1]}"
    return filename.stem.split("_")[0]


def build_segmentation_splits(data_dir: Path, out_dir: Path, seed: int = 42) -> None:
    """Build splits for segmentation dataset.
    
    Structure:
        data_dir/
            images/*.png
            masks/*.png
    """
    images_dir = data_dir / "images"
    masks_dir = data_dir / "masks"
    
    if not images_dir.exists() or not masks_dir.exists():
        raise ValueError(f"Expected images/ and masks/ in {data_dir}")
    
    # Get all image files
    image_files = sorted(images_dir.glob("*.png"))
    
    # Extract subject IDs
    subjects = list(set(extract_subject_id(f) for f in image_files))
    subjects.sort()
    
    print(f"Found {len(subjects)} unique subjects")
    
    # Split subjects (not individual slices)
    train_subjects, test_subjects = train_test_split(
        subjects, test_size=0.15, random_state=seed
    )
    train_subjects, val_subjects = train_test_split(
        train_subjects, test_size=0.15, random_state=seed
    )
    
    print(f"Train: {len(train_subjects)}, Val: {len(val_subjects)}, Test: {len(test_subjects)}")
    
    # Create splits
    splits = {
        "train": set(train_subjects),
        "val": set(val_subjects),
        "test": set(test_subjects)
    }
    
    # Write CSV files
    for split_name, split_subjects in splits.items():
        csv_path = out_dir / f"segmentation_{split_name}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "mask_path"])
            
            for img_file in image_files:
                subject_id = extract_subject_id(img_file)
                if subject_id in split_subjects:
                    mask_file = masks_dir / img_file.name
                    if mask_file.exists():
                        writer.writerow([str(img_file), str(mask_file)])
        
        print(f"  {split_name}: {csv_path}")
    
    # Save split info
    split_info = {
        "num_subjects": len(subjects),
        "train_subjects": len(train_subjects),
        "val_subjects": len(val_subjects),
        "test_subjects": len(test_subjects),
        "seed": seed
    }
    with open(out_dir / "splits_info.json", "w") as f:
        json.dump(split_info, f, indent=2)


def build_classification_splits(data_dir: Path, out_dir: Path, seed: int = 42) -> None:
    """Build splits for classification dataset.
    
    Structure:
        data_dir/
            benign/*.png
            malignant/*.png
    """
    benign_dir = data_dir / "benign"
    malignant_dir = data_dir / "malignant"
    
    # Collect all files with labels
    samples = []
    
    if benign_dir.exists():
        for f in benign_dir.glob("*.png"):
            samples.append((str(f), 0))
    
    if malignant_dir.exists():
        for f in malignant_dir.glob("*.png"):
            samples.append((str(f), 1))
    
    if not samples:
        raise ValueError(f"No samples found in {data_dir}")
    
    print(f"Found {len(samples)} total samples")
    
    # Simple random split (no stratification for small datasets)
    random.shuffle(samples)
    
    n = len(samples)
    n_train = int(0.7 * n)
    n_val = int(0.15 * n)
    
    train_samples = samples[:n_train]
    val_samples = samples[n_train:n_train + n_val]
    test_samples = samples[n_train + n_val:]
    
    print(f"Train: {len(train_samples)}, Val: {len(val_samples)}, Test: {len(test_samples)}")
    
    # Write CSV files
    label_map = {0: "benign", 1: "malignant"}
    
    for split_name, split_samples in [("train", train_samples), ("val", val_samples), ("test", test_samples)]:
        csv_path = out_dir / f"classification_{split_name}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "label"])
            
            for path, label in split_samples:
                writer.writerow([path, label_map[label]])
        
        print(f"  {split_name}: {csv_path}")
    
    # Save split info
    split_info = {
        "num_samples": len(samples),
        "train_samples": len(train_samples),
        "val_samples": len(val_samples),
        "test_samples": len(test_samples),
        "seed": seed
    }
    with open(out_dir / "splits_info.json", "w") as f:
        json.dump(split_info, f, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build train/val/test splits")
    ap.add_argument("--task", required=True, choices=["segmentation", "classification"])
    ap.add_argument("--data_dir", required=True, help="Path to dataset")
    ap.add_argument("--out_dir", default="ai/data/splits", help="Output directory")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    ap.add_argument("--group_by_subject", action="store_true", help="Group by subject")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if args.task == "segmentation":
        build_segmentation_splits(data_dir, out_dir, args.seed)
    else:
        build_classification_splits(data_dir, out_dir, args.seed)
    
    print(f"\nSplits saved to: {out_dir}")


if __name__ == "__main__":
    main()