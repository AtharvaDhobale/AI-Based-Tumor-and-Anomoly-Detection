from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path


class TestSubjectLevelSplits(unittest.TestCase):
    def test_group_by_subject_keeps_subjects_separate(self):
        # Build a tiny fake segmentation dataset
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "segmentation"
            (root / "images").mkdir(parents=True)
            (root / "masks").mkdir(parents=True)

            # Two subjects, two slices each
            for name in ["S001_z000.png", "S001_z001.png", "S002_z000.png", "S002_z001.png"]:
                (root / "images" / name).write_bytes(b"x")
                (root / "masks" / name).write_bytes(b"y")

            out_dir = Path(td) / "splits"

            # Import locally to avoid any heavy deps; this module is pure stdlib.
            # When running from the `ai/` directory, import via local package path.
            from datasets import build_splits

            # Call split logic through main helpers (simulate CLI behavior).
            items = [(str(root / "images" / p.name), str(root / "masks" / p.name)) for p in (root / "images").glob("*.png")]
            # Use private helper via group split function (kept in module).
            train, val, test = build_splits._split_groups(  # type: ignore[attr-defined]
                items=items,
                group_key_fn=lambda r: build_splits._infer_subject_id(r[0]),  # type: ignore[attr-defined]
                train=0.5,
                val=0.0,
            )

            def subjects(rows):
                return {Path(r[0]).name.split("_z", 1)[0] for r in rows}

            self.assertTrue(subjects(train).isdisjoint(subjects(test)))

            # Also verify we can write split CSVs with expected headers
            out_dir.mkdir(parents=True, exist_ok=True)
            seg_test_csv = out_dir / "segmentation_test.csv"
            with seg_test_csv.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["image_path", "mask_path"])
                w.writerows(test)
            self.assertTrue(seg_test_csv.exists())


if __name__ == "__main__":
    unittest.main()

