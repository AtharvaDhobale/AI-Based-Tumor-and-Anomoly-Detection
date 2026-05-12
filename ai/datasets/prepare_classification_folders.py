from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _copy_all(src: Path, dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for p in src.rglob(ext):
            out = dst / f"{src.name}_{p.stem}{p.suffix.lower()}"
            shutil.copy2(p, out)
            n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge external classification datasets into benign/malignant folders.")
    ap.add_argument("--benign_src", nargs="*", default=[])
    ap.add_argument("--malignant_src", nargs="*", default=[])
    ap.add_argument("--out_dir", default="ai/data/classification")
    args = ap.parse_args()

    out_b = Path(args.out_dir) / "benign"
    out_m = Path(args.out_dir) / "malignant"
    benign_n = 0
    malignant_n = 0
    for s in args.benign_src:
        benign_n += _copy_all(Path(s), out_b)
    for s in args.malignant_src:
        malignant_n += _copy_all(Path(s), out_m)
    print(f"Prepared classification data at {args.out_dir}")
    print(f"benign: {benign_n}, malignant: {malignant_n}")


if __name__ == "__main__":
    main()

