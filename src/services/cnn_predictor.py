"""
CNN Predictor — BreastCare AI
==============================
Uses the 2-class MobileNetV2 model trained on IDC histopathology patches.

Classes:
  0 = Benign  (IDC-negative tissue)
  1 = Malignant (IDC-positive tissue)

Validation rule:
  - Only class 0 and 1 images are accepted
  - Confidence must be above minimum threshold

If TensorFlow is not installed, falls back to a lightweight
heuristic (blank/black/solid colour rejection only).
"""

import os
import numpy as np

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH      = os.path.join(BASE_DIR, 'artifacts', 'cnn_model.h5')
CHECKPOINT_PATH = os.path.join(BASE_DIR, 'artifacts', 'cnn_best.keras')
IMG_SIZE        = 50

# Minimum CNN confidence to accept as tissue (class 0 or 1)
TISSUE_MIN_CONF = 0.45   # 45% — low enough to accept most real tissue patches

_cnn_model    = None
_model_n_out  = 3   # default assume 3-class


def load_cnn():
    """Load model lazily. Returns None if TF unavailable."""
    global _cnn_model, _model_n_out
    if _cnn_model is not None:
        return _cnn_model

    try:
        import tensorflow as tf
    except ImportError:
        print("[CNN] TensorFlow not installed — heuristic fallback active.")
        return None
    except Exception as e:
        print(f"[CNN] TensorFlow import error: {e}")
        return None

    for path in [MODEL_PATH, CHECKPOINT_PATH]:
        if not os.path.exists(path):
            continue
        if os.path.getsize(path) < 1000:
            print(f"[CNN] Skipping {os.path.basename(path)} — empty/corrupt.")
            continue
        try:
            _cnn_model = tf.keras.models.load_model(path)
            out_shape  = _cnn_model.output_shape
            _model_n_out = out_shape[-1] if len(out_shape) > 1 else 1
            kind = f"{_model_n_out}-class softmax" if _model_n_out > 1 else "binary sigmoid"
            print(f"[CNN] Model loaded from {os.path.basename(path)} ({kind}).")
            return _cnn_model
        except Exception as e:
            print(f"[CNN] Could not load {os.path.basename(path)}: {e}")

    print("[CNN] No valid model — heuristic fallback active.")
    return None


def _decode_image(image_bytes):
    """Decode bytes → normalised (1, IMG_SIZE, IMG_SIZE, 3) array."""
    try:
        import cv2
    except ImportError:
        raise RuntimeError("opencv-python-headless not installed")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — unsupported format or corrupted file.")
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)


def _colour_sanity(image_bytes):
    """
    Fast colour sanity check — rejects obviously non-tissue images.
    Only catches clear-cut cases: pure green, pure blue, dominant skin,
    cyan water, pure red. Does NOT reject complex real-world images.
    Returns (passes: bool, reason: str)
    """
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, "Could not decode image"

        if img.shape[0] > 200:
            img = cv2.resize(img, (200, 200))

        rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(float)
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        mean_r, mean_g, mean_b = float(r.mean()), float(g.mean()), float(b.mean())

        # Pure green (grass, plants): green dominant by large margin
        if mean_g > mean_r * 1.3 and mean_g > mean_b * 1.2 and mean_g > 80:
            return False, f"Rejected: green-dominant image (R={mean_r:.0f}, G={mean_g:.0f}, B={mean_b:.0f})"

        # Cyan/blue water or sky: blue+green >> red
        cyan_frac = float(np.mean((b > 120) & (g > 100) & (r < 130)))
        if cyan_frac > 0.20:
            return False, f"Rejected: cyan/water image (cyan fraction={cyan_frac:.0%})"

        # Blue dominant (sky, water)
        if mean_b > mean_r * 1.3 and mean_b > mean_g * 1.1 and mean_b > 80:
            return False, f"Rejected: blue-dominant image (R={mean_r:.0f}, G={mean_g:.0f}, B={mean_b:.0f})"

        # Pure red objects
        red_frac = float(np.mean((r > 180) & (g < 80) & (b < 80)))
        if red_frac > 0.15:
            return False, f"Rejected: red-dominant image (red fraction={red_frac:.0%})"

        # Skin-dominant (uniform orange-pink, low variation — face/body closeup)
        hsv   = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(float)
        skin  = float(np.mean((hsv[:,:,0] >= 0) & (hsv[:,:,0] <= 20) &
                               (hsv[:,:,1] >= 30) & (hsv[:,:,1] <= 200) &
                               (hsv[:,:,2] >= 80)))
        gray  = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        lap   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # Skin photo: high skin fraction AND low texture (smooth skin)
        if skin > 0.55 and lap < 500:
            return False, f"Rejected: skin-tone dominant image (skin={skin:.0%}, texture={lap:.0f})"

        return True, "Colour sanity passed"
    except Exception as e:
        return True, f"Colour check skipped ({e})"


def cnn_validate_image(image_bytes):
    """
    Validate whether an image is a tissue slide using the CNN only.

    Returns dict:
      is_valid    : bool
      confidence  : float 0-100
      reason      : str
      cnn_used    : bool
    """
    model = load_cnn()

    if model is None:
        valid, conf, reason = _heuristic_validate(image_bytes)
        return {'is_valid': valid, 'confidence': conf, 'reason': reason, 'cnn_used': False}

    try:
        arr   = _decode_image(image_bytes)
        probs = model.predict(arr, verbose=0)[0]

        if _model_n_out == 3:
            # 3-class: 0=Benign, 1=Malignant, 2=Unrelated
            p_ben, p_mal, p_unrel = float(probs[0]), float(probs[1]), float(probs[2])
            pred = int(np.argmax(probs))
            tissue_conf = max(p_ben, p_mal)

            # Reject all object images (class 2) and low-confidence tissue images
            if pred == 2 or tissue_conf < TISSUE_MIN_CONF:
                return {
                    'is_valid':   False,
                    'confidence': round(max(p_unrel, tissue_conf) * 100, 1),
                    'reason':     (f"Image rejected: Not a valid tissue image "
                                   f"(Unrelated={p_unrel:.0%}, Tissue confidence={tissue_conf:.0%}). "
                                   f"Only clear tissue images are accepted for feature extraction."),
                    'cnn_used':   True,
                }
            label = "Benign" if pred == 0 else "Malignant"
            conf  = round(tissue_conf * 100, 1)
            return {
                'is_valid':   True,
                'confidence': conf,
                'reason':     (f"Valid tissue image — CNN: {label} "
                               f"(Benign={p_ben:.0%}, Malignant={p_mal:.0%})."),
                'cnn_used':   True,
            }

        else:
            # Binary sigmoid: 0=Benign, 1=Malignant
            p_mal = float(probs[0]) if probs.shape == (1,) else float(probs)
            p_ben = 1.0 - p_mal
            # Reject uncertain images (likely objects or non-tissue)
            if 0.35 <= p_mal <= 0.65:
                return {
                    'is_valid':   False,
                    'confidence': round(max(p_ben, p_mal) * 100, 1),
                    'reason':     (f"Image rejected: CNN uncertain (p_mal={p_mal:.3f}). "
                                   f"Does not look like breast tissue. "
                                   f"Only clear tissue images are accepted for feature extraction."),
                    'cnn_used':   True,
                }
            label = "Malignant" if p_mal >= 0.5 else "Benign"
            conf  = round(max(p_ben, p_mal) * 100, 1)
            return {
                'is_valid':   True,
                'confidence': conf,
                'reason':     f"Valid tissue — CNN: {label} ({conf:.0f}%).",
                'cnn_used':   True,
            }

    except Exception as e:
        print(f"[CNN] validate error: {e}")
        valid, conf, reason = _heuristic_validate(image_bytes)
        return {'is_valid': valid, 'confidence': conf,
                'reason': f"CNN error ({e}); fallback: {reason}", 'cnn_used': False}


def cnn_predict_image(image_bytes):
    """
    Predict Benign (0) or Malignant (1) from image bytes.

    Returns dict:
      available   : bool
      result      : 0=Benign, 1=Malignant, None if unrelated/unavailable
      confidence  : float 0-100
      p_benign    : float 0-100
      p_malignant : float 0-100
      unrelated   : bool
    """
    model = load_cnn()
    if model is None:
        return {'available': False, 'result': None, 'confidence': 0,
                'p_benign': 0, 'p_malignant': 0, 'unrelated': False}

    try:
        arr   = _decode_image(image_bytes)
        probs = model.predict(arr, verbose=0)[0]

        if _model_n_out == 3:
            p_ben, p_mal, p_unrel = float(probs[0]), float(probs[1]), float(probs[2])
            pred = int(np.argmax(probs))
            # Only accept class 0 (Benign) and class 1 (Malignant)
            # Reject all object images (class 2)
            if pred == 2:
                return {'available': True, 'result': None, 'unrelated': True,
                        'confidence': round(p_unrel*100,2),
                        'p_benign': round(p_ben*100,2), 'p_malignant': round(p_mal*100,2),
                        'message': 'Object image rejected - only tissue images are accepted for prediction'}
            result = pred
            conf   = round(float(probs[result]) * 100, 2)
            return {'available': True, 'result': result, 'unrelated': False,
                    'confidence': conf,
                    'p_benign': round(p_ben*100,2), 'p_malignant': round(p_mal*100,2)}
        else:
            p_mal = float(probs[0]) if probs.shape == (1,) else float(probs)
            p_ben = 1.0 - p_mal
            result = 1 if p_mal >= 0.5 else 0
            conf   = round((p_mal if result == 1 else p_ben) * 100, 2)
            return {'available': True, 'result': result, 'unrelated': False,
                    'confidence': conf,
                    'p_benign': round(p_ben*100,2), 'p_malignant': round(p_mal*100,2)}

    except Exception as e:
        print(f"[CNN] predict error: {e}")
        return {'available': False, 'result': None, 'confidence': 0,
                'p_benign': 0, 'p_malignant': 0, 'unrelated': False, 'error': str(e)}


def cnn_available():
    """True if a valid model file exists on disk."""
    for path in [MODEL_PATH, CHECKPOINT_PATH]:
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return True
    return False
