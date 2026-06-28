from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np


def _run(cmd: list[str]) -> None:
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    ap = argparse.ArgumentParser(description="End-to-end BraTS pipeline: generate, prepare slices, splits, train & evaluate classifier and segmenter.")
    ap.add_argument("--brats_root", default="ai/data/brats/training", help="BraTS cases directory.")
    ap.add_argument("--modality", default="flair", choices=["flair", "t1", "t1ce", "t2"])
    ap.add_argument("--out_seg_dir", default="ai/data/segmentation")
    ap.add_argument("--out_clf_dir", default="ai/data/classification")
    ap.add_argument("--splits_dir", default="ai/data/splits")
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seg_epochs", type=int, default=5)
    ap.add_argument("--clf_epochs", type=int, default=5)
    ap.add_argument("--generate_mock", action="store_true", default=True, help="Whether to generate synthetic NIfTI data first.")
    args = ap.parse_args()

    py = sys.executable

    # 1) Generate mock BraTS dataset if requested
    if args.generate_mock or not Path(args.brats_root).exists():
        print("--- 1. Generating Mock BraTS NIfTI Dataset ---")
        _run(
            [
                py,
                "-m",
                "ai.datasets.generate_mock_brats",
                "--num_cases",
                "6",
                "--out_dir",
                args.brats_root,
            ]
        )

    # 2) Prepare segmentation dataset (2D slices)
    # We run prepare_brats_segmentation with min_mask_mean=0 to export all slices, both positive and negative,
    # which allows us to build classification dataset as well!
    print("--- 2. Extracting slices from NIfTI volumes ---")
    _run(
        [
            py,
            "-m",
            "ai.datasets.prepare_brats_segmentation",
            "--brats_root",
            args.brats_root,
            "--modality",
            args.modality,
            "--out_dir",
            args.out_seg_dir,
            "--stride",
            str(args.stride),
            "--min_mask_mean",
            "0.0",  # Keep all slices including backgrounds
        ]
    )

    # 3) Build classification folders from segmentation slices
    print("--- 3. Preparing classification folders (benign/malignant) ---")
    out_clf_path = Path(args.out_clf_dir)
    benign_dir = out_clf_path / "benign"
    malignant_dir = out_clf_path / "malignant"
    
    # Clean previous classification folders
    if benign_dir.exists():
        shutil.rmtree(benign_dir)
    if malignant_dir.exists():
        shutil.rmtree(malignant_dir)
        
    benign_dir.mkdir(parents=True, exist_ok=True)
    malignant_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = Path(args.out_seg_dir) / "images"
    masks_dir = Path(args.out_seg_dir) / "masks"
    
    benign_count = 0
    malignant_count = 0
    
    for img_path in sorted(images_dir.glob("*.png")):
        mask_path = masks_dir / img_path.name
        if mask_path.exists():
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            # If the mask has tumor pixels (>127), label as malignant, otherwise benign
            if mask is not None and mask.max() > 127:
                shutil.copy2(img_path, malignant_dir / img_path.name)
                malignant_count += 1
            else:
                shutil.copy2(img_path, benign_dir / img_path.name)
                benign_count += 1
                
    print(f"Prepared classification folders: {benign_count} benign, {malignant_count} malignant slices.")

    # 4) Build Splits (Segmentation & Classification)
    print("--- 4. Creating splits for Segmentation and Classification ---")
    _run(
        [
            py,
            "-m",
            "ai.datasets.build_splits",
            "--task",
            "segmentation",
            "--data_dir",
            args.out_seg_dir,
            "--out_dir",
            args.splits_dir,
            "--seed",
            str(args.seed),
            "--train",
            "0.6",
            "--val",
            "0.2",
            "--group_by_subject",
        ]
    )
    
    _run(
        [
            py,
            "-m",
            "ai.datasets.build_splits",
            "--task",
            "classification",
            "--data_dir",
            args.out_clf_dir,
            "--out_dir",
            args.splits_dir,
            "--seed",
            str(args.seed),
            "--train",
            "0.6",
            "--val",
            "0.2",
            "--group_by_subject",
        ]
    )

    # 5) Train segmenter
    print("--- 5. Training Segmenter model ---")
    _run(
        [
            py,
            "-m",
            "ai.training.train_segmenter",
            "--train_csv",
            str(Path(args.splits_dir) / "segmentation_train.csv"),
            "--val_csv",
            str(Path(args.splits_dir) / "segmentation_val.csv"),
            "--epochs",
            str(args.seg_epochs),
            "--out",
            "ai/weights/segmenter.pt",
        ]
    )

    # 6) Train classifier
    print("--- 6. Training Classifier model ---")
    _run(
        [
            py,
            "-m",
            "ai.training.train_classifier",
            "--train_csv",
            str(Path(args.splits_dir) / "classification_train.csv"),
            "--val_csv",
            str(Path(args.splits_dir) / "classification_val.csv"),
            "--epochs",
            str(args.clf_epochs),
            "--out",
            "ai/weights/classifier.pt",
        ]
    )

    # 7) Evaluate segmenter
    print("--- 7. Evaluating Segmenter model ---")
    _run(
        [
            py,
            "-m",
            "ai.training.evaluate_segmenter",
            "--weights",
            "ai/weights/segmenter.pt",
            "--test_csv",
            str(Path(args.splits_dir) / "segmentation_test.csv"),
            "--out",
            "ai/weights/segmenter_eval.json",
        ]
    )

    # 8) Evaluate classifier
    print("--- 8. Evaluating Classifier model ---")
    _run(
        [
            py,
            "-m",
            "ai.training.evaluate_classifier",
            "--weights",
            "ai/weights/classifier.pt",
            "--test_csv",
            str(Path(args.splits_dir) / "classification_test.csv"),
            "--out",
            "ai/weights/classifier_eval.json",
        ]
    )

    print("\n==============================================")
    print("BraTS Training Pipeline Completed Successfully!")
    print("Weights saved:")
    print("  Segmenter:  ai/weights/segmenter.pt")
    print("  Classifier: ai/weights/classifier.pt")
    print("==============================================")


if __name__ == "__main__":
    main()
