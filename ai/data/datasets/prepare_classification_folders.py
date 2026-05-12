"""
BraTS Classification Dataset Preparation

Converts BraTS data to binary classification (benign vs malignant) format.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import nibabel as nib
import numpy as np
from tqdm import tqdm


def get_tumor_label(seg_path: Path) -> int:
    """Determine if a subject has tumor (malignant) or not.
    
    BraTS segmentation labels:
    - 0: Background
    - 1: Necrotic and non-enhancing tumor core (NET)
    - 2: Peritumoral edema
    - 4: GD-enhancing tumor (ET)
    
    For binary classification:
    - Any tumor tissue (1, 2, 4) = malignant (1)
    - No tumor = benign (0)
    """
    if not seg_path.exists():
        return 0  # No segmentation = benign
    
    seg = nib.load(str(seg_path))
    mask = seg.get_fdata()
    
    # Check if any tumor labels present
    if mask.max() > 0:
        return 1  # malignant
    return 0  # benign


def load_brats_subject(subject_dir: Path, modality: str = "flair") -> np.ndarray:
    """Load a BraTS subject's imaging data.
    
    Args:
        subject_dir: Path to subject folder
        modality: MRI modality to load
    
    Returns:
        Image as numpy array
    """
    # Find NIfTI file
    for f in subject_dir.glob("*.nii.gz"):
        if f"_flair" in f.name and modality == "flair":
            img = nib.load(str(f))
            return img.get_fdata()
        elif f"_t1" in f.name and modality == "t1" and "ce" not in f.name.lower():
            img = nib.load(str(f))
            return img.get_fdata()
        elif f"_t1ce" in f.name and modality == "t1ce":
            img = nib.load(str(f))
            return img.get_fdata()
        elif f"_t2" in f.name and modality == "t2":
            img = nib.load(str(f))
            return img.get_fdata()
    
    raise FileNotFoundError(f"No {modality} file found in {subject_dir}")


def extract_central_slice(image: np.ndarray) -> np.ndarray:
    """Extract the central slice from 3D volume."""
    z = image.shape[2] // 2
    return image[:, :, z]


def normalize(volume: np.ndarray) -> np.ndarray:
    """Normalize MRI volume to [0, 255] range."""
    vmin, vmax = volume.min(), volume.max()
    if vmax > vmin:
        volume = (volume - vmin) / (vmax - vmin)
    return (volume * 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare BraTS classification dataset")
    ap.add_argument("--brats_root", required=True, help="Path to BraTS training data")
    ap.add_argument("--modality", default="flair", choices=["flair", "t1", "t1ce", "t2"])
    ap.add_argument("--out_dir", default="ai/data/classification", help="Output directory")
    ap.add_argument("--size", type=int, default=256, help="Output image size")
    args = ap.parse_args()

    brats_root = Path(args.brats_root)
    out_dir = Path(args.out_dir)
    
    # Create output directories
    benign_dir = out_dir / "benign"
    malignant_dir = out_dir / "malignant"
    benign_dir.mkdir(parents=True, exist_ok=True)
    malignant_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all subject directories
    subject_dirs = sorted([d for d in brats_root.iterdir() if d.is_dir()])
    print(f"Found {len(subject_dirs)} subjects in {brats_root}")
    
    stats = {"total_subjects": len(subject_dirs), "benign": 0, "malignant": 0}
    
    for subject_dir in tqdm(subject_dirs, desc="Processing subjects"):
        try:
            # Find segmentation file
            seg_files = list(subject_dir.glob("*_seg.nii.gz"))
            if not seg_files:
                # Try alternative naming
                seg_files = list(subject_dir.glob("*.nii.gz"))
                seg_files = [f for f in seg_files if "seg" in f.name.lower()]
            
            # Determine label
            label = 0
            if seg_files:
                label = get_tumor_label(seg_files[0])
            
            # Load and process image
            image = load_brats_subject(subject_dir, args.modality)
            image = normalize(image)
            slice_2d = extract_central_slice(image)
            slice_2d = cv2.resize(slice_2d, (args.size, args.size))
            
            # Save to appropriate folder
            output_dir = benign_dir if label == 0 else malignant_dir
            output_path = output_dir / f"{subject_dir.name}.png"
            cv2.imwrite(str(output_path), slice_2d)
            
            stats["benign" if label == 0 else "malignant"] += 1
            
        except Exception as e:
            print(f"Warning: Failed to process {subject_dir.name}: {e}")
    
    # Save statistics
    with open(out_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nDataset prepared:")
    print(f"  Total subjects: {stats['total_subjects']}")
    print(f"  Benign: {stats['benign']}")
    print(f"  Malignant: {stats['malignant']}")
    print(f"  Output directory: {out_dir}")


if __name__ == "__main__":
    main()