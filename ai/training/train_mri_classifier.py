"""
Simple MRI Classifier using Traditional ML

Uses HOG features + SVM for fast training without GPU.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import cv2
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, classification_report, 
                            confusion_matrix, f1_score, precision_score, 
                            recall_score, roc_auc_score)
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm


def extract_hog_features(image: np.ndarray) -> np.ndarray:
    """Extract HOG (Histogram of Oriented Gradients) features."""
    # Resize to standard size
    img = cv2.resize(image, (128, 128))
    
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Compute gradients
    gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=1)
    gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=1)
    
    # Compute magnitude and angle
    mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    
    # Create histogram of gradients
    hist = []
    bin_size = 20  # 9 bins for 0-180 degrees
    for i in range(0, 180, bin_size):
        mask = ((angle >= i) & (angle < i + bin_size))
        hist.append(mag[mask].sum())
    
    # Normalize
    hist = np.array(hist)
    if hist.max() > 0:
        hist = hist / hist.max()
    
    return hist


def extract_features(image: np.ndarray) -> np.ndarray:
    """Extract multiple features from image."""
    features = []
    
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # 1. HOG features
    hog_feat = extract_hog_features(gray)
    features.extend(hog_feat)
    
    # 2. Statistical features
    features.append(gray.mean())
    features.append(gray.std())
    features.append(np.median(gray))
    features.append(gray.min())
    features.append(gray.max())
    
    # 3. Histogram features (16 bins)
    hist, _ = np.histogram(gray.flatten(), bins=16, range=(0, 256))
    hist = hist / hist.sum()  # Normalize
    features.extend(hist)
    
    # 4. Texture features (simple)
    # Compute local variance (texture indicator)
    kernel_size = 5
    local_var = cv2.blur(gray.astype(np.float32)**2, (kernel_size, kernel_size)) - \
                cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))**2
    features.append(local_var.mean())
    features.append(local_var.std())
    
    # 5. Edge features
    edges = cv2.Canny(gray, 50, 150)
    features.append(edges.mean())
    features.append((edges > 0).sum() / edges.size)  # Edge density
    
    # 6. Center vs edge intensity ratio
    h, w = gray.shape
    center_region = gray[h//4:3*h//4, w//4:3*w//4]
    features.append(center_region.mean())
    features.append(center_region.std())
    
    return np.array(features)


class SimpleMRIDataset:
    """Simple dataset loader."""
    
    def __init__(self, csv_path: str):
        self.samples = []
        # Get the base directory (ai folder)
        csv_path = Path(csv_path)
        base_dir = csv_path.parent.parent.parent  # Go up from splits/ to ai/
        
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Convert string labels to integers
                label_str = str(r["label"]).strip().lower()
                label = 1 if label_str == "malignant" else 0
                
                # Resolve relative path
                img_path = base_dir / r["image_path"]
                self.samples.append((str(img_path), label))
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        if idx == 0:
            print(f"Loading image from: {path}")
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"ERROR: Could not read image: {path}")
            raise RuntimeError(f"Could not read image: {path}")
        # Resize to standard size
        img = cv2.resize(img, (128, 128))
        features = extract_features(img)
        # Debug: print feature shape
        feat_arr = np.array(features)
        if idx == 0:
            print(f"Feature shape: {feat_arr.shape}, dtype: {feat_arr.dtype}, first few: {feat_arr[:5] if len(feat_arr) > 0 else 'empty'}")
        return features, label


def train_model(train_csv: str, val_csv: str, output_path: str) -> dict:
    """Train the classifier."""
    print("Loading training data...")
    train_dataset = SimpleMRIDataset(train_csv)
    val_dataset = SimpleMRIDataset(val_csv)
    
    # Extract features
    X_train = []
    y_train = []
    print("Extracting training features...")
    for i in tqdm(range(len(train_dataset)), desc="Training"):
        try:
            features, label = train_dataset[i]
            feat = np.array(features)
            if len(feat.shape) > 0 and feat.shape[0] > 0:
                X_train.append(feat)
                y_train.append(label)
            else:
                print(f"Warning: Empty features for sample {i}")
        except Exception as e:
            print(f"Error processing sample {i}: {e}")
    
    X_val = []
    y_val = []
    print("Extracting validation features...")
    for i in tqdm(range(len(val_dataset)), desc="Validation"):
        try:
            features, label = val_dataset[i]
            feat = np.array(features)
            if len(feat.shape) > 0 and feat.shape[0] > 0:
                X_val.append(feat)
                y_val.append(label)
            else:
                print(f"Warning: Empty features for sample {i}")
        except Exception as e:
            print(f"Error processing sample {i}: {e}")
    
    print(f"Extracted {len(X_train)} training, {len(X_val)} validation features")
    
    if len(X_train) == 0:
        raise RuntimeError("No features extracted! Check image paths and feature extraction.")
    
    X_train = np.array(X_train)
    y_train = np.array(y_train)
    X_val = np.array(X_val)
    y_val = np.array(y_val)
    
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Feature dimensions: {X_train.shape[1]}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train model
    print("\nTraining Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_val_scaled)
    y_prob = model.predict_proba(X_val_scaled)[:, 1]
    
    metrics = {
        "accuracy": accuracy_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred),
        "recall": recall_score(y_val, y_pred),
        "f1_score": f1_score(y_val, y_pred),
        "roc_auc": roc_auc_score(y_val, y_prob),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist()
    }
    
    print("\n=== Validation Results ===")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1-Score: {metrics['f1_score']:.4f}")
    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"\nConfusion Matrix:\n{metrics['confusion_matrix']}")
    
    # Save model
    import pickle
    model_data = {
        "model": model,
        "scaler": scaler,
        "metrics": metrics
    }
    with open(output_path, "wb") as f:
        pickle.dump(model_data, f)
    
    print(f"\nModel saved to: {output_path}")
    
    return metrics


def evaluate_model(model_path: str, test_csv: str) -> dict:
    """Evaluate the trained model on test data."""
    import pickle
    
    print(f"Loading model from: {model_path}")
    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
    
    model = model_data["model"]
    scaler = model_data["scaler"]
    
    print("Loading test data...")
    test_dataset = SimpleMRIDataset(test_csv)
    
    X_test = []
    y_test = []
    for i in tqdm(range(len(test_dataset)), desc="Testing"):
        try:
            features, label = test_dataset[i]
            X_test.append(np.array(features))
            y_test.append(label)
        except Exception as e:
            print(f"Error processing sample {i}: {e}")
    
    X_test = np.array(X_test)
    y_test = np.array(y_test)
    
    X_test_scaled = scaler.transform(X_test)
    
    # Predict
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
    }
    
    print("\n=== Test Results ===")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1-Score: {metrics['f1_score']:.4f}")
    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"\nConfusion Matrix:\n{metrics['confusion_matrix']}")
    
    return metrics


def main() -> None:
    ap = argparse.ArgumentParser(description="Train MRI Classifier")
    ap.add_argument("--train_csv", required=True, help="Training CSV")
    ap.add_argument("--val_csv", required=True, help="Validation CSV")
    ap.add_argument("--test_csv", default=None, help="Test CSV (optional)")
    ap.add_argument("--output", default="ai/weights/classifier.pkl", help="Output model path")
    args = ap.parse_args()

    # Train
    train_model(args.train_csv, args.val_csv, args.output)
    
    # Test if provided
    if args.test_csv:
        evaluate_model(args.output, args.test_csv)


if __name__ == "__main__":
    main()