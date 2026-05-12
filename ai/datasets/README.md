# Medical Dataset Pipeline

This folder contains a reproducible dataset pipeline for high-quality MRI training.

## 1) Recommended Sources

See `registry.json` for curated sources (BraTS, TCIA UTSW/UCSF/BraTS-PEDs, Figshare).

- Prefer BraTS + TCIA for segmentation and clinically meaningful training.
- Use Figshare-like sets only for classifier warm-start, not final clinical claims.

## 2) Legal and Governance

- Follow each dataset's license and citation requirements.
- Do not redistribute restricted data.
- Maintain patient privacy and de-identification constraints.

## 3) Convert NIfTI Segmentation Data

Expected:
- MRI volumes in `--images_dir`
- matching mask volumes in `--masks_dir` with same filenames

Command:

```bash
python -m ai.datasets.prepare_nifti_segmentation --images_dir "<path_to_nifti_images>" --masks_dir "<path_to_nifti_masks>" --out_dir ai/data/segmentation --stride 2
```

Output:
- `ai/data/segmentation/images/*.png`
- `ai/data/segmentation/masks/*.png`

### BraTS folder conversion (recommended)

If you have a BraTS download where each case is a folder containing `*_flair.nii.gz` and `*_seg.nii.gz` (plus other modalities),
you can build a segmentation slice dataset like this:

```bash
python -m ai.datasets.prepare_brats_segmentation --brats_root "<path_to_brats_cases_root>" --modality flair --out_dir ai/data/segmentation --stride 2
```

Then build **subject-level splits** (prevents patient leakage across train/val/test):

```bash
python -m ai.datasets.build_splits --task segmentation --data_dir ai/data/segmentation --out_dir ai/data/splits --seed 42 --group_by_subject
```

## 4) Build Classification Dataset

Merge external folders into benign/malignant structure:

```bash
python -m ai.datasets.prepare_classification_folders --benign_src "<path_benign_1>" "<path_benign_2>" --malignant_src "<path_malignant_1>" "<path_malignant_2>" --out_dir ai/data/classification
```

## 5) Create Reproducible Splits

Classification:

```bash
python -m ai.datasets.build_splits --task classification --data_dir ai/data/classification --out_dir ai/data/splits --seed 42
```

Segmentation:

```bash
python -m ai.datasets.build_splits --task segmentation --data_dir ai/data/segmentation --out_dir ai/data/splits --seed 42
```

## 6) Train

Classifier:

```bash
python -m ai.training.train_classifier --data_dir ai/data/classification --epochs 15
```

With fixed splits:

```bash
python -m ai.training.train_classifier --train_csv ai/data/splits/classification_train.csv --val_csv ai/data/splits/classification_val.csv --epochs 15
```

Segmenter:

```bash
python -m ai.training.train_segmenter --data_dir ai/data/segmentation --epochs 20
```

With fixed splits:

```bash
python -m ai.training.train_segmenter --train_csv ai/data/splits/segmentation_train.csv --val_csv ai/data/splits/segmentation_val.csv --epochs 20
```

## 8) Evaluate Classifier on Held-Out Test

```bash
python -m ai.training.evaluate_classifier --weights ai/weights/classifier.pt --test_csv ai/data/splits/classification_test.csv --out ai/weights/classifier_eval.json
```

## 9) Evaluate Segmenter on Held-Out Test (Dice/IoU)

This expects a test split CSV with columns:

- `image_path`
- `mask_path`

```bash
python -m ai.training.evaluate_segmenter --weights ai/weights/segmenter.pt --test_csv ai/data/splits/segmentation_test.csv --out ai/weights/segmenter_eval.json
```

## 7) Clinical-Grade Next Steps

- External-site validation split (never seen in train).
- Report sensitivity/specificity/AUC/F1 and false-negative rate.
- Calibrate probabilities (temperature scaling or isotonic).
- Track model/data version for every trained checkpoint.

