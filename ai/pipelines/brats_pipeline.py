from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    ap = argparse.ArgumentParser(description="End-to-end BraTS pipeline: prepare -> splits -> train -> eval.")
    ap.add_argument("--brats_root", required=True)
    ap.add_argument("--modality", default="flair", choices=["flair", "t1", "t1ce", "t2"])
    ap.add_argument("--out_seg_dir", default="ai/data/segmentation")
    ap.add_argument("--splits_dir", default="ai/data/splits")
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seg_epochs", type=int, default=20)
    args = ap.parse_args()

    py = sys.executable

    # 1) Prepare segmentation dataset (2D slices)
    _run(
        [
            py,
            "-m",
            "ai.datasets.prepare_brats_segmentation",
            "--brats_root",
            str(Path(args.brats_root)),
            "--modality",
            args.modality,
            "--out_dir",
            args.out_seg_dir,
            "--stride",
            str(args.stride),
        ]
    )

    # 2) Subject-level splits
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
            "--group_by_subject",
        ]
    )

    # 3) Train segmenter
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
        ]
    )

    # 4) Evaluate segmenter
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


if __name__ == "__main__":
    main()

