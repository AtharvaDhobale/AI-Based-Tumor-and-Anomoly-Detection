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


def _find_case_files(case_dir: Path, modality: str) -> tuple[Path | None, Path | None]:
    # BraTS commonly uses: *_flair.nii.gz, *_t1.nii.gz, *_t1ce.nii.gz, *_t2.nii.gz, *_seg.nii.gz
    img = next(iter(case_dir.glob(f"*_{modality}.nii*")), None)
    seg = next(iter(case_dir.glob("*_seg.nii*")), None)
    return img, seg


def _subject_id(case_dir: Path) -> str:
    return case_dir.name


def _export_case(
    *,
    case_dir: Path,
    modality: str,
    out_images: Path,
    out_masks: Path,
    stride: int,
    min_mask_mean: float,
) -> int:
    img_path, seg_path = _find_case_files(case_dir, modality)
    if not img_path or not seg_path:
        return 0

    img_vol = nib.load(str(img_path)).get_fdata()
    seg_vol = nib.load(str(seg_path)).get_fdata()
    if img_vol.shape != seg_vol.shape:
        return 0

    sid = _subject_id(case_dir)
    n = 0
    for z in range(0, img_vol.shape[2], max(1, stride)):
        img = _normalize_to_u8(img_vol[:, :, z])
        msk = (seg_vol[:, :, z] > 0).astype(np.uint8) * 255
        if float(msk.mean()) < float(min_mask_mean):
            continue
        img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_LINEAR)
        msk = cv2.resize(msk, (256, 256), interpolation=cv2.INTER_NEAREST)
        fname = f"{sid}_z{z:03d}.png"
        cv2.imwrite(str(out_images / fname), img)
        cv2.imwrite(str(out_masks / fname), msk)
        n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare BraTS case folders into 2D PNG segmentation dataset.")
    ap.add_argument("--brats_root", required=True, help="Folder containing BraTS case directories.")
    ap.add_argument("--modality", default="flair", choices=["flair", "t1", "t1ce", "t2"])
    ap.add_argument("--out_dir", default="ai/data/segmentation")
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--min_mask_mean", type=float, default=1.0, help="Skip slices with mean mask below this (0..255 scale).")
    args = ap.parse_args()

    root = Path(args.brats_root)
    out_images = Path(args.out_dir) / "images"
    out_masks = Path(args.out_dir) / "masks"
    out_images.mkdir(parents=True, exist_ok=True)
    out_masks.mkdir(parents=True, exist_ok=True)

    total = 0
    cases = [p for p in sorted(root.iterdir()) if p.is_dir()]
    for c in cases:
        total += _export_case(
            case_dir=c,
            modality=args.modality,
            out_images=out_images,
            out_masks=out_masks,
            stride=args.stride,
            min_mask_mean=args.min_mask_mean,
        )

    print(f"Exported {total} positive slices to {args.out_dir}")


if __name__ == "__main__":
    main()

