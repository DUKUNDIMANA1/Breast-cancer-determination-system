"""
IDC Binary CNN — Breast Cancer Classifier
==========================================
Trains MobileNetV2 on the merged IDC dataset:
  data/merged_dataset/0/  — Benign patches  (4587 images)
  data/merged_dataset/1/  — Malignant patches (834 images)

Binary sigmoid output: 0 = Benign, 1 = Malignant

Usage:
  python ml/train_idc_cnn.py
"""

import os, sys, json
import numpy as np

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data', 'merged_dataset')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

# Only train on class 0 (Benign) and class 1 (Malignant) — skip class 2
BINARY_DIR = os.path.join(BASE_DIR, 'data', 'idc_binary')

IMG_SIZE   = 50
BATCH_SIZE = 32
SEED       = 42

os.makedirs(ARTIFACTS, exist_ok=True)

# ── Build binary dataset folder (symlink class 0 and 1 only) ─────────────────
import shutil
print("[IDC-CNN] Preparing binary dataset (Benign + Malignant only)...")

if os.path.exists(BINARY_DIR):
    shutil.rmtree(BINARY_DIR)
os.makedirs(os.path.join(BINARY_DIR, '0'), exist_ok=True)
os.makedirs(os.path.join(BINARY_DIR, '1'), exist_ok=True)

counts = {0: 0, 1: 0}
for cls in ['0', '1']:
    src_dir = os.path.join(DATA_DIR, cls)
    dst_dir = os.path.join(BINARY_DIR, cls)
    for fname in os.listdir(src_dir):
        src = os.path.join(src_dir, fname)
        dst = os.path.join(dst_dir, fname)
        os.symlink(os.path.abspath(src), dst)
        counts[int(cls)] += 1

print(f"  Benign    (0): {counts[0]:,}")
print(f"  Malignant (1): {counts[1]:,}")
print(f"  Total:         {sum(counts.values()):,}")

# ── Data pipeline ─────────────────────────────────────────────────────────────
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import sklearn.metrics as skm
from sklearn.utils.class_weight import compute_class_weight

print("\n[IDC-CNN] Building data generators...")

datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=180,
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.1,
    width_shift_range=0.1,
    height_shift_range=0.1,
    brightness_range=[0.85, 1.15],
    fill_mode='reflect',
    validation_split=0.2
)

train_gen = datagen.flow_from_directory(
    BINARY_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='training',
    seed=SEED,
    classes=['0', '1']
)

val_gen = datagen.flow_from_directory(
    BINARY_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    seed=SEED,
    classes=['0', '1']
)

print(f"Train: {train_gen.samples:,}  Val: {val_gen.samples:,}")

# Class weights
cws = compute_class_weight('balanced',
                           classes=np.unique(train_gen.classes),
                           y=train_gen.classes)
class_weight = dict(enumerate(cws))
print(f"Class weights: {class_weight}")

# ── Model ─────────────────────────────────────────────────────────────────────
print("\n[IDC-CNN] Building model...")

base = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                   include_top=False, weights='imagenet')
base.trainable = False

model = keras.Sequential([
    base,
    layers.GlobalAveragePooling2D(),
    layers.BatchNormalization(),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer=keras.optimizers.Adam(1e-3),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)
model.summary()

cbs = [
    keras.callbacks.EarlyStopping(
        patience=4, restore_best_weights=True,
        monitor='val_auc', mode='max'),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.3, patience=2,
        monitor='val_auc', mode='max', min_lr=1e-7),
    keras.callbacks.ModelCheckpoint(
        MODEL_PATH, save_best_only=True,
        monitor='val_auc', mode='max'),
]

# ── Phase 1: Train head only ──────────────────────────────────────────────────
print("\n[IDC-CNN] Phase 1: Training head (base frozen)...")
h1 = model.fit(
    train_gen, validation_data=val_gen,
    epochs=20, callbacks=cbs,
    class_weight=class_weight
)

best_auc_p1 = max(h1.history['val_auc'])
print(f"\n[IDC-CNN] Phase 1 best val_auc: {best_auc_p1:.4f}")

# ── Phase 2: Fine-tune ONLY if phase 1 gave good AUC (>0.80) ────────────────
# SKIP fine-tuning — phase 1 head training is sufficient for this dataset size
# Fine-tuning on 50x50 patches with MobileNetV2 tends to overfit
print(f"\n[IDC-CNN] Phase 1 complete. Best val_auc: {best_auc_p1:.4f}")
print("[IDC-CNN] Skipping fine-tuning (not needed for 50px patches).")

# ── Evaluate ──────────────────────────────────────────────────────────────────
# Load the best checkpoint saved during training (not the final epoch state)
print("\n[IDC-CNN] Loading best checkpoint for evaluation...")
best_model = tf.keras.models.load_model(MODEL_PATH)

print("[IDC-CNN] Final evaluation...")
val_gen.reset()
y_prob = best_model.predict(val_gen, verbose=1).flatten()
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

# ── Save ──────────────────────────────────────────────────────────────────────
metrics = {
    'model_type':    'CNN (MobileNetV2 Binary, IDC)',
    'dataset':       'data/merged_dataset/0 + /1 (IDC patches)',
    'model_output':  'sigmoid — p<0.5=Benign, p>=0.5=Malignant',
    'threshold':     0.5,
    'accuracy':      round(acc * 100, 2),
    'auc':           round(auc * 100, 2),
    'img_size':      IMG_SIZE,
    'train_samples': int(train_gen.samples),
    'val_samples':   int(val_gen.samples),
    'classes':       {'0': 'Benign (IDC-negative)', '1': 'Malignant (IDC-positive)'},
    'per_class': {
        'Benign':    {k: round(v*100,2) for k,v in report['Benign'].items() if k!='support'},
        'Malignant': {k: round(v*100,2) for k,v in report['Malignant'].items() if k!='support'},
    },
    'confusion_matrix': cm,
}

with open(METRICS_PATH, 'w') as mf:
    json.dump(metrics, mf, indent=2)

# Best model already saved by ModelCheckpoint callback — no need to re-save
print(f"\n[IDC-CNN] Model saved  → {MODEL_PATH}")
print(f"[IDC-CNN] Metrics      → {METRICS_PATH}")
print(f"[IDC-CNN] Accuracy: {acc*100:.2f}%  AUC: {auc*100:.2f}%")

# Cleanup
shutil.rmtree(BINARY_DIR, ignore_errors=True)
print("[IDC-CNN] Done.")
