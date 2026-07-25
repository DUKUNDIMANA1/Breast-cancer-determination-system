"""
Extract archive.zip into data/idc_extracted/
==========================================
Extracts all IDC histopathology patches from archive.zip into:
  data/idc_extracted/0/  — Benign patches  (class 0)
  data/idc_extracted/1/  — Malignant patches (class 1)

Run once before training. After extraction, train with:
  python ml/train_from_zip.py --max 30000
  (train_from_zip.py will use the extracted folder if zip extraction already done)

Usage:
  python ml/extract_archive.py
  python ml/extract_archive.py --out data/idc_extracted   # custom output dir
"""

import os, sys, zipfile, argparse
import numpy as np
import cv2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, 'data', 'archive.zip')

parser = argparse.ArgumentParser()
parser.add_argument('--out', default=os.path.join(BASE_DIR, 'data', 'idc_extracted'),
                    help='Output directory (default: data/idc_extracted)')
parser.add_argument('--size', type=int, default=50,
                    help='Resize images to NxN pixels (default: 50)')
args = parser.parse_args()

OUT_DIR  = args.out
IMG_SIZE = args.size

os.makedirs(os.path.join(OUT_DIR, '0'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, '1'), exist_ok=True)

print("=" * 60)
print("  BreastCare AI — Extract archive.zip")
print("=" * 60)
print(f"  ZIP    : {ZIP_PATH}")
print(f"  Output : {OUT_DIR}")
print(f"  Size   : {IMG_SIZE}x{IMG_SIZE}")
print()

if not os.path.exists(ZIP_PATH):
    print(f"ERROR: {ZIP_PATH} not found."); sys.exit(1)

# Scan zip
print("Scanning zip contents …")
benign_names    = []
malignant_names = []

with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    all_names = zf.namelist()
    for name in all_names:
        if not (name.endswith('.png') or name.endswith('.jpg')):
            continue
        parts = name.replace('\\', '/').split('/')
        if len(parts) < 3:
            continue
        cls_dir = parts[-2]
        if cls_dir == '0':
            benign_names.append(name)
        elif cls_dir == '1':
            malignant_names.append(name)

print(f"Found: {len(benign_names):,} benign,  {len(malignant_names):,} malignant")
print(f"Total: {len(benign_names)+len(malignant_names):,} images\n")

# Check what's already extracted
existing_b = len(os.listdir(os.path.join(OUT_DIR, '0')))
existing_m = len(os.listdir(os.path.join(OUT_DIR, '1')))
if existing_b > 0 or existing_m > 0:
    print(f"Already extracted: {existing_b:,} benign, {existing_m:,} malignant")
    print("Skipping already-extracted files and continuing from where we left off …\n")

# Build sets of already-extracted filenames to skip
done_b = set(os.listdir(os.path.join(OUT_DIR, '0')))
done_m = set(os.listdir(os.path.join(OUT_DIR, '1')))

# Extract
b_written = existing_b
m_written = existing_m

print("Extracting …")
with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    for i, name in enumerate(benign_names):
        out_fname = f'b_{i:07d}.png'
        if out_fname in done_b:
            continue
        try:
            data = zf.read(name)
            arr  = np.frombuffer(data, np.uint8)
            img  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None:
                img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                cv2.imwrite(os.path.join(OUT_DIR, '0', out_fname), img)
                b_written += 1
        except Exception:
            pass
        if b_written % 10000 == 0 and b_written > existing_b:
            print(f"  Benign    {b_written:,}/{len(benign_names):,}")

    for i, name in enumerate(malignant_names):
        out_fname = f'm_{i:07d}.png'
        if out_fname in done_m:
            continue
        try:
            data = zf.read(name)
            arr  = np.frombuffer(data, np.uint8)
            img  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None:
                img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                cv2.imwrite(os.path.join(OUT_DIR, '1', out_fname), img)
                m_written += 1
        except Exception:
            pass
        if m_written % 10000 == 0 and m_written > existing_m:
            print(f"  Malignant {m_written:,}/{len(malignant_names):,}")

final_b = len(os.listdir(os.path.join(OUT_DIR, '0')))
final_m = len(os.listdir(os.path.join(OUT_DIR, '1')))

print()
print("=" * 60)
print(f"  Extraction complete!")
print(f"  Benign    (0): {final_b:,}")
print(f"  Malignant (1): {final_m:,}")
print(f"  Total        : {final_b + final_m:,}")
print(f"  Output       : {OUT_DIR}")
print("=" * 60)
print()
print("Next step — train the CNN:")
print("  python ml/train_from_zip.py --max 30000")
print("  (or --max 0 to use all extracted images, balanced)")
