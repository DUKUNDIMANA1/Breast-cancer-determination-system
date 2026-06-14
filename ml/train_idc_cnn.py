"""
IDC Binary CNN — Breast Cancer Classifier
==========================================
Trains MobileNetV2 on the real IDC histopathology patches:
  data/8863/, data/8864/, data/8865/, data/8867/, data/8913/
  Each patient folder has subfolders:
    0/ = Benign (non-IDC) patches
    1/ = Malignant (IDC-positive) patches

Output:
  artifacts/cnn_model.h5      — binary model (sigmoid, 0=Benign 1=Malignant)
  artifacts/cnn_metrics.json  — accuracy, AUC, per-class metrics

Usage:
  python ml/train_idc_cnn.py
"""

import os, sys, json, shutil, tempfile
import numpy as np

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

# IDC patient folders
IDC_PATIENTS = ['8863', '8864', '8865', '8867', '8913']
DATA_ROOT    = os.path.join(BASE_DIR, 'data')

IMG_SIZE   = 50
BATCH_SIZE = 32
SEED       = 42

os.makedirs(ARTIFACTS, exist_ok=True)

# ── Step 1: Build a flat training directory ───────────────────────────────────
# Keras ImageDataGenerator needs a flat folder with class subfolders.
# We collect all IDC patches from the 5 patient folders.

print("[IDC-CNN] Collecting IDC patches from all patient folders...")
tmpdir = tempfile.mkdtemp(prefix='idc_train_')
os.makedirs(os.path.join(tmpdir, '0'), exist_ok=True)
os.makedirs(os.path.join(tmpdir, '1'), exist_ok=True)

counts = {0: 0, 1: 0}
for patient in IDC_PATIENTS:
    for cls in ['0', '1']:
        src_dir = os.path.join(DATA_ROOT, patient, cls)
        if not os.path.exists(src_dir):
            continue
        files = [f for f in os.listdir(src_dir) if f.lower().endswith('.png')]
        for fname in files:
            # Use symlink if supported, else copy
            src  = os.path.join(src_dir, fname)
            dst  = os.path.join(tmpdir, cls, f"{patient}_{fname}")
            try:
                os.symlink(src, dst)
            except (OSError, NotImplementedError):
                shutil.copy2(src, dst)
            counts[int(cls)] += 1

print(f"  Benign (0):    {counts[0]:,} patches")
print(f"  Malignant (1): {counts[1]:,} patches")
print(f"  Total:         {counts[0]+counts[1]:,} patches")
print(f"  Temp dir:      {tmpdir}")

# ── Step 2: Data generators ───────────────────────────────────────────────────
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import sklearn.metrics as skm
from sklearn.utils.class_weight import compute_class_weight

print("\n[IDC-CNN] Setting up data pipeline...")

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=180,        # H&E slides can be any orientation
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.15,
    shear_range=0.1,
    brightness_range=[0.85, 1.15],
    fill_mode='reflect',
    validation_split=0.2
)

train_gen = train_datagen.flow_from_directory(
    tmpdir,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',        # sigmoid output: 0=Benign, 1=Malignant
    subset='training',
    seed=SEED,
    classes=['0', '1']
)

val_gen = train_datagen.flow_from_directory(
    tmpdir,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    seed=SEED,
    classes=['0', '1']
)

print(f"[IDC-CNN] Train: {train_gen.samples:,}  Val: {val_gen.samples:,}")

# Class weights — malignant is rare so upweight it
all_labels = train_gen.classes
cws = compute_class_weight('balanced', classes=np.unique(all_labels), y=all_labels)
class_weight = dict(enumerate(cws))
print(f"[IDC-CNN] Class weights: { {k: round(v,2) for k,v in class_weight.items()} }")

# ── Step 3: Build model ───────────────────────────────────────────────────────
print("\n[IDC-CNN] Building MobileNetV2 binary classifier...")

base = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights='imagenet')
base.trainable = False

model = keras.Sequential([
    base,
    layers.GlobalAveragePooling2D(),
    layers.BatchNormalization(),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.4),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')   # binary: 0=Benign, 1=Malignant
])

model.compile(
    optimizer=keras.optimizers.Adam(1e-3),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)

model.summary()

callbacks_p1 = [
    keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True, monitor='val_auc', mode='max'),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=2, monitor='val_auc', mode='max'),
    keras.callbacks.ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_auc', mode='max'),
]

# ── Phase 1: Train top layers ─────────────────────────────────────────────────
print("\n[IDC-CNN] Phase 1: Training top layers (base frozen)...")
h1 = model.fit(
    train_gen, validation_data=val_gen,
    epochs=15,
    callbacks=callbacks_p1,
    class_weight=class_weight
)

# ── Phase 2: Fine-tune last 40 layers of MobileNetV2 ─────────────────────────
print("\n[IDC-CNN] Phase 2: Fine-tuning last 40 layers...")
base.trainable = True
for layer in base.layers[:-40]:
    layer.trainable = False

model.compile(
    optimizer=keras.optimizers.Adam(5e-6),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)

callbacks_p2 = [
    keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True, monitor='val_auc', mode='max'),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=2, monitor='val_auc', mode='max'),
    keras.callbacks.ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_auc', mode='max'),
]

h2 = model.fit(
    train_gen, validation_data=val_gen,
    epochs=10,
    callbacks=callbacks_p2,
    class_weight=class_weight
)

# ── Evaluate ──────────────────────────────────────────────────────────────────
print("\n[IDC-CNN] Evaluating on validation set...")
val_gen.reset()
y_prob = model.predict(val_gen, verbose=1).flatten()
y_pred = (y_prob >= 0.5).astype(int)
y_true = val_gen.classes[:len(y_pred)]

report = skm.classification_report(
    y_true, y_pred,
    target_names=['Benign', 'Malignant'],
    output_dict=True
)
auc = skm.roc_auc_score(y_true, y_prob)
acc = report['accuracy']
cm  = skm.confusion_matrix(y_true, y_pred).tolist()

print(skm.classification_report(y_true, y_pred, target_names=['Benign','Malignant']))
print(f"AUC: {auc:.4f}")

# ── Save metrics ──────────────────────────────────────────────────────────────
metrics = {
    'model_type':    'CNN (MobileNetV2 Binary, IDC dataset)',
    'dataset':       f'IDC histopathology patches: {"+".join(IDC_PATIENTS)}',
    'model_output':  'sigmoid — 0=Benign, 1=Malignant',
    'threshold':     0.5,
    'accuracy':      round(acc * 100, 2),
    'auc':           round(auc * 100, 2),
    'img_size':      IMG_SIZE,
    'train_samples': train_gen.samples,
    'val_samples':   val_gen.samples,
    'classes':       {'0': 'Benign / IDC-negative', '1': 'Malignant / IDC-positive'},
    'per_class': {
        'Benign':    {k: round(v*100,2) for k,v in report['Benign'].items() if k != 'support'},
        'Malignant': {k: round(v*100,2) for k,v in report['Malignant'].items() if k != 'support'},
    },
    'confusion_matrix': cm,
    'notes': (
        f"Trained on {counts[0]+counts[1]} real IDC patches. "
        f"Binary sigmoid output — thresholded at 0.5. "
        f"High malignant recall prioritized (cancer screening)."
    )
}

with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)

model.save(MODEL_PATH)
print(f"\n[IDC-CNN] ✓ Model saved  → {MODEL_PATH}")
print(f"[IDC-CNN] ✓ Metrics saved → {METRICS_PATH}")
print(f"[IDC-CNN]   Accuracy: {acc*100:.2f}%   AUC: {auc*100:.2f}%")

# Cleanup temp dir
shutil.rmtree(tmpdir, ignore_errors=True)
print("[IDC-CNN] Temp files cleaned up.")
