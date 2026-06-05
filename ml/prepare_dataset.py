"""
Prepare Merged Dataset for CNN Training — BreastCare AI
========================================================
Combines THREE data sources into a 3-class dataset:

  Class 0 — Benign tissue
  Class 1 — Malignant tissue
  Class 2 — Unrelated (non-tissue) images

Sources used automatically (no external download needed):

  Source 1  Real patient image patches from data/<patient_id>/0/ and /1/
            Folders: 8863, 8864, 8865, 8867, 8913 (or any numeric folder)

  Source 2  Wisconsin Breast Cancer CSV (data/breast-cancer.csv)
            Each row rendered as a 50x50 colour heatmap image

  Source 3  Synthetic unrelated images (generated automatically)
            Covers: solid colours, noise, white documents, gradients,
            geometric shapes, dark images, overexposed images

Output:
  data/merged_dataset/
    0/   <- benign   (patches + CSV heatmaps)
    1/   <- malignant (patches + CSV heatmaps)
    2/   <- unrelated (synthetic)

Usage:
  python ml/prepare_dataset.py
  python ml/prepare_dataset.py --max 5000   # limit patches per class
  python ml/prepare_dataset.py --no-csv     # skip CSV heatmaps
"""

import os, sys, shutil, glob, argparse
import numpy as np
import cv2

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, 'data')
CSV_PATH  = os.path.join(DATA_DIR, 'breast-cancer.csv')
OUT_DIR   = os.path.join(DATA_DIR, 'merged_dataset')
IMG_SIZE  = 50

FEATURES = [
    'radius_mean','texture_mean','perimeter_mean','area_mean','smoothness_mean',
    'compactness_mean','concavity_mean','concave points_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','perimeter_se','area_se','smoothness_se',
    'compactness_se','concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'radius_worst','texture_worst','perimeter_worst','area_worst','smoothness_worst',
    'compactness_worst','concavity_worst','concave points_worst','symmetry_worst','fractal_dimension_worst',
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_patient_folders():
    """Return all numeric-named subfolders inside data/ (patient ID folders)."""
    folders = []
    for name in os.listdir(DATA_DIR):
        full = os.path.join(DATA_DIR, name)
        if os.path.isdir(full) and name.isdigit():
            folders.append(full)
    return sorted(folders)


def _copy_patient_images(max_per_class):
    """
    Walk every data/<patient_id>/0/ and data/<patient_id>/1/ folder
    and copy PNGs into merged_dataset/0/ and merged_dataset/1/.
    """
    benign_files    = []
    malignant_files = []

    for folder in _find_patient_folders():
        b = glob.glob(os.path.join(folder, '0', '*.png'))
        m = glob.glob(os.path.join(folder, '1', '*.png'))
        benign_files.extend(b)
        malignant_files.extend(m)

    print(f"  Patient folders found : {len(_find_patient_folders())}")
    print(f"  Total patches found   : {len(benign_files):,} benign, "
          f"{len(malignant_files):,} malignant")

    # Shuffle so we get a mix of patients when capping
    rng = np.random.RandomState(42)
    rng.shuffle(benign_files)
    rng.shuffle(malignant_files)

    benign_files    = benign_files[:max_per_class]
    malignant_files = malignant_files[:max_per_class]

    print(f"  Using                 : {len(benign_files):,} benign, "
          f"{len(malignant_files):,} malignant  (max={max_per_class:,})")

    for i, src in enumerate(benign_files):
        dst = os.path.join(OUT_DIR, '0', f'patch_b_{i:06d}.png')
        img = cv2.imread(src)
        if img is not None:
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            cv2.imwrite(dst, img)
        if (i + 1) % 1000 == 0:
            print(f"    Copied {i+1:,}/{len(benign_files):,} benign patches…")

    for i, src in enumerate(malignant_files):
        dst = os.path.join(OUT_DIR, '1', f'patch_m_{i:06d}.png')
        img = cv2.imread(src)
        if img is not None:
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            cv2.imwrite(dst, img)
        if (i + 1) % 1000 == 0:
            print(f"    Copied {i+1:,}/{len(malignant_files):,} malignant patches…")

    return len(benign_files), len(malignant_files)


def _csv_row_to_image(feature_values):
    """Convert a 30-element feature vector to a 50x50 colour heatmap image."""
    vals  = np.array(feature_values, dtype=np.float32)
    v_min, v_max = vals.min(), vals.max()
    normed = np.zeros_like(vals) if (v_max - v_min) < 1e-9 else (vals - v_min) / (v_max - v_min)
    grid   = normed.reshape(5, 6)
    canvas = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32)
    th, tw = IMG_SIZE // 5, IMG_SIZE // 6
    for r in range(5):
        for c in range(6):
            canvas[r*th:(r+1)*th, c*tw:(c+1)*tw] = grid[r, c]
    gray = (canvas * 255).astype(np.uint8)
    bgr  = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
    return cv2.resize(bgr, (IMG_SIZE, IMG_SIZE))


def _generate_csv_images():
    """Render each Wisconsin CSV row as a heatmap image."""
    try:
        import pandas as pd
    except ImportError:
        print("  [WARN] pandas not available — skipping CSV images.")
        return 0, 0

    if not os.path.exists(CSV_PATH):
        print(f"  [WARN] CSV not found at {CSV_PATH} — skipping.")
        return 0, 0

    df = pd.read_csv(CSV_PATH)
    df['_label'] = df['diagnosis'].map({'M': 1, 'B': 0, 1: 1, 0: 0})
    df = df.dropna(subset=['_label'])
    df['_label'] = df['_label'].astype(int)

    feat_cols = [f for f in FEATURES if f in df.columns]
    print(f"  CSV rows   : {len(df)} | features: {len(feat_cols)}/30")

    b_count = m_count = 0
    for idx, row in df.iterrows():
        vals  = [float(row[f]) if f in feat_cols else 0.0 for f in FEATURES]
        img   = _csv_row_to_image(vals)
        label = int(row['_label'])
        cv2.imwrite(os.path.join(OUT_DIR, str(label), f'csv_{idx:06d}.png'), img)
        if label == 0: b_count += 1
        else:          m_count += 1

    print(f"  CSV images : {b_count} benign, {m_count} malignant")
    return b_count, m_count


def _generate_unrelated_images(count):
    """
    Generate synthetic non-tissue images for class 2.
    Covers: solid colours, random noise, white docs, gradients,
    dark images, overexposed, geometric shapes, checkerboards.
    """
    rng = np.random.RandomState(99)
    images = []
    per_type = max(1, count // 8)

    # 1. Solid colour blocks
    for _ in range(per_type):
        colour = rng.randint(0, 256, 3, dtype=np.uint8)
        images.append(np.full((IMG_SIZE, IMG_SIZE, 3), colour, dtype=np.uint8))

    # 2. Random noise
    for _ in range(per_type):
        images.append(rng.randint(50, 200, (IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8))

    # 3. White/light background (documents)
    for _ in range(per_type):
        base = rng.randint(230, 256)
        img  = np.full((IMG_SIZE, IMG_SIZE, 3), base, dtype=np.uint8)
        for _ in range(rng.randint(2, 6)):
            y = rng.randint(5, IMG_SIZE - 5)
            img[y:y+2, 5:IMG_SIZE-5] = rng.randint(0, 60)
        images.append(img)

    # 4. Gradients
    for _ in range(per_type):
        c1 = rng.randint(0, 256, 3, dtype=np.uint8)
        c2 = rng.randint(0, 256, 3, dtype=np.uint8)
        xs  = np.linspace(0, 1, IMG_SIZE)
        img = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
        for ch in range(3):
            row = (c1[ch] * (1 - xs) + c2[ch] * xs).astype(np.uint8)
            img[:, :, ch] = np.tile(row, (IMG_SIZE, 1))
        images.append(img)

    # 5. Dark images
    for _ in range(per_type):
        images.append(np.full((IMG_SIZE, IMG_SIZE, 3), rng.randint(0, 40), dtype=np.uint8))

    # 6. Overexposed images
    for _ in range(per_type):
        images.append(np.full((IMG_SIZE, IMG_SIZE, 3), rng.randint(220, 256), dtype=np.uint8))

    # 7. Geometric shapes (icons / diagrams)
    for _ in range(per_type):
        img = np.full((IMG_SIZE, IMG_SIZE, 3), 240, dtype=np.uint8)
        col = (int(rng.randint(0, 120)), int(rng.randint(0, 120)), int(rng.randint(150, 256)))
        cv2.circle(img, (IMG_SIZE//2, IMG_SIZE//2), IMG_SIZE//3, col, -1)
        images.append(img)

    # 8. Checkerboards
    for _ in range(per_type):
        img  = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
        tile = rng.randint(4, 12)
        for ry in range(0, IMG_SIZE, tile):
            for rx in range(0, IMG_SIZE, tile):
                val = 230 if ((ry//tile + rx//tile) % 2 == 0) else 20
                img[ry:ry+tile, rx:rx+tile] = val
        images.append(img)

    rng.shuffle(images)
    return images[:count]


# ── main ──────────────────────────────────────────────────────────────────────

def prepare(max_per_class=10000, include_csv=True):
    # Create output dirs
    for cls in ['0', '1', '2']:
        os.makedirs(os.path.join(OUT_DIR, cls), exist_ok=True)

    print("=" * 62)
    print("  BreastCare AI — Dataset Merge (3-class)")
    print("=" * 62)
    print(f"Output: {OUT_DIR}\n")

    # ── Source 1: Real patient image patches ─────────────────────
    print("[1/3] Copying real patient image patches…")
    patch_b, patch_m = _copy_patient_images(max_per_class)

    # ── Source 2: Wisconsin CSV heatmaps ─────────────────────────
    if include_csv:
        print("\n[2/3] Generating Wisconsin CSV heatmap images…")
        csv_b, csv_m = _generate_csv_images()
    else:
        print("\n[2/3] CSV merging skipped.")
        csv_b = csv_m = 0

    # ── Source 3: Synthetic unrelated images ─────────────────────
    tissue_total  = (patch_b + csv_b + patch_m + csv_m)
    unrel_count   = max(tissue_total, 500)
    print(f"\n[3/3] Generating {unrel_count:,} synthetic unrelated images…")
    unrel_imgs = _generate_unrelated_images(unrel_count)
    for i, img in enumerate(unrel_imgs):
        cv2.imwrite(os.path.join(OUT_DIR, '2', f'unrelated_{i:06d}.png'), img)
    print(f"  Generated : {len(unrel_imgs):,} unrelated images")

    # ── Summary ──────────────────────────────────────────────────
    total_0 = len(os.listdir(os.path.join(OUT_DIR, '0')))
    total_1 = len(os.listdir(os.path.join(OUT_DIR, '1')))
    total_2 = len(os.listdir(os.path.join(OUT_DIR, '2')))

    print("\n" + "=" * 62)
    print("  Merge complete!")
    print(f"  Benign    (class 0) : {total_0:,} images")
    print(f"  Malignant (class 1) : {total_1:,} images")
    print(f"  Unrelated (class 2) : {total_2:,} images")
    print(f"  Total               : {total_0 + total_1 + total_2:,} images")
    print(f"\n  Breakdown:")
    print(f"    Real patches      : {patch_b:,} benign + {patch_m:,} malignant")
    print(f"    CSV heatmaps      : {csv_b:,} benign + {csv_m:,} malignant")
    print(f"    Synthetic unrel.  : {len(unrel_imgs):,}")
    print("=" * 62)
    print("\nNext: python ml/train_cnn.py")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Merge real image patches + CSV heatmaps + synthetic unrelated images.')
    parser.add_argument('--max', type=int, default=10000,
                        help='Max real patches per class (default: 10000).')
    parser.add_argument('--no-csv', dest='csv', action='store_false', default=True,
                        help='Skip Wisconsin CSV heatmap generation.')
    args = parser.parse_args()
    prepare(max_per_class=args.max, include_csv=args.csv)
