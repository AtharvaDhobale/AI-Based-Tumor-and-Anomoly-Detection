"""
BraTS Segmentation Dataset Preparation

Converts BraTS NIfTI volumes to 2D slices for segmentation training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import nibabel as nib
import numpy as np
from tqdm import tqdm


def load_brats_subject(subject_dir: Path, modality: str = "flair") -> tuple[np.ndarray, np.ndarray]:
    """Load a BraTS subject's imaging data and segmentation mask.
    
    Args:
        subject_dir: Path to subject folder (e.g., BraTS2021_00000)
        modality: MRI modality to load (flair, t1, t1ce, t2)
    
    Returns:
        Tuple of (image, mask) as numpy arrays
    """
    # Find NIfTI files
    flair_file = None
    seg_file = None
    
    for f in subject_dir.glob("*.nii.gz"):
        if "_flair" in f.name and modality == "flair":
            flair_file = f
        elif "_t1" in f.name and modality == "t1" and "ce" not in f.name:
            flair_file = f
        elif "_t1ce" in f.name and modality == "t1ce":
            flair_file = f
        elif "_t2" in f.name and modality == "t2":
            flair_file = f
        elif "_seg" in f.name:
            seg_file = f
    
    if flair_file is None:
        # Try generic search
        files = list(subject_dir.glob(f"*_{modality}.nii.gz"))
        if files:
            flair_file = files[0]
    
    if seg_file is None:
        files = list(subject_dir.glob("*_seg.nii.gz"))
        if files:
            seg_file = files[0]
    
    if flair_file is None:
        raise FileNotFoundError(f"No {modality} file found in {subject_dir}")
    
    # Load NIfTI
    img = nib.load(str(flair_file))
    image = img.get_fdata()
    
    if seg_file:
        seg = nib.load(str(seg_file))
        mask = seg.get_fdata()
    else:
        mask = np.zeros_like(image)
    
    return image, mask


def extract_slices(image: np.ndarray, mask: np.ndarray, stride: int = 2) -> list[tuple[np.ndarray, np.ndarray]]:
    """Extract 2D slices from 3D volume at regular intervals.
    
    Args:
        image: 3D MRI volume
        mask: 3D segmentation mask
        stride: Interval between slices
    
    Returns:
        List of (slice, mask_slice) tuples
    """
    slices = []
    z = image.shape[2]
    
    for i in range(0, z, stride):
        img_slice = image[:, :, i]
        mask_slice = mask[:, :, i]
        
        # Only include slices with tumor content (for balanced training)
        if mask_slice.max() > 0:
            slices.append((img_slice, mask_slice))
        # Also include some background slices
        elif i % (stride * 3) == 0:
            slices.append((img_slice, mask_slice))
    
    return slices


def normalize(volume: np.ndarray) -> np.ndarray:
    """Normalize MRI volume to [0, 255] range."""
    vmin, vmax = volume.min(), volume.max()
    if vmax > vmin:
        volume = (volume - vmin) / (vmax - vmin)
    return (volume * 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare BraTS segmentation dataset")
    ap.add_argument("--brats_root", required=True, help="Path to BraTS training data")
    ap.add_argument("--modality", default="flair", choices=["flair", "t1", "t1ce", "t2"])
    ap.add_argument("--out_dir", default="ai/data/segmentation", help="Output directory")
    ap.add_argument("--stride", type=int, default=2, help="Slice extraction stride")
    ap.add_argument("--size", type=int, default=256, help="Output image size")
    args = ap.parse_args()

    brats_root = Path(args.brats_root)
    out_dir = Path(args.out_dir)
    
    # Create output directories
    images_dir = out_dir / "images"
    masks_dir = out_dir / "masks"
    images_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all subject directories
    subject_dirs = sorted([d for d in brats_root.iterdir() if d.is_dir()])
    print(f"Found {len(subject_dirs)} subjects in {brats_root}")
    
    stats = {"total_subjects": len(subject_dirs), "total_slices": 0, "slices_with_tumor": 0}
    
    for subject_dir in tqdm(subject_dirs, desc="Processing subjects"):
        try:
            # Load subject data
            image, mask = load_brats_subject(subject_dir, args.modality)
            
            # Normalize
            image = normalize(image)
            
            # Extract slices
            slices = extract_slices(image, mask, args.stride)
            
            for idx, (img_slice, mask_slice) in enumerate(slices):
                # Resize
                img_slice = cv2.resize(img_slice, (args.size, args.size))
                mask_slice = cv2.resize(mask_slice, (args.size, args.size), interpolation=cv2.INTER_NEAREST)
                
                # Convert mask to binary (0=background, 255=tumor)
                mask_slice = (mask_slice > 0).astype(np.uint8) * 255
                
                # Save
                subject_name = subject_dir.name
                img_path = images_dir / f"{subject_name}_{idx:04d}.png"
                mask_path = masks_dir / f"{subject_name}_{idx:04d}.png"
                
                cv2.imwrite(str(img_path), img_slice)
                cv2.imwrite(str(mask_path), mask_slice)
                
                stats["total_slices"] += 1
                if mask_slice.max() > 0:
                    stats["slices_with_tumor"] += 1
                    
        except Exception as e:
            print(f"Warning: Failed to process {subject_dir.name}: {e}")
    
    # Save statistics
    with open(out_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nDataset prepared:")
    print(f"  Total subjects: {stats['total_subjects']}")
    print(f"  Total slices: {stats['total_slices']}")
    print(f"  Slices with tumor: {stats['slices_with_tumor']}")
    print(f"  Output directory: {out_dir}")


if __name__ == "__main__":
    main()