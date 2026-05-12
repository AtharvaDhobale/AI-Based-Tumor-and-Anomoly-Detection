from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import nibabel as nib
import numpy as np


def _normalize_to_u8(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32)
    p1, p99 = np.percentile(x, [1, 99])
    x = np.clip((x - p1) / max(1e-6, p99 - p1), 0.0, 1.0)
    return (x * 255.0).astype(np.uint8)


def _export_case(image_nii: Path, mask_nii: Path, out_images: Path, out_masks: Path, stride: int) -> int:
    img_vol = nib.load(str(image_nii)).get_fdata()
    msk_vol = nib.load(str(mask_nii)).get_fdata()
    if img_vol.shape != msk_vol.shape:
        return 0
    n = 0
    stem = image_nii.stem.replace(".nii", "")
    for z in range(0, img_vol.shape[2], max(1, stride)):
        img = _normalize_to_u8(img_vol[:, :, z])
        msk = (msk_vol[:, :, z] > 0).astype(np.uint8) * 255
        if msk.mean() < 1.0:
            continue
        img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_LINEAR)
        msk = cv2.resize(msk, (256, 256), interpolation=cv2.INTER_NEAREST)
        fname = f"{stem}_z{z:03d}.png"
        cv2.imwrite(str(out_images / fname), img)
        cv2.imwrite(str(out_masks / fname), msk)
        n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert NIfTI MRI+mask volumes into PNG slice dataset.")
    ap.add_argument("--images_dir", required=True, help="Directory containing *.nii or *.nii.gz MRI volumes")
    ap.add_argument("--masks_dir", required=True, help="Directory containing matching mask NIfTI volumes")
    ap.add_argument("--out_dir", default="ai/data/segmentation")
    ap.add_argument("--stride", type=int, default=2, help="Slice stride along z-axis")
    args = ap.parse_args()

    images_dir = Path(args.images_dir)
    masks_dir = Path(args.masks_dir)
    out_images = Path(args.out_dir) / "images"
    out_masks = Path(args.out_dir) / "masks"
    out_images.mkdir(parents=True, exist_ok=True)
    out_masks.mkdir(parents=True, exist_ok=True)

    image_files = sorted(list(images_dir.glob("*.nii")) + list(images_dir.glob("*.nii.gz")))
    total = 0
    for image_path in image_files:
        mask_path = masks_dir / image_path.name
        if not mask_path.exists():
            continue
        total += _export_case(image_path, mask_path, out_images, out_masks, args.stride)

    print(f"Exported {total} positive slices to {args.out_dir}")


if __name__ == "__main__":
    main()

