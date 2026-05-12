"""
Synthetic MRI Dataset Generator for Training

Creates realistic brain MRI-like images for model training without downloading large datasets.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm


def create_brain_outline(size: int = 256) -> np.ndarray:
    """Create a brain-shaped outline."""
    canvas = np.zeros((size, size), dtype=np.uint8)
    
    # Create elliptical brain shape
    center = (size // 2, size // 2)
    axes = (size // 2 - 20, size // 2 - 30)
    
    cv2.ellipse(canvas, center, axes, 0, 0, 360, 255, -1)
    
    # Add some irregularity to make it look more natural
    kernel = np.ones((5, 5), np.uint8)
    canvas = cv2.morphologyEx(canvas, cv2.MORPH_CLOSE, kernel)
    
    return canvas


def add_ventricles(brain_mask: np.ndarray, size: int = 256) -> np.ndarray:
    """Add ventricle-like structures inside the brain."""
    canvas = brain_mask.copy()
    
    # Left ventricle
    left_center = (size // 2 - 30, size // 2 - 20)
    cv2.ellipse(canvas, left_center, (15, 25), 0, 0, 360, 0, -1)
    
    # Right ventricle
    right_center = (size // 2 + 30, size // 2 - 20)
    cv2.ellipse(canvas, right_center, (15, 25), 0, 0, 360, 0, -1)
    
    return canvas


def add_tumor(brain_mask: np.ndarray, size: int = 256, severity: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Add tumor-like region inside the brain.
    
    Args:
        brain_mask: Brain outline
        size: Image size
        severity: 1=small, 2=medium, 3=large
    
    Returns:
        Tuple of (brain with tumor, tumor mask)
    """
    canvas = brain_mask.copy()
    tumor_mask = np.zeros((size, size), dtype=np.uint8)
    
    # Random tumor position within brain
    center_x = random.randint(size // 3, 2 * size // 3)
    center_y = random.randint(size // 3, 2 * size // 3)
    
    # Tumor size based on severity
    tumor_radius = random.randint(15, 35) * severity // 2
    
    # Draw tumor with irregular edges
    num_points = random.randint(8, 16)
    for _ in range(num_points):
        angle = random.uniform(0, 2 * np.pi)
        r = tumor_radius * random.uniform(0.8, 1.2)
        x = int(center_x + r * np.cos(angle))
        y = int(center_y + r * np.sin(angle))
        cv2.circle(tumor_mask, (x, y), tumor_radius // 3, 255, -1)
    
    # Add to brain (darker region for tumor)
    canvas = cv2.subtract(canvas, tumor_mask)
    
    return canvas, tumor_mask


def generate_mri_image(
    size: int = 256,
    has_tumor: bool = True,
    tumor_severity: int = 1,
    noise_level: float = 0.1,
    add_artifacts: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic MRI brain image.
    
    Args:
        size: Image size
        has_tumor: Whether to add tumor
        tumor_severity: Tumor size (1-3)
        noise_level: MRI noise level
        add_artifacts: Add MRI artifacts
    
    Returns:
        Tuple of (brain image, tumor mask)
    """
    # Create base brain
    brain = create_brain_outline(size)
    
    # Add ventricles
    brain = add_ventricles(brain, size)
    
    tumor_mask = np.zeros((size, size), dtype=np.uint8)
    
    # Add tumor if requested
    if has_tumor:
        brain, tumor_mask = add_tumor(brain, size, tumor_severity)
    
    # Convert to grayscale (MRI-like)
    brain = brain.astype(np.float32)
    
    # Add Gaussian noise (MRI artifact)
    if noise_level > 0:
        noise = np.random.normal(0, noise_level * 50, brain.shape)
        brain = brain + noise
    
    # Add intensity variations (natural MRI look)
    for _ in range(5):
        x = random.randint(0, size - 50)
        y = random.randint(0, size - 50)
        w = random.randint(20, 50)
        brightness = random.uniform(0.8, 1.2)
        roi = brain[y:y+w, x:x+w]
        brain[y:y+w, x:x+w] = roi * brightness
    
    # Add ring artifact (common MRI artifact)
    if add_artifacts:
        for r in range(30, 120, 20):
            cv2.circle(brain, (size//2, size//2), r, random.uniform(-10, 10), 2)
    
    # Normalize to 0-255
    brain = np.clip(brain, 0, 255)
    brain = brain.astype(np.uint8)
    
    # Apply slight blur for MRI realism
    brain = cv2.GaussianBlur(brain, (3, 3), 0.5)
    
    return brain, tumor_mask


def generate_dataset(
    output_dir: Path,
    num_benign: int = 100,
    num_malignant: int = 100,
    size: int = 256,
    seed: int = 42
) -> dict:
    """Generate a complete synthetic MRI dataset.
    
    Args:
        output_dir: Output directory
        num_benign: Number of benign samples
        num_malignant: Number of malignant samples
        size: Image size
        seed: Random seed
    
    Returns:
        Statistics dictionary
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Create directories
    benign_dir = output_dir / "benign"
    malignant_dir = output_dir / "malignant"
    benign_dir.mkdir(parents=True, exist_ok=True)
    malignant_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {"benign": 0, "malignant": 0}
    
    # Generate benign samples
    print(f"Generating {num_benign} benign samples...")
    for i in tqdm(range(num_benign)):
        img, _ = generate_mri_image(
            size=size,
            has_tumor=False,
            noise_level=random.uniform(0.05, 0.15)
        )
        path = benign_dir / f"benign_{i:04d}.png"
        cv2.imwrite(str(path), img)
        stats["benign"] += 1
    
    # Generate malignant samples
    print(f"Generating {num_malignant} malignant samples...")
    for i in tqdm(range(num_malignant)):
        severity = random.randint(1, 3)
        img, mask = generate_mri_image(
            size=size,
            has_tumor=True,
            tumor_severity=severity,
            noise_level=random.uniform(0.05, 0.15)
        )
        path = malignant_dir / f"malignant_{i:04d}.png"
        cv2.imwrite(str(path), img)
        stats["malignant"] += 1
    
    # Save statistics
    stats["total"] = stats["benign"] + stats["malignant"]
    stats["size"] = size
    
    with open(output_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nDataset generated:")
    print(f"  Benign: {stats['benign']}")
    print(f"  Malignant: {stats['malignant']}")
    print(f"  Total: {stats['total']}")
    print(f"  Output: {output_dir}")
    
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate synthetic MRI dataset")
    ap.add_argument("--output", default="ai/data/mri_dataset", help="Output directory")
    ap.add_argument("--num_benign", type=int, default=100, help="Number of benign samples")
    ap.add_argument("--num_malignant", type=int, default=100, help="Number of malignant samples")
    ap.add_argument("--size", type=int, default=256, help="Image size")
    ap.add_argument("--seed", type=int, default=42, help="Random seed")
    args = ap.parse_args()

    output_dir = Path(args.output)
    generate_dataset(
        output_dir=output_dir,
        num_benign=args.num_benign,
        num_malignant=args.num_malignant,
        size=args.size,
        seed=args.seed
    )


if __name__ == "__main__":
    main()