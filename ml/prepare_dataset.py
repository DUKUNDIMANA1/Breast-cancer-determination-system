"""
Prepare IDC Breast Cancer Dataset for CNN training.

After downloading from Kaggle, the structure is:
  IDC_regular_ps50_idx5/
    ├── 8863/          ← patient ID
    │   ├── 0/         ← benign patches
    │   │   └── *.png
    │   └── 1/         ← malignant patches
    │       └── *.png
    └── ...

This script flattens it into:
  data/breast_histopathology/
    ├── 0/   ← all benign
    └── 1/   ← all malignant

Usage:
  python ml/prepare_dataset.py --source "C:/path/to/extracted/IDC_regular_ps50_idx5"
"""

import os, sys, shutil, glob, argparse

def prepare(source_dir, max_per_class=15000):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir  = os.path.join(BASE_DIR, 'data', 'breast_histopathology')
    os.makedirs(os.path.join(out_dir, '0'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, '1'), exist_ok=True)

    print(f"Source: {source_dir}")
    print(f"Output: {out_dir}")

    benign_files    = glob.glob(os.path.join(source_dir, '**', '0', '*.png'), recursive=True)
    malignant_files = glob.glob(os.path.join(source_dir, '**', '1', '*.png'), recursive=True)

    print(f"Found: {len(benign_files):,} benign,  {len(malignant_files):,} malignant")

    # Limit to max_per_class for manageable training size
    benign_files    = benign_files[:max_per_class]
    malignant_files = malignant_files[:max_per_class]

    print(f"Using: {len(benign_files):,} benign,  {len(malignant_files):,} malignant")
    print("Copying files...")

    for i, f in enumerate(benign_files):
        dst = os.path.join(out_dir, '0', f'b_{i:06d}.png')
        shutil.copy2(f, dst)
        if (i+1) % 1000 == 0: print(f"  Benign: {i+1:,}/{len(benign_files):,}")

    for i, f in enumerate(malignant_files):
        dst = os.path.join(out_dir, '1', f'm_{i:06d}.png')
        shutil.copy2(f, dst)
        if (i+1) % 1000 == 0: print(f"  Malignant: {i+1:,}/{len(malignant_files):,}")

    print(f"\nDone! Dataset ready at: {out_dir}")
    print(f"  Benign (0):    {len(os.listdir(os.path.join(out_dir,'0'))):,}")
    print(f"  Malignant (1): {len(os.listdir(os.path.join(out_dir,'1'))):,}")
    print("\nNext step: python ml/train_cnn.py")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True,
                        help='Path to extracted IDC dataset folder')
    parser.add_argument('--max', type=int, default=15000,
                        help='Max images per class (default: 15000)')
    args = parser.parse_args()

    if not os.path.exists(args.source):
        print(f"ERROR: Source folder not found: {args.source}")
        sys.exit(1)

    prepare(args.source, args.max)
