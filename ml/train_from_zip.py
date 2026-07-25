"""
Train CNN from idc_extracted (or archive.zip fallback) — BreastCare AI
========================================================================
Full pipeline: source images → build merged_dataset → train → save

Steps:
  1. Source from data/idc_extracted/ if available (pre-extracted by extract_archive.py)
     OR fall back to extracting directly from data/archive.zip
  2. Generate synthetic unrelated images (class 2)
  3. Train 3-class MobileNetV2 on the merged dataset
  4. Save best model to artifacts/cnn_model.h5
  5. Save metrics to artifacts/cnn_metrics.json

Usage:
  python ml/train_from_zip.py                  # default: 30000 per class
  python ml/train_from_zip.py --max 50000      # larger run
  python ml/train_from_zip.py --max 0          # use ALL images (balanced)
"""

import os, sys, json, zipfile, argparse, warnings, shutil, glob
warnings.filterwarnings('ignore')
import numpy as np
import cv2

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH        = os.path.join(BASE_DIR, 'data', 'archive.zip')
IDC_EXTRACTED   = os.path.join(BASE_DIR, 'data', 'idc_extracted')   # pre-extracted folder
DATASET_DIR     = os.path.join(BASE_DIR, 'data', 'merged_dataset')
ARTIFACTS       = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH      = os.path.join(ARTIFACTS, 'cnn_model.h5')
BEST_CKPT       = os.path.join(ARTIFACTS, 'cnn_best.keras')
METRICS_PATH    = os.path.join(ARTIFACTS, 'cnn_metrics.json')

IMG_SIZE   = 50
BATCH_SIZE = 64
SEED       = 42

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--max', type=int, default=30000,
                    help='Max patches per class (0 = all balanced). Default: 30000')
args, _ = parser.parse_known_args()
MAX_PER_CLASS = args.max if args.max > 0 else 999_999_999

print("=" * 64)
print("  BreastCare AI — Train CNN")
print("=" * 64)
print(f"  Dataset   : {DATASET_DIR}")
print(f"  Max/class : {'ALL (balanced to minority class)' if args.max == 0 else f'{MAX_PER_CLASS:,}'}")
print(f"  IMG size  : {IMG_SIZE}x{IMG_SIZE}")
print()

# ── Step 1: Build merged_dataset from idc_extracted or archive.zip ───────────
print("[1/4] Preparing dataset …")

# Clear old merged_dataset
if os.path.exists(DATASET_DIR):
    print(f"  Removing old merged_dataset …")
    import subprocess
    try:
        subprocess.run(['cmd', '/c', f'rmdir /s /q "{DATASET_DIR}"'],
                       check=True, capture_output=True)
    except Exception:
        for root, dirs, files in os.walk(DATASET_DIR, topdown=False):
            for fname in files:
                try: os.remove(os.path.join(root, fname))
                except: pass
            for dname in dirs:
                try: os.rmdir(os.path.join(root, dname))
                except: pass
        try: os.rmdir(DATASET_DIR)
        except: pass

for cls in ['0', '1', '2']:
    os.makedirs(os.path.join(DATASET_DIR, cls), exist_ok=True)

# ── Check if idc_extracted is ready ──────────────────────────────────────────
idc_b_dir = os.path.join(IDC_EXTRACTED, '0')
idc_m_dir = os.path.join(IDC_EXTRACTED, '1')
idc_b_count = len(os.listdir(idc_b_dir)) if os.path.exists(idc_b_dir) else 0
idc_m_count = len(os.listdir(idc_m_dir)) if os.path.exists(idc_m_dir) else 0

if idc_b_count > 1000 and idc_m_count > 1000:
    # ── SOURCE: idc_extracted folder ─────────────────────────────────────────
    print(f"  Using idc_extracted: {idc_b_count:,} benign, {idc_m_count:,} malignant")

    rng = np.random.RandomState(SEED)

    if args.max == 0:
        minority = min(idc_b_count, idc_m_count)
        n_b = n_m = minority
        print(f"  Balancing to minority: {minority:,} per class")
    else:
        n_b = min(MAX_PER_CLASS, idc_b_count)
        n_m = min(MAX_PER_CLASS, idc_m_count)

    b_files = sorted(glob.glob(os.path.join(idc_b_dir, '*.png')))
    m_files = sorted(glob.glob(os.path.join(idc_m_dir, '*.png')))
    rng.shuffle(b_files); rng.shuffle(m_files)
    b_files = b_files[:n_b]
    m_files = m_files[:n_m]

    print(f"  Copying {len(b_files):,} benign + {len(m_files):,} malignant …")
    for i, src in enumerate(b_files):
        shutil.copy2(src, os.path.join(DATASET_DIR, '0', f'b_{i:07d}.png'))
        if (i+1) % 10000 == 0: print(f"    Benign {i+1:,}/{len(b_files):,}")
    for i, src in enumerate(m_files):
        shutil.copy2(src, os.path.join(DATASET_DIR, '1', f'm_{i:07d}.png'))
        if (i+1) % 10000 == 0: print(f"    Malignant {i+1:,}/{len(m_files):,}")

    b_written = len(b_files)
    m_written = len(m_files)
    source_label = f'idc_extracted — {b_written:,} benign + {m_written:,} malignant'

else:
    # ── Check patient folders in data/ ────────────────────────────────────────
    patient_b = sorted(glob.glob(os.path.join(BASE_DIR, 'data', '*', '0', '*.png')))
    patient_m = sorted(glob.glob(os.path.join(BASE_DIR, 'data', '*', '1', '*.png')))
    # Filter to only numeric patient dirs
    patient_b = [p for p in patient_b if os.path.basename(os.path.dirname(os.path.dirname(p))).isdigit()]
    patient_m = [p for p in patient_m if os.path.basename(os.path.dirname(os.path.dirname(p))).isdigit()]

    if len(patient_b) > 1000 and len(patient_m) > 1000:
        # ── SOURCE: patient folders already on disk ───────────────────────────
        print(f"  Using patient folders: {len(patient_b):,} benign, {len(patient_m):,} malignant")
        rng = np.random.RandomState(SEED)
        rng.shuffle(patient_b); rng.shuffle(patient_m)

        if args.max == 0:
            minority = min(len(patient_b), len(patient_m))
            patient_b = patient_b[:minority]
            patient_m = patient_m[:minority]
            print(f"  Balancing to minority: {minority:,} per class")
        else:
            patient_b = patient_b[:MAX_PER_CLASS]
            patient_m = patient_m[:MAX_PER_CLASS]

        print(f"  Copying {len(patient_b):,} benign + {len(patient_m):,} malignant …")
        for i, src in enumerate(patient_b):
            shutil.copy2(src, os.path.join(DATASET_DIR, '0', f'b_{i:07d}.png'))
            if (i+1) % 10000 == 0: print(f"    Benign {i+1:,}/{len(patient_b):,}")
        for i, src in enumerate(patient_m):
            shutil.copy2(src, os.path.join(DATASET_DIR, '1', f'm_{i:07d}.png'))
            if (i+1) % 10000 == 0: print(f"    Malignant {i+1:,}/{len(patient_m):,}")
        b_written = len(patient_b)
        m_written = len(patient_m)
        source_label = f'patient folders — {b_written:,} benign + {m_written:,} malignant'

    else:
        # ── SOURCE: archive.zip (fallback) ────────────────────────────────────
        print(f"  idc_extracted not ready ({idc_b_count:,} benign, {idc_m_count:,} malignant)")
        print(f"  Falling back to archive.zip …")

        if not os.path.exists(ZIP_PATH):
            print(f"ERROR: {ZIP_PATH} not found. Run ml/extract_archive.py first."); sys.exit(1)

        print("  Scanning zip …")
        benign_names = []; malignant_names = []
        with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
            for name in zf.namelist():
                if not (name.endswith('.png') or name.endswith('.jpg')): continue
                parts = name.replace('\\', '/').split('/')
                if len(parts) < 3: continue
                cls_dir = parts[-2]
                if cls_dir == '0': benign_names.append(name)
                elif cls_dir == '1': malignant_names.append(name)

        print(f"  Found: {len(benign_names):,} benign, {len(malignant_names):,} malignant")
        rng = np.random.RandomState(SEED)
        rng.shuffle(benign_names); rng.shuffle(malignant_names)

        if args.max == 0:
            minority = min(len(benign_names), len(malignant_names))
            benign_names = benign_names[:minority]
            malignant_names = malignant_names[:minority]
            print(f"  Balancing to minority: {minority:,} per class")
        else:
            benign_names    = benign_names[:MAX_PER_CLASS]
            malignant_names = malignant_names[:MAX_PER_CLASS]

        print(f"  Using: {len(benign_names):,} benign, {len(malignant_names):,} malignant")

        needed = set(benign_names) | set(malignant_names)
        b_idx = {n: i for i, n in enumerate(benign_names)}
        m_idx = {n: i for i, n in enumerate(malignant_names)}
        b_written = m_written = 0

        print("  Extracting patches …")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
            for name in zf.namelist():
                if name not in needed: continue
                try:
                    data = zf.read(name)
                    arr  = np.frombuffer(data, np.uint8)
                    img  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if img is None: continue
                    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                    if name in b_idx:
                        cv2.imwrite(os.path.join(DATASET_DIR, '0', f'b_{b_idx[name]:07d}.png'), img)
                        b_written += 1
                        if b_written % 10000 == 0: print(f"    Benign    {b_written:,}/{len(benign_names):,}")
                    elif name in m_idx:
                        cv2.imwrite(os.path.join(DATASET_DIR, '1', f'm_{m_idx[name]:07d}.png'), img)
                        m_written += 1
                        if m_written % 10000 == 0: print(f"    Malignant {m_written:,}/{len(malignant_names):,}")
                except Exception: pass

        source_label = f'archive.zip — {b_written:,} benign + {m_written:,} malignant'

print(f"  Written: {b_written:,} benign, {m_written:,} malignant")

# ── Step 2: Generate synthetic unrelated images (class 2) ─────────────────────
print("\n[2/4] Generating synthetic unrelated images (class 2) …")

# Cap at 5000 — enough to teach the CNN what "not tissue" looks like,
# and small enough that all writes reliably complete on Windows.
UNREL_TARGET = 5000
print(f"  Generating {UNREL_TARGET:,} unrelated images …")

rng2 = np.random.RandomState(99)
per_type = max(1, UNREL_TARGET // 8)
images = []

# 1. Solid colour blocks
for _ in range(per_type):
    c = rng2.randint(0, 256, 3, dtype=np.uint8)
    images.append(np.full((IMG_SIZE, IMG_SIZE, 3), c, dtype=np.uint8))

# 2. Random noise
for _ in range(per_type):
    images.append(rng2.randint(50, 200, (IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8))

# 3. White/document backgrounds
for _ in range(per_type):
    base = int(rng2.randint(230, 256))
    img  = np.full((IMG_SIZE, IMG_SIZE, 3), base, dtype=np.uint8)
    for _ in range(int(rng2.randint(2, 6))):
        y = int(rng2.randint(5, IMG_SIZE - 5))
        img[y:y+2, 5:IMG_SIZE-5] = int(rng2.randint(0, 60))
    images.append(img)

# 4. Gradients
for _ in range(per_type):
    c1 = rng2.randint(0, 256, 3, dtype=np.uint8)
    c2 = rng2.randint(0, 256, 3, dtype=np.uint8)
    xs  = np.linspace(0, 1, IMG_SIZE)
    img = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    for ch in range(3):
        row = (c1[ch] * (1 - xs) + c2[ch] * xs).astype(np.uint8)
        img[:, :, ch] = np.tile(row, (IMG_SIZE, 1))
    images.append(img)

# 5. Dark
for _ in range(per_type):
    images.append(np.full((IMG_SIZE, IMG_SIZE, 3), int(rng2.randint(0, 40)), dtype=np.uint8))

# 6. Overexposed
for _ in range(per_type):
    images.append(np.full((IMG_SIZE, IMG_SIZE, 3), int(rng2.randint(220, 256)), dtype=np.uint8))

# 7. Geometric shapes
for _ in range(per_type):
    img = np.full((IMG_SIZE, IMG_SIZE, 3), 240, dtype=np.uint8)
    colour = (int(rng2.randint(0,120)), int(rng2.randint(0,120)), int(rng2.randint(150,256)))
    cv2.circle(img, (IMG_SIZE//2, IMG_SIZE//2), IMG_SIZE//3, colour, -1)
    images.append(img)

# 8. Checkerboards
for _ in range(per_type):
    img  = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    tile = int(rng2.randint(4, 12))
    for ry in range(0, IMG_SIZE, tile):
        for rx in range(0, IMG_SIZE, tile):
            val = 230 if ((ry//tile + rx//tile) % 2 == 0) else 20
            img[ry:ry+tile, rx:rx+tile] = val
    images.append(img)

rng2.shuffle(images)
images = images[:UNREL_TARGET]

# Write and verify every file — retry once on failure
u2_dir = os.path.join(DATASET_DIR, '2')
written_unrel = 0
for i, img in enumerate(images):
    out_path = os.path.join(u2_dir, f'unrel_{i:07d}.png')
    ok = cv2.imwrite(out_path, img)
    if not ok:
        # retry
        ok = cv2.imwrite(out_path, img)
    if ok and os.path.exists(out_path):
        written_unrel += 1

print(f"  Written: {written_unrel:,}/{UNREL_TARGET:,} unrelated images")

# Verify all three class dirs — count only existing files
def count_valid_files(directory):
    """Count files that actually exist on disk."""
    if not os.path.exists(directory):
        return 0
    return sum(1 for f in os.listdir(directory)
               if os.path.isfile(os.path.join(directory, f)))

c0 = count_valid_files(os.path.join(DATASET_DIR, '0'))
c1 = count_valid_files(os.path.join(DATASET_DIR, '1'))
c2 = count_valid_files(os.path.join(DATASET_DIR, '2'))
total = c0 + c1 + c2
print(f"  Dataset ready: Benign={c0:,}  Malignant={c1:,}  Unrelated={c2:,}  Total={total:,}")

if c0 == 0 or c1 == 0 or c2 == 0:
    print("ERROR: One or more class directories is empty. Aborting."); sys.exit(1)

# ── Step 3: Train ─────────────────────────────────────────────────────────────
print("\n[3/4] Training CNN …")

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2

print(f"  TensorFlow {tf.__version__}")
os.makedirs(ARTIFACTS, exist_ok=True)

# Data generators with augmentation
# Enhanced augmentation to reduce overfitting and improve benign class discrimination
gen = keras.preprocessing.image.ImageDataGenerator(
    rescale=1./255,
    rotation_range=25,        # Increased from 20
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.15,          # Increased from 0.1
    width_shift_range=0.15,   # Increased from 0.1
    height_shift_range=0.15,  # Increased from 0.1
    brightness_range=[0.80, 1.20],  # Widened from [0.85, 1.15]
    shear_range=0.1,          # Added shear transformation
    channel_shift_range=0.1,  # Added channel shift for color variation
    validation_split=0.2,
)

train_gen = gen.flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    seed=SEED,
    classes=['0', '1', '2']
)

val_gen = gen.flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    seed=SEED,
    classes=['0', '1', '2']
)

print(f"  Train: {train_gen.samples:,}  Val: {val_gen.samples:,}")

# Class weights to handle imbalance
# INCREASED weight for benign (class 0) to reduce false positives (benign→malignant errors)
# This addresses the bias where 26.76% of benign images were misclassified as malignant
counts_dict = {'0': c0, '1': c1, '2': c2}
base_weights = {
    i: (total / (3 * counts_dict[str(i)])) if counts_dict[str(i)] > 0 else 1.0
    for i in range(3)
}
# Boost benign class weight by 2x to penalize false positives more heavily
class_weight = {
    0: base_weights[0] * 2.0,  # Benign - increased to reduce false positives
    1: base_weights[1],         # Malignant - keep as is
    2: base_weights[2]          # Unrelated - keep as is
}
print(f"  Class weights: { {k: round(v,3) for k,v in class_weight.items()} }")
print(f"  NOTE: Benign weight boosted by 2x to reduce false positives (benign→malignant errors)")

# Model: MobileNetV2 + custom head
base = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)
base.trainable = False

inp = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x   = base(inp, training=False)
x   = layers.GlobalAveragePooling2D()(x)
x   = layers.BatchNormalization()(x)
x   = layers.Dense(256, activation='relu')(x)
x   = layers.Dropout(0.4)(x)
x   = layers.Dense(128, activation='relu')(x)
x   = layers.Dropout(0.3)(x)
out = layers.Dense(3, activation='softmax')(x)

model = keras.Model(inp, out, name='BreastCare_CNN_3class')
model.compile(
    optimizer=keras.optimizers.Adam(1e-3),
    loss='categorical_crossentropy',
    metrics=['accuracy'],
)
model.summary()

callbacks = [
    keras.callbacks.EarlyStopping(
        patience=5,
        restore_best_weights=True,
        monitor='val_accuracy',
        mode='max'
    ),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.5,
        patience=2,
        monitor='val_loss',
        min_lr=1e-6
    ),
    # NOTE: ModelCheckpoint removed — Keras 3 cannot reload MobileNetV2 .keras
    # files due to BatchNorm renorm arg incompatibility. EarlyStopping with
    # restore_best_weights=True keeps the best weights in memory instead.
]

print("\n  Phase 1: Training head (base frozen) …")
history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=20,
    callbacks=callbacks,
    class_weight=class_weight,
)

best_val_acc = max(history.history['val_accuracy'])
print(f"\n  Best val_accuracy: {best_val_acc*100:.2f}%")

# Fine-tune top layers if phase 1 accuracy is good enough
if best_val_acc >= 0.80:   # lowered from 0.85 — fine-tune whenever head training converges
    print("\n  Phase 2: Fine-tuning top 30 layers of MobileNetV2 …")
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(1e-4),   # lower LR for fine-tuning
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )

    callbacks_ft = [
        keras.callbacks.EarlyStopping(
            patience=4,
            restore_best_weights=True,
            monitor='val_accuracy',
            mode='max'
        ),
        keras.callbacks.ReduceLROnPlateau(
            factor=0.3,
            patience=2,
            monitor='val_loss',
            min_lr=1e-7
        ),
        # No ModelCheckpoint — same reason as phase 1
    ]

    history2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=10,
        callbacks=callbacks_ft,
        class_weight=class_weight,
    )
    best_val_acc = max(best_val_acc, max(history2.history['val_accuracy']))
    print(f"  Best val_accuracy after fine-tune: {best_val_acc*100:.2f}%")
else:
    print(f"  Skipping fine-tune (val_acc={best_val_acc*100:.1f}% < 85%)")

# ── Step 4: Evaluate and save ─────────────────────────────────────────────────
print("\n[4/4] Evaluating and saving …")

from sklearn.metrics import classification_report, confusion_matrix

# Use in-memory model — EarlyStopping already restored best weights.
# Do NOT load from BEST_CKPT: Keras 3 cannot deserialise MobileNetV2's
# BatchNorm layers that contain legacy 'renorm' config keys.
best = model
if os.path.exists(BEST_CKPT):
    os.remove(BEST_CKPT)   # clean up any leftover checkpoint

eval_gen = keras.preprocessing.image.ImageDataGenerator(rescale=1./255).flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False,
    classes=['0', '1', '2']
)

y_prob = best.predict(eval_gen, verbose=1)
y_pred = np.argmax(y_prob, axis=1)
y_true = eval_gen.classes[:len(y_pred)]

report = classification_report(
    y_true, y_pred,
    target_names=['Benign', 'Malignant', 'Unrelated'],
    output_dict=True
)
acc = report['accuracy']
cm  = confusion_matrix(y_true, y_pred)

print(classification_report(y_true, y_pred, target_names=['Benign', 'Malignant', 'Unrelated']))
print(f"Overall accuracy: {acc*100:.2f}%")

# Save model
best.save(MODEL_PATH)
print(f"  Model saved → {MODEL_PATH}")

# Save metrics
metrics = {
    'model_type':    'CNN (MobileNetV2 3-class, IDC dataset)',
    'dataset':       source_label + f' + {c2:,} unrelated',
    'accuracy':      round(acc * 100, 2),
    'img_size':      IMG_SIZE,
    'train_samples': int(train_gen.samples),
    'val_samples':   int(val_gen.samples),
    'classes':       {'0': 'Benign', '1': 'Malignant', '2': 'Unrelated'},
    'per_class': {
        'Benign':    {k: round(v*100, 2) for k,v in report['Benign'].items()    if k != 'support'},
        'Malignant': {k: round(v*100, 2) for k,v in report['Malignant'].items() if k != 'support'},
        'Unrelated': {k: round(v*100, 2) for k,v in report['Unrelated'].items() if k != 'support'},
    },
    'confusion_matrix': cm.tolist(),
}

with open(METRICS_PATH, 'w') as mf:
    json.dump(metrics, mf, indent=2)
print(f"  Metrics saved → {METRICS_PATH}")

# Cleanup any leftover checkpoint file
if os.path.exists(BEST_CKPT):
    os.remove(BEST_CKPT)

print()
print("=" * 64)
print(f"  DONE  —  Accuracy: {acc*100:.2f}%")
print(f"  Model : {MODEL_PATH}")
print("=" * 64)
