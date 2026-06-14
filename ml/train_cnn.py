"""
CNN Training — 3-class Breast Cancer Classifier
================================================
Classes:
  0 = Benign tissue  (IDC class-0 patches)
  1 = Malignant tissue (IDC class-1 patches)
  2 = Unrelated / not a medical image

Dataset: data/merged_dataset/  (already on disk)
Model:   MobileNetV2 transfer learning (HEAD ONLY — no fine-tuning)
Saved:   artifacts/cnn_model.h5

The 3-class softmax approach is more stable than binary sigmoid
on imbalanced histopathology data because the Unrelated class
acts as a regulariser and class weights handle the 0/1 imbalance.
"""

import os, sys, json, warnings
warnings.filterwarnings('ignore')
import numpy as np

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data', 'merged_dataset')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
BEST_CKPT    = os.path.join(ARTIFACTS, 'cnn_best.keras')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

IMG_SIZE   = 50
BATCH_SIZE = 64
SEED       = 42

os.makedirs(ARTIFACTS, exist_ok=True)

# ── TensorFlow ────────────────────────────────────────────────────────────────
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.applications import MobileNetV2
    print(f"[CNN] TensorFlow {tf.__version__}")
except ImportError:
    print("[CNN] ERROR: pip install tensorflow"); sys.exit(1)

# ── Dataset check ─────────────────────────────────────────────────────────────
print("[CNN] Checking dataset...")
counts = {}
for cls in ['0','1','2']:
    d = os.path.join(DATA_DIR, cls)
    counts[cls] = len(os.listdir(d)) if os.path.exists(d) else 0
print(f"  Benign(0): {counts['0']:,}  Malignant(1): {counts['1']:,}  Unrelated(2): {counts['2']:,}")

total = sum(counts.values())
if total == 0:
    print("ERROR: No images."); sys.exit(1)

# ── Data generators ───────────────────────────────────────────────────────────
gen = keras.preprocessing.image.ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    horizontal_flip=True, vertical_flip=True,
    zoom_range=0.1,
    width_shift_range=0.1, height_shift_range=0.1,
    brightness_range=[0.85, 1.15],
    validation_split=0.2,
)

train_gen = gen.flow_from_directory(
    DATA_DIR, target_size=(IMG_SIZE,IMG_SIZE), batch_size=BATCH_SIZE,
    class_mode='categorical', subset='training', seed=SEED, classes=['0','1','2'])

val_gen = gen.flow_from_directory(
    DATA_DIR, target_size=(IMG_SIZE,IMG_SIZE), batch_size=BATCH_SIZE,
    class_mode='categorical', subset='validation', seed=SEED, classes=['0','1','2'])

print(f"[CNN] Train: {train_gen.samples:,}  Val: {val_gen.samples:,}")

# Class weights
class_weight = {i: (total / (3 * counts[str(i)])) if counts[str(i)] > 0 else 1.0
                for i in range(3)}
print(f"[CNN] Weights: {class_weight}")

# ── Model ─────────────────────────────────────────────────────────────────────
base = MobileNetV2(input_shape=(IMG_SIZE,IMG_SIZE,3), include_top=False, weights='imagenet')
base.trainable = False

inp = keras.Input(shape=(IMG_SIZE,IMG_SIZE,3))
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

# ── Train (head only — NO fine-tuning phase) ──────────────────────────────────
print("\n[CNN] Training classification head (base frozen)...")
callbacks = [
    keras.callbacks.EarlyStopping(
        patience=5, restore_best_weights=True,
        monitor='val_accuracy', mode='max'),
    keras.callbacks.ReduceLROnPlateau(
        factor=0.5, patience=2, monitor='val_loss', min_lr=1e-6),
    keras.callbacks.ModelCheckpoint(
        BEST_CKPT, save_best_only=True,
        monitor='val_accuracy', mode='max'),
]

history = model.fit(
    train_gen, validation_data=val_gen,
    epochs=20, callbacks=callbacks,
    class_weight=class_weight,
)

best_val_acc = max(history.history['val_accuracy'])
print(f"\n[CNN] Best val_accuracy: {best_val_acc*100:.2f}%")

# ── Evaluate using the best checkpoint ───────────────────────────────────────
print("[CNN] Loading best checkpoint for evaluation...")
if os.path.exists(BEST_CKPT):
    best = keras.models.load_model(BEST_CKPT)
else:
    best = model

from sklearn.metrics import classification_report, confusion_matrix

eval_gen = keras.preprocessing.image.ImageDataGenerator(rescale=1./255).flow_from_directory(
    DATA_DIR, target_size=(IMG_SIZE,IMG_SIZE), batch_size=BATCH_SIZE,
    class_mode='categorical', shuffle=False, classes=['0','1','2'])

y_prob = best.predict(eval_gen, verbose=1)
y_pred = np.argmax(y_prob, axis=1)
y_true = eval_gen.classes[:len(y_pred)]

report = classification_report(y_true, y_pred,
    target_names=['Benign','Malignant','Unrelated'], output_dict=True)
acc = report['accuracy']
cm  = confusion_matrix(y_true, y_pred)

print(classification_report(y_true, y_pred,
    target_names=['Benign','Malignant','Unrelated']))
print(f"Overall accuracy: {acc*100:.2f}%")

# ── Save ──────────────────────────────────────────────────────────────────────
metrics = {
    'model_type': 'CNN (MobileNetV2 3-class, IDC dataset)',
    'dataset': 'Real IDC patient patches (8863,8864,8865,8867,8913) + unrelated',
    'accuracy': round(acc*100, 2),
    'img_size': IMG_SIZE,
    'val_samples': int(eval_gen.samples),
    'classes': {'0':'Benign','1':'Malignant','2':'Unrelated'},
    'per_class': {
        'Benign':    {k: round(v*100,2) for k,v in report['Benign'].items() if k!='support'},
        'Malignant': {k: round(v*100,2) for k,v in report['Malignant'].items() if k!='support'},
        'Unrelated': {k: round(v*100,2) for k,v in report['Unrelated'].items() if k!='support'},
    },
    'confusion_matrix': cm.tolist(),
}

with open(METRICS_PATH,'w') as f:
    json.dump(metrics, f, indent=2)

best.save(MODEL_PATH)
if os.path.exists(BEST_CKPT):
    os.remove(BEST_CKPT)

print(f"\n[CNN] Model  → {MODEL_PATH}")
print(f"[CNN] Metrics → {METRICS_PATH}")
print(f"[CNN] Accuracy: {acc*100:.2f}%")
