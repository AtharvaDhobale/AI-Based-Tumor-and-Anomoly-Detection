# BraTS Dataset Download and Training Guide

## Official BraTS Dataset Sources

### 1. TCIA (The Cancer Imaging Archive) - Primary Source
- **URL**: https://www.cancerimagingarchive.net/collections/the-brats-challenge/
- **Registration**: Free, requires account creation
- **Data**: Multi-institutional MRI scans with ground truth labels

### 2. Kaggle BraTS Challenges
- **BraTS 2021**: https://www.kaggle.com/c/rsna-miccai-brain-tumor-radiogenomic-classification
- **BraTS 2023**: https://www.kaggle.com/competitions/rsna-2023-abdominal-trauma-detection (related)
- **Note**: Kaggle competitions often host subsets

### 3. Medical Decathlon (MedNIST)
- **URL**: http://medicaldecathlon.com/
- **Purpose**: Alternative dataset for classification tasks

---

## Download Instructions

### Step 1: Register for TCIA Account
1. Go to: https://www.cancerimagingarchive.net/
2. Click "Register" in the top right
3. Verify your email

### Step 2: Download BraTS 2021 Data
1. Login to TCIA
2. Search for "BraTS 2021"
3. Download the following collections:
   - BraTS 2021 Training Data (~50GB)
   - BraTS 2021 Validation Data (~5GB)

### Step 3: Extract and Organize
```bash
# After downloading, extract:
tar -xvf BraTS2021_training_data.tar.gz
tar -xvf BraTS2021_validation_data.tar.gz
```

---

## Project Data Structure

Create this folder structure in your project:

```
ai/data/
├── brats/
│   ├── training/
│   │   ├── BraTS2021_00000/
│   │   │   ├── BraTS2021_00000_flair.nii.gz
│   │   │   ├── BraTS2021_00000_t1.nii.gz
│   │   │   ├── BraTS2021_00000_t1ce.nii.gz
│   │   │   ├── BraTS2021_00000_t2.nii.gz
│   │   │   └── BraTS2021_00000_seg.nii.gz
│   │   └── ...
│   └── validation/
│       └── ...
├── segmentation/
│   ├── images/
│   └── masks/
└── splits/
    ├── segmentation_train.csv
    ├── segmentation_val.csv
    └── segmentation_test.csv
```

---

## Training Commands

### Option 1: Full Pipeline (Prepare + Train + Evaluate)
```bash
cd mri-ai-tumor-system
python -m ai.pipelines.brats_pipeline --brats_root ai/data/brats/training
```

### Option 2: Step by Step

#### Step 2a: Prepare Segmentation Dataset
```bash
python -m ai.datasets.prepare_brats_segmentation \
    --brats_root ai/data/brats/training \
    --modality flair \
    --out_dir ai/data/segmentation \
    --stride 2
```

#### Step 2b: Create Train/Val/Test Splits
```bash
python -m ai.datasets.build_splits \
    --task segmentation \
    --data_dir ai/data/segmentation \
    --out_dir ai/data/splits \
    --seed 42 \
    --group_by_subject
```

#### Step 2c: Train Segmentation Model
```bash
python -m ai.training.train_segmenter \
    --train_csv ai/data/splits/segmentation_train.csv \
    --val_csv ai/data/splits/segmentation_val.csv \
    --epochs 20
```

#### Step 2d: Evaluate Model
```bash
python -m ai.training.evaluate_segmenter \
    --weights ai/weights/segmenter.pt \
    --test_csv ai/data/splits/segmentation_test.csv \
    --out ai/weights/segmenter_eval.json
```

---

## Alternative: Classification Training

For tumor classification (benign vs malignant):

### Step 1: Prepare Classification Data
```bash
python -m ai.datasets.prepare_classification_folders \
    --brats_root ai/data/brats/training \
    --out_dir ai/data/classification
```

### Step 2: Create Splits
```bash
python -m ai.datasets.build_splits \
    --task classification \
    --data_dir ai/data/classification \
    --out_dir ai/data/splits \
    --seed 42
```

### Step 3: Train Classifier
```bash
python -m ai.training.train_classifier \
    --train_csv ai/data/splits/classification_train.csv \
    --val_csv ai/data/splits/classification_val.csv \
    --epochs 30
```

### Step 4: Evaluate Classifier
```bash
python -m ai.training.evaluate_classifier \
    --weights ai/weights/classifier.pt \
    --test_csv ai/data/splits/classification_test.csv \
    --out ai/weights/classifier_eval.json
```

---

## Expected Results

### Segmentation Metrics (BraTS)
| Metric | Target |
|--------|--------|
| Dice Score | > 0.75 |
| Hausdorff Distance | < 5mm |
| Sensitivity | > 0.80 |

### Classification Metrics
| Metric | Target |
|--------|--------|
| Accuracy | > 90% |
| F1-Score | > 0.88 |
| AUC-ROC | > 0.95 |

---

## GPU Requirements

- **Minimum**: 8GB VRAM (GTX 1080 / RTX 2080)
- **Recommended**: 16GB+ VRAM (RTX 3090 / RTX 4090 / A100)
- **Batch Size**: Adjust based on available VRAM (8-32)

---

## Troubleshooting

### Out of Memory
```bash
# Reduce batch size in training script
--batch_size 4
```

### Slow Training
```bash
# Use mixed precision training
--use_amp
```

### Data Not Found
```bash
# Verify data paths
ls -la ai/data/brats/training/
```