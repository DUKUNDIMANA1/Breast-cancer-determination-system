"""
CNN Predictor — BreastCare AI
==============================
Uses the AutoML-selected CNN model trained on IDC histopathology patches.
The model architecture is chosen automatically by ml/train_direct.py from
multiple candidate configurations; the best one (highest validation accuracy)
is saved to artifacts/cnn_model.h5 alongside a metrics file that records
the selected architecture.

Classes:
  0 = Benign  (IDC-negative tissue)
  1 = Malignant (IDC-positive tissue)
  2 = Unrelated (not a tissue slide)

Validation:
  Step 1 — Colour sanity (fast, rejects obvious non-tissue: pure green,
            cyan water, blue sky, pure red, blank, black)
  Step 2 — AutoML CNN 3-class check (must predict class 0 or 1 with >= 45%
            confidence)

No H&E stain check — the CNN handles tissue vs non-tissue classification.
"""

import os
import json
import hashlib
import numpy as np

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH      = os.path.join(BASE_DIR, 'artifacts', 'cnn_model.h5')
METRICS_PATH    = os.path.join(BASE_DIR, 'artifacts', 'cnn_metrics.json')
IMG_SIZE        = 50

# Minimum CNN confidence to accept as tissue (class 0 or 1)
TISSUE_MIN_CONF = 0.45

_cnn_model   = None
_model_n_out = 3


def get_model_display_name():
    """
    Return a human-readable model name that reflects the AutoML architecture
    stored in cnn_metrics.json. Falls back gracefully if the file is missing.
    """
    try:
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            arch = metrics.get('architecture') or metrics.get('automl', {})
            model_type = metrics.get('model_type', '')
            if arch and isinstance(arch, dict):
                filters = arch.get('base_filters', '?')
                blocks  = arch.get('conv_blocks', '?')
                lr      = arch.get('learning_rate', '?')
                return (f"AutoML-CNN "
                        f"(filters={filters}, blocks={blocks}, lr={lr})")
            if 'AutoML' in model_type:
                return 'AutoML-selected CNN (IDC dataset)'
    except Exception:
        pass
    return 'AutoML-CNN (IDC histopathology)'


# ── In-memory result caches (keyed by SHA-256 of image bytes) ─────────────────
# Holds at most 256 entries; oldest entry is evicted when full.
_MAX_CACHE   = 256
_predict_cache  = {}   # hash → cnn_predict_image result dict
_validate_cache = {}   # hash → cnn_validate_image result dict

def _img_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

def _cache_get(store: dict, key: str):
    return store.get(key)

def _cache_set(store: dict, key: str, value):
    if len(store) >= _MAX_CACHE:
        # Evict the oldest key (insertion-order guaranteed in Python 3.7+)
        store.pop(next(iter(store)))
    store[key] = value


def load_cnn():
    """Load AutoML-selected model lazily. Returns None if TF unavailable."""
    global _cnn_model, _model_n_out
    if _cnn_model is not None:
        return _cnn_model

    try:
        import tensorflow as tf
    except ImportError:
        print("[AutoML-CNN] TensorFlow not installed — heuristic fallback active.")
        return None
    except Exception as e:
        print(f"[AutoML-CNN] TensorFlow import error: {e}")
        return None

    for path in [MODEL_PATH]:
        if not os.path.exists(path):
            continue
        if os.path.getsize(path) < 1000:
            print(f"[AutoML-CNN] Skipping {os.path.basename(path)} — empty/corrupt.")
            continue
        try:
            _cnn_model = tf.keras.models.load_model(path)
            out_shape  = _cnn_model.output_shape
            _model_n_out = out_shape[-1] if len(out_shape) > 1 else 1
            kind = f"{_model_n_out}-class softmax" if _model_n_out > 1 else "binary sigmoid"
            display = get_model_display_name()
            print(f"[AutoML-CNN] Model loaded: {display} ({kind}).")
            return _cnn_model
        except Exception as e:
            print(f"[AutoML-CNN] Could not load {os.path.basename(path)}: {e}")

    print("[AutoML-CNN] No valid model — heuristic fallback active.")
    return None


def _decode_image(image_bytes, model=None):
    """Decode bytes and resize to the loaded model's input dimensions."""
    try:
        import cv2
    except ImportError:
        raise RuntimeError("opencv-python-headless not installed")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — unsupported format or corrupted file.")
    input_shape = getattr(model, 'input_shape', None)
    if isinstance(input_shape, list):
        input_shape = input_shape[0]
    if input_shape and len(input_shape) == 4:
        height = input_shape[1] or IMG_SIZE
        width = input_shape[2] or IMG_SIZE
        channels = input_shape[3] or 3
    else:
        height = width = IMG_SIZE
        channels = 3
    if channels == 1:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = np.expand_dims(img, axis=-1)
    img = cv2.resize(img, (int(width), int(height)))
    if img.ndim == 2:
        img = np.expand_dims(img, axis=-1)
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)


def _colour_sanity(image_bytes):
    """
    Fast colour sanity — rejects obviously non-tissue images.
    Catches: pure green/grass, cyan water, blue sky, pure red, blank, black.
    Does NOT use H&E stain check — the CNN handles that.
    Returns (passes: bool, reason: str)
    """
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, "Could not decode image file"

        if img.shape[0] > 200:
            img = cv2.resize(img, (200, 200))

        gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        bright = float(img.mean())
        std    = float(gray.std())

        # Blank / black / solid colour
        if bright > 245 and std < 5:
            return False, "Image appears blank or empty"
        if bright < 5:
            return False, "Image is completely black"
        if std < 3:
            return False, "Image has no variation (solid colour)"

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(float)
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        mean_r = float(r.mean())
        mean_g = float(g.mean())
        mean_b = float(b.mean())

        # Pure green dominant (grass, plants, leaves)
        if mean_g > mean_r * 1.35 and mean_g > mean_b * 1.25 and mean_g > 80:
            return False, f"Green-dominant image (R={mean_r:.0f} G={mean_g:.0f} B={mean_b:.0f})"

        # Cyan water / pool / sky (blue+green >> red)
        cyan = float(np.mean((b > 120) & (g > 100) & (r < 130)))
        if cyan > 0.20:
            return False, f"Cyan/water image (cyan={cyan:.0%})"

        # Blue dominant (sky, sea)
        if mean_b > mean_r * 1.35 and mean_b > mean_g * 1.1 and mean_b > 80:
            return False, f"Blue-dominant image (R={mean_r:.0f} G={mean_g:.0f} B={mean_b:.0f})"

        # Pure red objects
        red = float(np.mean((r > 180) & (g < 80) & (b < 80)))
        if red > 0.15:
            return False, f"Red-dominant image (red={red:.0%})"

        # Document/icon detection: very high white + some black lines
        white = float(np.mean((r > 220) & (g > 220) & (b > 220)))
        black = float(np.mean((r < 40)  & (g < 40)  & (b < 40)))
        if white > 0.40 and black > 0.05:
            return False, f"Document/icon image (white={white:.0%}, black={black:.0%})"
        if white > 0.80:   # only reject nearly-all-white (was 0.55, too aggressive)
            return False, f"Document/screenshot (white={white:.0%})"

        # Natural photo detection (animals, people, landscapes, food, objects)
        # Natural photos have warm tones (yellow/orange/brown/skin) that H&E tissue doesn't
        # Key insight: in tissue slides, warm tones (eosin pink) coexist with purple nuclei
        # In natural photos, warm tones dominate WITHOUT the haematoxylin purple/blue nuclei
        hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(float)
        h_ch = hsv[:,:,0]
        s_ch = hsv[:,:,1]
        v_ch = hsv[:,:,2]

        # Warm natural tones: hue 5-35 (yellow/orange/brown/skin/fur) with decent saturation
        warm  = float(np.mean((h_ch >= 5)  & (h_ch <= 35) & (s_ch >= 25) & (v_ch >= 40)))
        # Cool sky/grey tones: hue 90-130, low-mid saturation (clouds, sky, grey backgrounds)
        cool  = float(np.mean((h_ch >= 90) & (h_ch <= 130) & (s_ch < 80) & (v_ch > 100)))
        # Purple/haematoxylin: hue 120-160, meaningful saturation
        purple = float(np.mean((h_ch >= 120) & (h_ch <= 160) & (s_ch >= 40) & (v_ch >= 40)))

        # Natural photo: dominated by warm tones + optional cool sky, WITHOUT purple nuclei
        # Dogs, grass, sand, skin, wood, food all have high warm fraction
        if warm > 0.30 and purple < 0.05:
            return False, f"Natural photo (warm={warm:.0%}, purple={purple:.0%}) — not a tissue slide"

        # Mixed natural scene: warm + cool (landscape, outdoor photos)
        if warm > 0.20 and cool > 0.15 and purple < 0.05:
            return False, f"Natural outdoor scene (warm={warm:.0%}, cool={cool:.0%}, purple={purple:.0%})"

        return True, "Colour sanity passed"

    except Exception as e:
        return True, f"Colour check skipped ({e})"


def _heuristic_validate(image_bytes):
    """Fallback when AutoML-CNN unavailable."""
    ok, reason = _colour_sanity(image_bytes)
    return ok, 50.0 if ok else 0.0, reason if not ok else "Accepted (AutoML-CNN unavailable — basic check passed)."


def cnn_validate_image(image_bytes):
    """
    Validate whether an image is a tissue slide.

    Returns dict:
      is_valid    : bool
      confidence  : float 0-100
      reason      : str
      cnn_used    : bool
    """
    h = _img_hash(image_bytes)
    cached = _cache_get(_validate_cache, h)
    if cached is not None:
        return cached

    # Step 1: fast colour sanity (no model needed)
    col_ok, col_reason = _colour_sanity(image_bytes)
    if not col_ok:
        result = {
            'is_valid':   False,
            'confidence': 0.0,
            'reason':     f"Image rejected: {col_reason}. Upload an H&E stained tissue slide.",
            'cnn_used':   False,
        }
        _cache_set(_validate_cache, h, result)
        return result

    # Step 2: CNN classification
    model = load_cnn()
    if model is None:
        result = {
            'is_valid':   True,
            'confidence': 50.0,
            'reason':     "Accepted (AutoML-CNN unavailable — colour check passed).",
            'cnn_used':   False,
        }
        _cache_set(_validate_cache, h, result)
        return result

    try:
        arr   = _decode_image(image_bytes, model)
        probs = model.predict(arr, verbose=0)[0]

        if _model_n_out == 3:
            p_ben  = float(probs[0])
            p_mal  = float(probs[1])
            p_unrel = float(probs[2])
            pred   = int(np.argmax(probs))
            tissue_conf = max(p_ben, p_mal)

            if pred == 2:
                result = {
                    'is_valid':   False,
                    'confidence': round(p_unrel * 100, 1),
                    'reason':     (f"Image rejected: CNN says Unrelated ({p_unrel:.0%}). "
                                   f"Only tissue slides are accepted."),
                    'cnn_used':   True,
                }
                _cache_set(_validate_cache, h, result)
                return result
            if tissue_conf < TISSUE_MIN_CONF:
                result = {
                    'is_valid':   False,
                    'confidence': round(tissue_conf * 100, 1),
                    'reason':     (f"Image rejected: CNN not confident it is tissue "
                                   f"(Benign={p_ben:.0%}, Malignant={p_mal:.0%}, "
                                   f"Unrelated={p_unrel:.0%})."),
                    'cnn_used':   True,
                }
                _cache_set(_validate_cache, h, result)
                return result
            label = "Benign" if pred == 0 else "Malignant"
            result = {
                'is_valid':   True,
                'confidence': round(tissue_conf * 100, 1),
                'reason':     (f"Valid tissue slide — CNN: {label} "
                               f"(Benign={p_ben:.0%}, Malignant={p_mal:.0%})."),
                'cnn_used':   True,
            }
            _cache_set(_validate_cache, h, result)
            return result
        else:
            # Binary sigmoid
            p_mal = float(probs[0]) if probs.shape == (1,) else float(probs)
            p_ben = 1.0 - p_mal
            if 0.35 <= p_mal <= 0.65:
                result = {
                    'is_valid':   False,
                    'confidence': round(max(p_ben, p_mal) * 100, 1),
                    'reason':     f"Image rejected: CNN uncertain (p={p_mal:.3f}).",
                    'cnn_used':   True,
                }
                _cache_set(_validate_cache, h, result)
                return result
            label = "Malignant" if p_mal >= 0.5 else "Benign"
            conf  = round(max(p_ben, p_mal) * 100, 1)
            result = {'is_valid': True, 'confidence': conf,
                      'reason': f"Valid tissue — CNN: {label} ({conf:.0f}%).",
                      'cnn_used': True}
            _cache_set(_validate_cache, h, result)
            return result

    except Exception as e:
        print(f"[AutoML-CNN] validate error: {e}")
        result = {
            'is_valid':   True,
            'confidence': 50.0,
            'reason':     f"AutoML-CNN error ({e}); colour check passed.",
            'cnn_used':   False,
        }
        _cache_set(_validate_cache, h, result)
        return result


def cnn_predict_image(image_bytes):
    """
    Predict Benign (0) or Malignant (1) from image bytes.

    Uses elevated threshold for malignant (0.55 instead of 0.5) to reduce
    false positives (benign classified as malignant).

    Returns dict:
      available   : bool
      result      : 0=Benign, 1=Malignant, None if unrelated/unavailable
      confidence  : float 0-100
      p_benign    : float 0-100
      p_malignant : float 0-100
      unrelated   : bool
      uncertain   : bool  — True if prediction is low-confidence (< 60%)
    """
    h = _img_hash(image_bytes)
    cached = _cache_get(_predict_cache, h)
    if cached is not None:
        return cached

    model = load_cnn()
    if model is None:
        return {'available': False, 'result': None, 'confidence': 0,
                'p_benign': 0, 'p_malignant': 0, 'unrelated': False, 'uncertain': False}

    try:
        arr   = _decode_image(image_bytes, model)
        probs = model.predict(arr, verbose=0)[0]

        if _model_n_out == 3:
            p_ben  = float(probs[0])
            p_mal  = float(probs[1])
            p_unrel = float(probs[2])
            pred   = int(np.argmax(probs))
            if pred == 2:
                result = {'available': True, 'result': None, 'unrelated': True,
                        'confidence': round(p_unrel * 100, 2),
                        'p_benign': round(p_ben * 100, 2),
                        'p_malignant': round(p_mal * 100, 2), 'uncertain': False}
                _cache_set(_predict_cache, h, result)
                return result
            res = pred
            conf   = round(float(probs[res]) * 100, 2)
            uncertain = conf < 60.0
            result = {'available': True, 'result': res, 'unrelated': False,
                    'confidence': conf,
                    'p_benign': round(p_ben * 100, 2),
                    'p_malignant': round(p_mal * 100, 2),
                    'uncertain': uncertain}
            _cache_set(_predict_cache, h, result)
            return result
        else:
            # ELEVATED THRESHOLD: Require 55% confidence for malignant (instead of 50%)
            p_mal = float(probs[0]) if probs.shape == (1,) else float(probs)
            p_ben = 1.0 - p_mal
            res = 1 if p_mal >= 0.55 else 0
            conf   = round((p_mal if res == 1 else p_ben) * 100, 2)
            uncertain = conf < 60.0
            result = {'available': True, 'result': res, 'unrelated': False,
                    'confidence': conf,
                    'p_benign': round(p_ben * 100, 2),
                    'p_malignant': round(p_mal * 100, 2),
                    'uncertain': uncertain}
            _cache_set(_predict_cache, h, result)
            return result

    except Exception as e:
        print(f"[AutoML-CNN] predict error: {e}")
        return {'available': False, 'result': None, 'confidence': 0,
                'p_benign': 0, 'p_malignant': 0, 'unrelated': False, 'uncertain': False, 'error': str(e)}


def cnn_available():
    """True if a valid model file exists on disk."""
    for path in [MODEL_PATH]:
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return True
    return False
