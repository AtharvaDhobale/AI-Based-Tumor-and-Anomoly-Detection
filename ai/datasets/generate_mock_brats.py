"""
Synthetic NIfTI Generator for simulating a subset of the BraTS dataset.
Creates T1, T1ce, T2, FLAIR, and Seg volumes for training/validation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import numpy as np
import nibabel as nib

def generate_mock_case(case_dir: Path, case_id: str, shape: tuple[int, int, int] = (128, 128, 64)) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create a 3D coordinate grid
    x, y, z = np.ogrid[:shape[0], :shape[1], :shape[2]]
    cx, cy, cz = shape[0] // 2, shape[1] // 2, shape[2] // 2
    
    # 2. Draw ellipsoid brain outline
    # Brain semi-axes
    bx, by, bz = shape[0] // 2 - 10, shape[1] // 2 - 15, shape[2] // 2 - 5
    brain_mask = ((x - cx)**2 / bx**2 + (y - cy)**2 / by**2 + (z - cz)**2 / bz**2) < 1.0
    
    # 3. Ventricles (two parallel ellipsoids near center)
    v1_mask = (((x - (cx - 15))**2 / 8**2 + (y - (cy - 10))**2 / 20**2 + (z - cz)**2 / 12**2) < 1.0) & brain_mask
    v2_mask = (((x - (cx + 15))**2 / 8**2 + (y - (cy - 10))**2 / 20**2 + (z - cz)**2 / 12**2) < 1.0) & brain_mask
    ventricles = v1_mask | v2_mask
    
    # 4. Tumor (with irregular spherical noise at random location inside brain)
    has_tumor = np.random.rand() < 0.8
    tumor_mask = np.zeros(shape, dtype=bool)
    if has_tumor:
        tcx = int(cx + np.random.randint(-20, 20))
        tcy = int(cy + np.random.randint(-20, 20))
        tcz = int(cz + np.random.randint(-10, 10))
        # Draw tumor
        tr = np.random.randint(12, 24)
        dist_sq = (x - tcx)**2 + (y - tcy)**2 + (z - tcz)**2
        # Add slight boundary noise
        noise = np.random.normal(0, 2.0, shape)
        tumor_mask = ((dist_sq + noise) < tr**2) & brain_mask
        
    # 5. Base matter tissue values
    # We will formulate FLAIR, T1, T1ce, T2 intensities
    # Background is always 0
    
    # --- FLAIR Modality ---
    flair = np.zeros(shape, dtype=np.float32)
    flair[brain_mask] = 100.0  # brain tissue
    flair[ventricles] = 10.0   # dark CSF
    if has_tumor:
        flair[tumor_mask] = 230.0  # hyperintense tumor
    # Add random Gaussian noise
    flair += np.random.normal(0, 5.0, shape)
    flair = np.clip(flair, 0, 255)
    
    # --- T1 Modality ---
    t1 = np.zeros(shape, dtype=np.float32)
    t1[brain_mask] = 120.0
    t1[ventricles] = 20.0
    if has_tumor:
        t1[tumor_mask] = 70.0  # hypointense tumor
    t1 += np.random.normal(0, 5.0, shape)
    t1 = np.clip(t1, 0, 255)

    # --- T1ce Modality ---
    t1ce = t1.copy()
    if has_tumor:
        # Enhancing ring around tumor
        inner_r = max(2, tr - 6)
        ring_mask = tumor_mask & ((dist_sq + noise) >= inner_r**2)
        t1ce[ring_mask] = 220.0
    t1ce += np.random.normal(0, 4.0, shape)
    t1ce = np.clip(t1ce, 0, 255)

    # --- T2 Modality ---
    t2 = np.zeros(shape, dtype=np.float32)
    t2[brain_mask] = 90.0
    t2[ventricles] = 240.0  # bright CSF
    if has_tumor:
        t2[tumor_mask] = 180.0  # hyperintense tumor
    t2 += np.random.normal(0, 5.0, shape)
    t2 = np.clip(t2, 0, 255)

    # --- Seg Modality ---
    # In BraTS, seg values are 0 (BG), 1 (Necrotic core), 2 (Edema), 4 (Enhancing)
    # Any value > 0 is treated as tumor in prepare_brats_segmentation.py
    seg = np.zeros(shape, dtype=np.uint8)
    if has_tumor:
        # Let's map necrotic core and enhancing core
        seg[tumor_mask] = 2  # Edema
        inner_r = max(2, tr - 6)
        inner_mask = tumor_mask & ((dist_sq + noise) < inner_r**2)
        seg[inner_mask] = 1  # Necrotic
        ring_mask = tumor_mask & ((dist_sq + noise) >= inner_r**2)
        seg[ring_mask] = 4  # Enhancing
            
    # Save NIfTI volumes
    affine = np.eye(4)
    for name, vol in [("flair", flair), ("t1", t1), ("t1ce", t1ce), ("t2", t2)]:
        vol_img = nib.Nifti1Image(vol, affine)
        nib.save(vol_img, str(case_dir / f"{case_id}_{name}.nii.gz"))
        
    seg_img = nib.Nifti1Image(seg, affine)
    nib.save(seg_img, str(case_dir / f"{case_id}_seg.nii.gz"))
    print(f"Generated case {case_id} in {case_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic NIfTI brain datasets resembling BraTS.")
    parser.add_argument("--num_cases", type=int, default=5, help="Number of simulated cases to generate.")
    parser.add_argument("--out_dir", default="ai/data/brats/training", help="Output root directory.")
    args = parser.parse_args()
    
    out_path = Path(args.out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    for i in range(args.num_cases):
        case_id = f"BraTS2021_{i:05d}"
        case_dir = out_path / case_id
        generate_mock_case(case_dir, case_id)
        
    print(f"\nSuccessfully generated {args.num_cases} synthetic BraTS cases under: {args.out_dir}")

if __name__ == "__main__":
    main()
