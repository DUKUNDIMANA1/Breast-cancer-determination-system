"""
CNN Training Script — BreastCare AI (3-Class Merged Dataset)
=============================================================
Trains a MobileNetV2 classifier with 3 output classes:
  0 — Benign tissue
  1 — Malignant tissue
  2 — Unrelated (non-tissue) image  ← used for validation gate

Dataset:
  data/merged_dataset/
    0/   ← benign  (IDC patches + Wisconsin CSV heatmaps)
    1/   ← malignant
    2/   ← synthetic unrelated images

Steps:
  python ml/prepare_dataset.py --csv-only      (or --source <IDC_dir>)
  python ml/train_cnn.py

Output:
  artifacts/cnn_model.h5       — trained Keras model
  artifacts/cnn_metrics.json   — accuracy / AUC / per-class report
"""

import os, sys, json, warnings
warnings.filterwarnings('ignore')
import numpy as np

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data', 'merged_dataset')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

IMG_SIZE   = 50
BATCH_SIZE = 32
EPOCHS     = 20
SEED       = 42
NUM_CLASSES = 3   # 0=Benign, 1=Malignant, 2=Unrelated

os.makedirs(ARTIFACTS, exist_ok=True)


# ── 0. Verify TensorFlow ──────────────────────────────────────────────────────
print("[CNN] Checking TensorFlow...")
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.applications import MobileNetV2
    print(f"[CNN] TensorFlow {tf.__version__} ready.")
except ImportError:
    print("[CNN] ERROR: TensorFlow not installed.  Run:  pip install tensorflow")
    sys.exit(1)


# ── 1. Verify dataset ─────────────────────────────────────────────────────────
print("\n[CNN] Checking dataset...")
if not os.path.exists(DATA_DIR):
    print(f"""
[CNN] ERROR: Merged dataset not found at {DATA_DIR}
Run first:  python ml/prepare_dataset.py --csv-only
""")
    sys.exit(1)

counts = {}
for cls in ['0', '1', '2']:
    d = os.path.join(DATA_DIR, cls)
    if os.path.exists(d):
        counts[cls] = len([f for f in os.listdir(d)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    else:
        counts[cls] = 0

total = sum(counts.values())
if total == 0:
    print("[CNN] ERROR: No images found. Run prepare_dataset.py first.")
    sys.exit(1)

print(f"[CNN] Benign (0): {counts['0']:,} | Malignant (1): {counts['1']:,} | "
      f"Unrelated (2): {counts['2']:,} | Total: {total:,}")

if counts['2'] == 0:
    print("[CNN] WARNING: No unrelated images (class 2). Re-run prepare_dataset.py.")


# ── 2. Data pipeline ──────────────────────────────────────────────────────────
print("\n[CNN] Setting up data pipeline...")

train_datagen = keras.preprocessing.image.ImageDataGenerator(
    rescale=1.0 / 255,
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.15,
    brightness_range=[0.8, 1.2],
    validation_split=0.2,
)

train_gen = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',        # one-hot for 3 classes
    subset='training',
    seed=SEED,
    classes=['0', '1', '2'],
)

val_gen = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    seed=SEED,
    classes=['0', '1', '2'],
)

print(f"[CNN] Train: {train_gen.samples:,} | Val: {val_gen.samples:,}")


# ── 3. Class weights ──────────────────────────────────────────────────────────
class_weight = {}
for i, cls in enumerate(['0', '1', '2']):
    n = counts[cls]
    class_weight[i] = (total / (NUM_CLASSES * n)) if n > 0 else 1.0
print(f"[CNN] Class weights — benign: {class_weight[0]:.2f}, "
      f"malignant: {class_weight[1]:.2f}, unrelated: {class_weight[2]:.2f}")


# ── 4. Model — MobileNetV2 + 3-class head ────────────────────────────────────
print("\n[CNN] Building MobileNetV2 model (3-class)...")

base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet',
)
base_model.trainable = False

inputs  = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x       = base_model(inputs, training=False)
x       = layers.GlobalAveragePooling2D()(x)
x       = layers.BatchNormalization()(x)
x       = layers.Dense(256, activation='relu')(x)
x       = layers.Dropout(0.4)(x)
x       = layers.Dense(128, activation='relu')(x)
x       = layers.Dropout(0.3)(x)
outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)  # 3-class softmax

cnn_model = keras.Model(inputs, outputs, name='BreastCare_CNN_3class')

cnn_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss='categorical_crossentropy',
    metrics=['accuracy'],
)
cnn_model.summary()


# ── 5. Phase 1: Train head (base frozen) ─────────────────────────────────────
print("\n[CNN] Phase 1 — training classification head...")

callbacks_p1 = [
    keras.callbacks.EarlyStopping(
        patience=5, restore_best_weights=True, monitor='val_accuracy', mode='max'),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.5, patience=3, monitor='val_loss', min_lr=1e-6),
    keras.callbacks.ModelCheckpoint(
        MODEL_PATH, save_best_only=True, monitor='val_accuracy', mode='max'),
]

history1 = cnn_model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS,
    callbacks=callbacks_p1,
    class_weight=class_weight,
    verbose=1,
)


# ── 6. Phase 2: Fine-tune last 30 base layers ────────────────────────────────
print("\n[CNN] Phase 2 — fine-tuning last 30 base layers...")

base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

cnn_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss='categorical_crossentropy',
    metrics=['accuracy'],
)

callbacks_p2 = [
    keras.callbacks.EarlyStopping(
        patience=4, restore_best_weights=True, monitor='val_accuracy', mode='max'),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.3, patience=2, monitor='val_loss', min_lr=1e-7),
    keras.callbacks.ModelCheckpoint(
        MODEL_PATH, save_best_only=True, monitor='val_accuracy', mode='max'),
]

history2 = cnn_model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=10,
    callbacks=callbacks_p2,
    class_weight=class_weight,
    verbose=1,
)


# ── 7. Evaluate ───────────────────────────────────────────────────────────────
print("\n[CNN] Evaluating on validation set...")
from sklearn.metrics import classification_report, confusion_matrix

# Collect predictions in a single pass (avoids generator reset alignment issues)
val_datagen_eval = keras.preprocessing.image.ImageDataGenerator(rescale=1.0 / 255)
eval_gen = val_datagen_eval.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False,                  # IMPORTANT: no shuffle for correct alignment
    classes=['0', '1', '2'],
)

y_pred_prob = cnn_model.predict(eval_gen, verbose=0)    # shape (N, 3)
y_pred      = np.argmax(y_pred_prob, axis=1)
y_true      = eval_gen.classes

report = classification_report(
    y_true, y_pred,
    target_names=['Benign', 'Malignant', 'Unrelated'],
    output_dict=True,
)
acc = report['accuracy']
cm  = confusion_matrix(y_true, y_pred)

print(f"\n  Overall Accuracy : {acc * 100:.2f}%")
print(f"\n  Per-class:")
for cls_name in ['Benign', 'Malignant', 'Unrelated']:
    r = report[cls_name]
    print(f"    {cls_name:12s}  precision={r['precision']:.2f}  "
          f"recall={r['recall']:.2f}  f1={r['f1-score']:.2f}")
print(f"\n  Confusion matrix:\n{cm}")

total_epochs = len(history1.history['loss']) + len(history2.history['loss'])

metrics = {
    'model_type':    'CNN (MobileNetV2 Transfer Learning, 3-class)',
    'dataset':       'Merged (IDC patches + Wisconsin CSV heatmaps + synthetic unrelated)',
    'accuracy':      round(acc * 100, 2),
    'img_size':      IMG_SIZE,
    'epochs_trained': total_epochs,
    'train_samples': train_gen.samples,
    'val_samples':   val_gen.samples,
    'class_counts':  {k: int(v) for k, v in counts.items()},
    'classes':       {'0': 'Benign', '1': 'Malignant', '2': 'Unrelated'},
    'per_class':     {
        cls: {
            'precision': round(report[cls]['precision'] * 100, 2),
            'recall':    round(report[cls]['recall'] * 100, 2),
            'f1':        round(report[cls]['f1-score'] * 100, 2),
        }
        for cls in ['Benign', 'Malignant', 'Unrelated']
    },
    'confusion_matrix': cm.tolist(),
}

with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)


# ── 8. Save ───────────────────────────────────────────────────────────────────
cnn_model.save(MODEL_PATH)
print(f"\n[CNN] Model saved  → {MODEL_PATH}")
print(f"[CNN] Metrics saved → {METRICS_PATH}")
print("\n" + "=" * 60)
print(f"  Training complete!  Accuracy: {acc * 100:.2f}%")
print("=" * 60)


import os, sys, json, warnings
warnings.filterwarnings('ignore')

import numpy as np

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data', 'merged_dataset')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

IMG_SIZE   = 50      # matches IDC patch size; CSV heatmaps also rendered at 50×50
BATCH_SIZE = 32
EPOCHS     = 20
SEED       = 42

os.makedirs(ARTIFACTS, exist_ok=True)


# ── 0. Verify TensorFlow ──────────────────────────────────────────────────────
print("[CNN] Checking TensorFlow...")
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.applications import MobileNetV2
    print(f"[CNN] TensorFlow {tf.__version__} ready.")
except ImportError:
    print("[CNN] ERROR: TensorFlow not installed.")
    print("      Run:  pip install tensorflow")
    sys.exit(1)


# ── 1. Verify dataset ─────────────────────────────────────────────────────────
print("\n[CNN] Checking dataset...")
if not os.path.exists(DATA_DIR):
    print(f"""
[CNN] ERROR: Merged dataset not found at:
      {DATA_DIR}

Please run the preparation script first:

  # CSV only (no IDC images required):
  python ml/prepare_dataset.py --csv-only

  # IDC + CSV merged:
  python ml/prepare_dataset.py --source "C:/path/to/IDC_regular_ps50_idx5"
""")
    sys.exit(1)

class0_dir = os.path.join(DATA_DIR, '0')
class1_dir = os.path.join(DATA_DIR, '1')

if not os.path.exists(class0_dir) or not os.path.exists(class1_dir):
    print(f"[CNN] ERROR: Expected subdirectories '0' and '1' inside {DATA_DIR}")
    sys.exit(1)

benign_count    = len([f for f in os.listdir(class0_dir)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
malignant_count = len([f for f in os.listdir(class1_dir)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
total           = benign_count + malignant_count

if total == 0:
    print("[CNN] ERROR: No images found in the merged dataset. Run prepare_dataset.py first.")
    sys.exit(1)

print(f"[CNN] Benign (0): {benign_count:,} | Malignant (1): {malignant_count:,} | Total: {total:,}")


# ── 2. Data pipeline ──────────────────────────────────────────────────────────
print("\n[CNN] Setting up data pipeline...")

train_datagen = keras.preprocessing.image.ImageDataGenerator(
    rescale=1.0 / 255,
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.15,
    brightness_range=[0.8, 1.2],
    validation_split=0.2,
)

train_gen = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='training',
    seed=SEED,
    classes=['0', '1'],
)

val_gen = train_datagen.flow_from_directory(
    DATA_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    seed=SEED,
    classes=['0', '1'],
)

print(f"[CNN] Train: {train_gen.samples:,} samples | Val: {val_gen.samples:,} samples")


# ── 3. Model — MobileNetV2 Transfer Learning ──────────────────────────────────
print("\n[CNN] Building MobileNetV2 model...")

base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet',
)
base_model.trainable = False   # freeze base in Phase 1

inputs  = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x       = base_model(inputs, training=False)
x       = layers.GlobalAveragePooling2D()(x)
x       = layers.BatchNormalization()(x)
x       = layers.Dense(256, activation='relu')(x)
x       = layers.Dropout(0.4)(x)
x       = layers.Dense(128, activation='relu')(x)
x       = layers.Dropout(0.3)(x)
outputs = layers.Dense(1, activation='sigmoid')(x)   # 0=benign, 1=malignant

cnn_model = keras.Model(inputs, outputs, name='BreastCare_CNN')

# Class weights to handle imbalance
weight_for_0 = (1 / benign_count)    * (total / 2.0)
weight_for_1 = (1 / malignant_count) * (total / 2.0)
class_weight = {0: weight_for_0, 1: weight_for_1}
print(f"[CNN] Class weights — benign: {weight_for_0:.3f}, malignant: {weight_for_1:.3f}")


# ── 4. Phase 1: Train top layers only ────────────────────────────────────────
print("\n[CNN] Phase 1 — training classification head (base frozen)...")

cnn_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')],
)
cnn_model.summary()

callbacks_p1 = [
    keras.callbacks.EarlyStopping(
        patience=5, restore_best_weights=True,
        monitor='val_auc', mode='max'),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.5, patience=3, monitor='val_loss', min_lr=1e-6),
    keras.callbacks.ModelCheckpoint(
        MODEL_PATH, save_best_only=True,
        monitor='val_auc', mode='max'),
]

history1 = cnn_model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS,
    callbacks=callbacks_p1,
    class_weight=class_weight,
    verbose=1,
)


# ── 5. Phase 2: Fine-tune top layers of MobileNetV2 ──────────────────────────
print("\n[CNN] Phase 2 — fine-tuning last 30 base layers...")

base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

cnn_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')],
)

callbacks_p2 = [
    keras.callbacks.EarlyStopping(
        patience=4, restore_best_weights=True,
        monitor='val_auc', mode='max'),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.3, patience=2, monitor='val_loss', min_lr=1e-7),
    keras.callbacks.ModelCheckpoint(
        MODEL_PATH, save_best_only=True,
        monitor='val_auc', mode='max'),
]

history2 = cnn_model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=10,
    callbacks=callbacks_p2,
    class_weight=class_weight,
    verbose=1,
)


# ── 6. Evaluate ───────────────────────────────────────────────────────────────
print("\n[CNN] Evaluating on validation set...")

from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

val_gen.reset()
y_pred_prob = cnn_model.predict(val_gen, verbose=0).flatten()
y_pred      = (y_pred_prob >= 0.5).astype(int)
y_true      = val_gen.classes[:len(y_pred)]

report = classification_report(
    y_true, y_pred,
    target_names=['Benign', 'Malignant'],
    output_dict=True,
)
auc = roc_auc_score(y_true, y_pred_prob[:len(y_true)])
acc = report['accuracy']

cm = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0

print(f"\n  Accuracy    : {acc * 100:.2f}%")
print(f"  ROC-AUC     : {auc * 100:.2f}%")
print(f"  Sensitivity : {sensitivity * 100:.2f}%  (recall malignant)")
print(f"  Specificity : {specificity * 100:.2f}%  (recall benign)")
print(f"  Precision (M): {report['Malignant']['precision'] * 100:.2f}%")
print(f"\nConfusion Matrix (TN={tn} FP={fp} FN={fn} TP={tp})")

total_epochs = len(history1.history['loss']) + len(history2.history['loss'])

metrics = {
    'model_type':          'CNN (MobileNetV2 Transfer Learning)',
    'dataset':             'Merged (IDC histopathology + Wisconsin CSV heatmaps)',
    'accuracy':            round(acc * 100, 2),
    'roc_auc':             round(auc * 100, 2),
    'sensitivity':         round(sensitivity * 100, 2),
    'specificity':         round(specificity * 100, 2),
    'precision_malignant': round(report['Malignant']['precision'] * 100, 2),
    'recall_malignant':    round(report['Malignant']['recall'] * 100, 2),
    'img_size':            IMG_SIZE,
    'epochs_trained':      total_epochs,
    'train_samples':       train_gen.samples,
    'val_samples':         val_gen.samples,
    'benign_total':        benign_count,
    'malignant_total':     malignant_count,
    'classes':             {'0': 'Benign', '1': 'Malignant'},
    'confusion_matrix':    {'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)},
}

with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)


# ── 7. Save ───────────────────────────────────────────────────────────────────
cnn_model.save(MODEL_PATH)
print(f"\n[CNN] Model saved  → {MODEL_PATH}")
print(f"[CNN] Metrics saved → {METRICS_PATH}")
print("\n" + "=" * 60)
print("  Training complete!")
print(f"  Accuracy: {acc * 100:.2f}%  |  AUC: {auc * 100:.2f}%")
print("=" * 60)
