"""
CNN Training Script — Breast Cancer Image Classification
Uses Transfer Learning with MobileNetV2 on the IDC Breast Cancer dataset from Kaggle.

Dataset: https://www.kaggle.com/datasets/paultimothymooney/breast-histopathology-images
- 0 = Benign (non-IDC)
- 1 = Malignant (IDC positive)

Usage:
  1. Download dataset from Kaggle and extract to data/breast_histopathology/
  2. Run: python ml/train_cnn.py
  3. Model saved to artifacts/cnn_model.h5
"""

import os, sys, json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, roc_auc_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data', 'breast_histopathology')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

IMG_SIZE   = 50      # IDC images are 50x50
BATCH_SIZE = 64
EPOCHS     = 15
SEED       = 42

os.makedirs(ARTIFACTS, exist_ok=True)

# ── Verify dataset ─────────────────────────────────────────────────────────────
print("[CNN] Checking dataset...")
if not os.path.exists(DATA_DIR):
    print(f"""
[CNN] ERROR: Dataset not found at {DATA_DIR}

Please download the IDC Breast Cancer dataset from Kaggle:
  https://www.kaggle.com/datasets/paultimothymooney/breast-histopathology-images

After downloading, extract so the structure is:
  data/
  └── breast_histopathology/
      ├── 0/          ← Benign images
      └── 1/          ← Malignant images

Then run this script again.
""")
    sys.exit(1)

benign_count   = len([f for f in os.listdir(os.path.join(DATA_DIR, '0')) if f.endswith('.png')])
malignant_count= len([f for f in os.listdir(os.path.join(DATA_DIR, '1')) if f.endswith('.png')])
total          = benign_count + malignant_count
print(f"[CNN] Benign: {benign_count:,}  Malignant: {malignant_count:,}  Total: {total:,}")

# ── Data generators ────────────────────────────────────────────────────────────
print("[CNN] Setting up data pipeline...")

# Use a subset for faster training if dataset is very large
MAX_PER_CLASS = 10000  # use up to 10k per class — increase for better accuracy

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.1,
    validation_split=0.2
)

train_gen = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='training',
    seed=SEED,
    classes=['0', '1']
)

val_gen = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    seed=SEED,
    classes=['0', '1']
)

print(f"[CNN] Train samples: {train_gen.samples}  Val samples: {val_gen.samples}")

# ── Model: MobileNetV2 Transfer Learning ──────────────────────────────────────
print("[CNN] Building MobileNetV2 model...")

base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)
base_model.trainable = False  # freeze base layers

model = keras.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(1, activation='sigmoid')  # binary: 0=benign, 1=malignant
])

# Handle class imbalance
class_weight = {0: malignant_count/total, 1: benign_count/total}

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)

model.summary()

# ── Callbacks ─────────────────────────────────────────────────────────────────
callbacks = [
    keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True, monitor='val_auc', mode='max'),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=2, monitor='val_loss'),
    keras.callbacks.ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_auc', mode='max')
]

# ── Phase 1: Train top layers ──────────────────────────────────────────────────
print("[CNN] Phase 1: Training top layers...")
history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS,
    callbacks=callbacks,
    class_weight=class_weight,
    verbose=1
)

# ── Phase 2: Fine-tune top layers of base model ────────────────────────────────
print("[CNN] Phase 2: Fine-tuning...")
base_model.trainable = True
# Unfreeze only the last 30 layers
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)

history2 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=5,
    callbacks=callbacks,
    class_weight=class_weight,
    verbose=1
)

# ── Evaluate ──────────────────────────────────────────────────────────────────
print("[CNN] Evaluating...")
val_gen.reset()
y_pred_prob = model.predict(val_gen, verbose=0)
y_pred = (y_pred_prob > 0.5).astype(int).flatten()
y_true = val_gen.classes[:len(y_pred)]

report = classification_report(y_true, y_pred, target_names=['Benign','Malignant'], output_dict=True)
auc    = roc_auc_score(y_true, y_pred_prob[:len(y_true)])
acc    = report['accuracy']

print(f"\n[CNN] Results:")
print(f"  Accuracy : {acc*100:.2f}%")
print(f"  ROC-AUC  : {auc*100:.2f}%")
print(f"  Precision (Malignant): {report['Malignant']['precision']*100:.2f}%")
print(f"  Recall    (Malignant): {report['Malignant']['recall']*100:.2f}%")

# Save metrics
metrics = {
    'model_type': 'CNN (MobileNetV2)',
    'accuracy': round(acc * 100, 2),
    'roc_auc':  round(auc * 100, 2),
    'precision_malignant': round(report['Malignant']['precision'] * 100, 2),
    'recall_malignant':    round(report['Malignant']['recall'] * 100, 2),
    'img_size': IMG_SIZE,
    'epochs_trained': len(history.history['loss']) + len(history2.history['loss']),
    'classes': {'0': 'Benign', '1': 'Malignant'}
}
with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)

model.save(MODEL_PATH)
print(f"[CNN] Model saved to {MODEL_PATH}")
print(f"[CNN] Metrics saved to {METRICS_PATH}")
