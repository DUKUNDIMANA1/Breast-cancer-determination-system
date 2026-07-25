"""
Train CNN directly from patient folders — NO file copying.
==========================================================
Uses tf.data to read images directly from patient folders.
Balanced: 60K benign + 60K malignant (equal classes).

Usage:
  python ml/train_direct.py
  python ml/train_direct.py --max 30000
"""
import os, sys, json, argparse, warnings, glob, tempfile, random
warnings.filterwarnings('ignore')
import numpy as np
import cv2

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, 'data')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'cnn_model.h5')
METRICS_PATH = os.path.join(ARTIFACTS, 'cnn_metrics.json')

IMG_SIZE   = 50
BATCH_SIZE = 64
SEED       = 42
VAL_SPLIT  = 0.2

parser = argparse.ArgumentParser()
parser.add_argument('--max', type=int, default=60000,
                    help='Max images per tissue class. Default: 60000')
args, _ = parser.parse_known_args()

print("=" * 64)
print("  BreastCare AI — Train CNN (direct, no copy, balanced)")
print("=" * 64)
print(f"  Max per class : {args.max:,}")
print(f"  IMG size      : {IMG_SIZE}x{IMG_SIZE}")
print()

# ── Collect file paths ────────────────────────────────────────────────────────
print("[1/3] Scanning patient folders …")

benign_files    = []
malignant_files = []

for patient_id in sorted(os.listdir(DATA_DIR)):
    pdir = os.path.join(DATA_DIR, patient_id)
    if not os.path.isdir(pdir) or not patient_id.isdigit():
        continue
    benign_files.extend(glob.glob(os.path.join(pdir, '0', '*.png')))
    malignant_files.extend(glob.glob(os.path.join(pdir, '1', '*.png')))

print(f"  Benign    (0): {len(benign_files):,}")
print(f"  Malignant (1): {len(malignant_files):,}")

rng = random.Random(SEED)
rng.shuffle(benign_files)
rng.shuffle(malignant_files)

# Balance: cap both to args.max
n = min(args.max, len(benign_files), len(malignant_files))
benign_files    = benign_files[:n]
malignant_files = malignant_files[:n]
print(f"  Using (balanced): {n:,} benign + {n:,} malignant")

# Generate 5K synthetic unrelated images into temp dir

# Generate 5K synthetic unrelated images into temp dir
UNREL_DIR = os.path.join(tempfile.gettempdir(), 'breastcare_unrel')
os.makedirs(UNREL_DIR, exist_ok=True)
unrel_files = [os.path.join(UNREL_DIR, f) for f in os.listdir(UNREL_DIR) if f.endswith('.png')]

if len(unrel_files) < 5000:
    print("  Generating 5,000 synthetic unrelated images …")
    r2 = np.random.RandomState(99)
    per = 625
    imgs = []
    for _ in range(per): imgs.append(np.full((IMG_SIZE,IMG_SIZE,3), r2.randint(0,256,3,dtype=np.uint8), dtype=np.uint8))
    for _ in range(per): imgs.append(r2.randint(50,200,(IMG_SIZE,IMG_SIZE,3),dtype=np.uint8))
    for _ in range(per):
        b=int(r2.randint(230,256)); img=np.full((IMG_SIZE,IMG_SIZE,3),b,dtype=np.uint8)
        for _ in range(int(r2.randint(2,6))): img[int(r2.randint(5,IMG_SIZE-5)):int(r2.randint(5,IMG_SIZE-5))+2,5:IMG_SIZE-5]=int(r2.randint(0,60))
        imgs.append(img)
    for _ in range(per):
        c1=r2.randint(0,256,3,dtype=np.uint8); c2=r2.randint(0,256,3,dtype=np.uint8)
        xs=np.linspace(0,1,IMG_SIZE); img=np.zeros((IMG_SIZE,IMG_SIZE,3),dtype=np.uint8)
        for ch in range(3): img[:,:,ch]=np.tile((c1[ch]*(1-xs)+c2[ch]*xs).astype(np.uint8),(IMG_SIZE,1))
        imgs.append(img)
    for _ in range(per): imgs.append(np.full((IMG_SIZE,IMG_SIZE,3),int(r2.randint(0,40)),dtype=np.uint8))
    for _ in range(per): imgs.append(np.full((IMG_SIZE,IMG_SIZE,3),int(r2.randint(220,256)),dtype=np.uint8))
    for _ in range(per):
        img=np.full((IMG_SIZE,IMG_SIZE,3),240,dtype=np.uint8)
        cv2.circle(img,(IMG_SIZE//2,IMG_SIZE//2),IMG_SIZE//3,(int(r2.randint(0,120)),int(r2.randint(0,120)),int(r2.randint(150,256))),-1)
        imgs.append(img)
    for _ in range(per):
        img=np.zeros((IMG_SIZE,IMG_SIZE,3),dtype=np.uint8); t=int(r2.randint(4,12))
        for ry in range(0,IMG_SIZE,t):
            for rx in range(0,IMG_SIZE,t): img[ry:ry+t,rx:rx+t]=230 if (ry//t+rx//t)%2==0 else 20
        imgs.append(img)
    r2.shuffle(imgs)
    for i,img in enumerate(imgs[:5000]):
        cv2.imwrite(os.path.join(UNREL_DIR, f'u_{i:07d}.png'), img)
    unrel_files = [os.path.join(UNREL_DIR, f) for f in os.listdir(UNREL_DIR) if f.endswith('.png')]

unrel_files = unrel_files[:5000]
print(f"  Unrelated (2): {len(unrel_files):,}")

# ── Build train/val splits ────────────────────────────────────────────────────
print("\n[2/3] Building splits …")

def split(files, ratio=VAL_SPLIT):
    n_val = int(len(files) * ratio)
    return files[n_val:], files[:n_val]

rng.shuffle(benign_files); rng.shuffle(malignant_files); rng.shuffle(unrel_files)
b_tr, b_val = split(benign_files)
m_tr, m_val = split(malignant_files)
u_tr, u_val = split(unrel_files)

train = [(p, 0) for p in b_tr] + [(p, 1) for p in m_tr] + [(p, 2) for p in u_tr]
val   = [(p, 0) for p in b_val] + [(p, 1) for p in m_val] + [(p, 2) for p in u_val]
rng.shuffle(train)

print(f"  Train: {len(train):,}  Val: {len(val):,}")
total = len(train)
# Boost benign weight 2x — model must not ignore benign false positives
class_weight = {
    0: (total / (3 * len(b_tr))) * 2.0,   # benign  — 2× boost
    1: total / (3 * len(m_tr)),             # malignant
    2: total / (3 * len(u_tr)),             # unrelated
}
print(f"  Class weights: { {k:round(v,3) for k,v in class_weight.items()} }")

# ── tf.data pipeline ──────────────────────────────────────────────────────────
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2

print(f"\n  TensorFlow {tf.__version__}")

def make_ds(samples, augment=False, shuffle=False):
    paths  = tf.constant([s[0] for s in samples])
    labels = tf.constant([s[1] for s in samples], dtype=tf.int32)
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(min(len(samples), 5000), seed=SEED)
    def load(p, lbl):
        raw = tf.io.read_file(p)
        img = tf.image.decode_png(raw, channels=3)
        img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
        img = tf.cast(img, tf.float32) / 255.0
        if augment:
            img = tf.image.random_flip_left_right(img)
            img = tf.image.random_flip_up_down(img)
            img = tf.image.random_brightness(img, 0.15)
        return img, tf.one_hot(lbl, 3)
    return ds.map(load, num_parallel_calls=tf.data.AUTOTUNE).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

train_ds = make_ds(train, augment=True,  shuffle=True)
val_ds   = make_ds(val,   augment=False, shuffle=False)

# ── Model ─────────────────────────────────────────────────────────────────────
print("\n[3/3] Training …")
os.makedirs(ARTIFACTS, exist_ok=True)

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
model.compile(optimizer=keras.optimizers.Adam(1e-3),
              loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()

cb = [keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True,
                                    monitor='val_accuracy', mode='max'),
      keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=2,
                                        monitor='val_loss', min_lr=1e-6)]

print("\n  Phase 1: frozen base …")
h1 = model.fit(train_ds, validation_data=val_ds, epochs=20,
               class_weight=class_weight, callbacks=cb)
best = max(h1.history['val_accuracy'])
print(f"\n  Phase 1 best val_accuracy: {best*100:.2f}%")

if best >= 0.75:   # lower threshold — fine-tune whenever head converges at all
    print("\n  Phase 2: fine-tune ALL MobileNetV2 layers …")
    base.trainable = True   # unfreeze entire base
    model.compile(optimizer=keras.optimizers.Adam(1e-4),
                  loss='categorical_crossentropy', metrics=['accuracy'])
    cb2 = [keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True,
                                         monitor='val_accuracy', mode='max'),
           keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=2,
                                             monitor='val_loss', min_lr=1e-7)]
    h2 = model.fit(train_ds, validation_data=val_ds, epochs=10,
                   class_weight=class_weight, callbacks=cb2)
    best = max(best, max(h2.history['val_accuracy']))
    print(f"  Phase 2 best: {best*100:.2f}%")

# Evaluate
from sklearn.metrics import classification_report, confusion_matrix
print("\n  Evaluating …")
eval_ds = make_ds(val, augment=False, shuffle=False)
y_prob  = model.predict(eval_ds)
y_pred  = np.argmax(y_prob, axis=1)
y_true  = np.array([s[1] for s in val])[:len(y_pred)]

report = classification_report(y_true, y_pred,
    target_names=['Benign','Malignant','Unrelated'], output_dict=True)
acc = report['accuracy']
cm  = confusion_matrix(y_true, y_pred)

print(classification_report(y_true, y_pred, target_names=['Benign','Malignant','Unrelated']))
print(f"Accuracy: {acc*100:.2f}%")

model.save(MODEL_PATH)
print(f"  Model → {MODEL_PATH}")

metrics = {
    'model_type': 'CNN (MobileNetV2 3-class, IDC dataset)',
    'dataset':    f'Patient folders balanced — {n:,} benign + {n:,} malignant + {len(unrel_files):,} unrelated',
    'accuracy':   round(acc*100, 2),
    'img_size':   IMG_SIZE,
    'train_samples': len(train),
    'val_samples':   len(val),
    'classes':    {'0':'Benign','1':'Malignant','2':'Unrelated'},
    'per_class': {
        'Benign':    {k: round(v*100,2) for k,v in report['Benign'].items()    if k!='support'},
        'Malignant': {k: round(v*100,2) for k,v in report['Malignant'].items() if k!='support'},
        'Unrelated': {k: round(v*100,2) for k,v in report['Unrelated'].items() if k!='support'},
    },
    'confusion_matrix': cm.tolist(),
}
with open(METRICS_PATH, 'w') as f: json.dump(metrics, f, indent=2)
print(f"  Metrics → {METRICS_PATH}")

print()
print("=" * 64)
print(f"  DONE — Accuracy: {acc*100:.2f}%")
print("=" * 64)
