from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def _infer_subject_id(path: str) -> str:
    """Best-effort subject id inference from filenames like <subject>_z012.png."""
    name = Path(path).name
    if "_z" in name:
        return name.split("_z", 1)[0]
    return Path(path).stem.split("_", 1)[0]


def _collect_classification(root: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for label in ("benign", "malignant"):
        for p in sorted((root / label).glob("*.png")):
            rows.append((str(p), label))
    return rows


def _collect_segmentation(root: Path) -> list[tuple[str, str]]:
    imgs = sorted((root / "images").glob("*.png"))
    out: list[tuple[str, str]] = []
    for img in imgs:
        m = root / "masks" / img.name
        if m.exists():
            out.append((str(img), str(m)))
    return out


def _write_csv(path: Path, header: list[str], rows: list[tuple[str, ...]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _split_groups(
    *,
    items: list[tuple[str, ...]],
    group_key_fn,
    train: float,
    val: float,
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]], list[tuple[str, ...]]]:
    groups: dict[str, list[tuple[str, ...]]] = {}
    for it in items:
        k = str(group_key_fn(it))
        groups.setdefault(k, []).append(it)

    keys = list(groups.keys())
    random.shuffle(keys)

    n = len(keys)
    n_train = int(n * train)
    n_val = int(n * val)
    k_train = set(keys[:n_train])
    k_val = set(keys[n_train : n_train + n_val])

    train_rows: list[tuple[str, ...]] = []
    val_rows: list[tuple[str, ...]] = []
    test_rows: list[tuple[str, ...]] = []
    for k, rows in groups.items():
        if k in k_train:
            train_rows.extend(rows)
        elif k in k_val:
            val_rows.extend(rows)
        else:
            test_rows.extend(rows)
    return train_rows, val_rows, test_rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Build reproducible train/val/test split CSVs.")
    ap.add_argument("--task", choices=["classification", "segmentation"], required=True)
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--out_dir", default="ai/data/splits")
    ap.add_argument("--train", type=float, default=0.7)
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--group_by_subject",
        action="store_true",
        help="Do subject-level splits (prevents patient leakage). Recommended for BraTS.",
    )
    args = ap.parse_args()

    root = Path(args.data_dir)
    random.seed(args.seed)

    if args.task == "classification":
        samples = _collect_classification(root)
        if args.group_by_subject:
            train_rows, val_rows, test_rows = _split_groups(
                items=[(p, y) for p, y in samples],
                group_key_fn=lambda r: _infer_subject_id(r[0]),
                train=args.train,
                val=args.val,
            )
        else:
            random.shuffle(samples)
            n = len(samples)
            n_train = int(n * args.train)
            n_val = int(n * args.val)
            train_rows = [(p, y) for p, y in samples[:n_train]]
            val_rows = [(p, y) for p, y in samples[n_train : n_train + n_val]]
            test_rows = [(p, y) for p, y in samples[n_train + n_val :]]
        out = Path(args.out_dir)
        _write_csv(out / "classification_train.csv", ["image_path", "label"], train_rows)
        _write_csv(out / "classification_val.csv", ["image_path", "label"], val_rows)
        _write_csv(out / "classification_test.csv", ["image_path", "label"], test_rows)
    else:
        samples = _collect_segmentation(root)
        if args.group_by_subject:
            train_rows, val_rows, test_rows = _split_groups(
                items=[(i, m) for i, m in samples],
                group_key_fn=lambda r: _infer_subject_id(r[0]),
                train=args.train,
                val=args.val,
            )
        else:
            random.shuffle(samples)
            n = len(samples)
            n_train = int(n * args.train)
            n_val = int(n * args.val)
            train_rows = [(i, m) for i, m in samples[:n_train]]
            val_rows = [(i, m) for i, m in samples[n_train : n_train + n_val]]
            test_rows = [(i, m) for i, m in samples[n_train + n_val :]]
        out = Path(args.out_dir)
        _write_csv(out / "segmentation_train.csv", ["image_path", "mask_path"], train_rows)
        _write_csv(out / "segmentation_val.csv", ["image_path", "mask_path"], val_rows)
        _write_csv(out / "segmentation_test.csv", ["image_path", "mask_path"], test_rows)

    print(f"Split files written under {args.out_dir}")


if __name__ == "__main__":
    main()

