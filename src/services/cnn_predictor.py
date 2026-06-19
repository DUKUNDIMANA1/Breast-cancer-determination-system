"""
CNN Predictor — BreastCare AI
==============================
Uses the IDC-trained binary MobileNetV2 model.

Model output:
  sigmoid probability p in [0, 1]
  p < 0.5  → Benign  (IDC-negative)
  p >= 0.5 → Malignant (IDC-positive)

Two public functions:
  cnn_validate_image(image_bytes) → is this a real tissue slide?
  cnn_predict_image(image_bytes)  → Benign (0) or Malignant (1)?

If TensorFlow is not installed, validation falls back to a lightweight
heuristic so the app stays usable on Render free tier.
"""

import os
import numpy as np

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH      = os.path.join(BASE_DIR, 'artifacts', 'cnn_model.h5')
CHECKPOINT_PATH = os.path.join(BASE_DIR, 'artifacts', 'cnn_best.keras')
IMG_SIZE        = 50

# Sigmoid threshold — images below this are Benign, above are Malignant
THRESHOLD = 0.5

# Images whose sigmoid probability sits in this uncertainty band
# are likely not tissue (unrelated images hover near 0.5)
UNCERTAIN_LOW  = 0.35
UNCERTAIN_HIGH = 0.65

_cnn_model     = None
_model_is_binary = True   # binary sigmoid model by default


def load_cnn():
    """Load model lazily on first use. Returns None if TF unavailable."""
    global _cnn_model, _model_is_binary
    if _cnn_model is not None:
        return _cnn_model

    try:
        import tensorflow as tf
    except ImportError:
        print("[CNN] TensorFlow not installed — using heuristic fallback.")
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
            # Detect binary vs 3-class
            out_shape = _cnn_model.output_shape
            n_out = out_shape[-1] if len(out_shape) > 1 else 1
            _model_is_binary = (n_out == 1)
            print(f"[CNN] Model loaded from {os.path.basename(path)} "
                  f"({'binary sigmoid' if _model_is_binary else f'{n_out}-class softmax'}).")
            return _cnn_model
        except Exception as e:
            print(f"[CNN] Could not load {os.path.basename(path)}: {e}")

    print("[CNN] No valid model — heuristic fallback active.")
    return None


def _decode_image(image_bytes):
    """Decode bytes → normalised numpy array (1, IMG_SIZE, IMG_SIZE, 3)."""
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


def _he_stain_check(image_bytes):
    """
    Check for H&E (haematoxylin & eosin) staining — the hallmark of
    histopathology slides.  Returns (passes: bool, detail: str).

    Criteria (ALL must be met):
      1. Eosin pink  > 8%   — pink tissue regions
      2. Haematoxylin purple > 5% — blue/purple nuclei
      3. Cyan (water/sky) < 15%  — reject landscape/water photos
      4. Texture (Laplacian) > 200 — fine cellular structure
      5. White/overexposed < 35%  — reject documents/screenshots
      6. Not a natural colour photo (skin, food, objects)
         — dominated by neither pure red nor pure green
    """
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, "Could not decode image"

        # Work at original resolution for accuracy, then resize
        if img.shape[0] > 200:
            img = cv2.resize(img, (200, 200))

        rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(float)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]

        # ── H&E colour features ───────────────────────────────────────────────
        # Eosin pink: R dominant, moderate G and B
        pink   = float(np.mean((r > 160) & (g > 80) & (b > 100) & (r > g) & (r > b * 1.1)))
        # Haematoxylin purple: B > G, moderate R (exclude cyan = sky/water)
        purple = float(np.mean((b > 120) & (b > g * 1.2) & (r > 50) & (r < 200) & (g < 170)))
        # Cyan rejection (water, sky, pool)
        cyan   = float(np.mean((b > 120) & (g > 110) & (r < 130)))
        # Texture — cellular structure has high Laplacian variance
        lap    = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # Over-bright/white (documents, screenshots)
        white  = float(np.mean((r > 220) & (g > 220) & (b > 220)))
        # Pure red objects (red objects, tomatoes, red fabric)
        red_obj = float(np.mean((r > 180) & (g < 80) & (b < 80)))
        # Pure green (plants, grass, leaves)
        green_obj = float(np.mean((g > 140) & (r < 100) & (b < 100)))
        # Dark brown (wood, soil) — common in natural photos
        brown  = float(np.mean((r > 80) & (r < 180) & (g > 40) & (g < 130) & (b < 80) & (r > g * 1.2)))
        # Skin tone detection: reddish, medium brightness, low saturation variance
        hsv    = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(float)
        skin   = float(np.mean((hsv[:,:,0] > 0) & (hsv[:,:,0] < 25) &
                               (hsv[:,:,1] > 20) & (hsv[:,:,1] < 170) &
                               (hsv[:,:,2] > 80)))

        # ── Dominant channel check (blue/cyan dominant = water/sky) ──────────
        mean_r = float(r.mean())
        mean_g = float(g.mean())
        mean_b = float(b.mean())
        # Blue-dominant: overall image is more blue/cyan than pink/purple
        blue_dominant = (mean_b > mean_r * 1.15) and (mean_b > 100)
        # Also check: if blue channel mean is high and cyan fraction is significant
        pool_like = blue_dominant and cyan > 0.08

        detail = (f"pink={pink:.0%}, purple={purple:.0%}, cyan={cyan:.0%}, "
                  f"texture={lap:.0f}, white={white:.0%}, red={red_obj:.0%}, "
                  f"green={green_obj:.0%}, skin={skin:.0%}, "
                  f"blue_dom={blue_dominant}(R={mean_r:.0f},G={mean_g:.0f},B={mean_b:.0f})")

        # All conditions must pass
        passes = (
            (pink > 0.08 or purple > 0.15) and  # eosin OR dense nuclei
            purple     > 0.05 and   # haematoxylin nuclei required
            cyan       < 0.12 and   # reject water/sky (tightened from 0.15)
            not pool_like     and   # reject pool/water photos
            white      < 0.35 and   # reject documents
            lap        > 200  and   # cellular texture required
            red_obj    < 0.10 and   # reject red objects
            green_obj  < 0.10 and   # reject plants/grass
            skin       < 0.50       # reject skin/face photos
        )
        return passes, detail
    except Exception as e:
        return True, f"H&E check skipped ({e})"


def _heuristic_validate(image_bytes):
    """Fallback when CNN is unavailable. Returns (is_valid, confidence, reason)."""
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, "Could not decode image file."
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        bright = float(img.mean())
        std    = float(gray.std())
        if bright > 245 and std < 5:
            return False, 0.0, "Image appears blank."
        if bright < 5:
            return False, 0.0, "Image is completely black."
        if std < 3:
            return False, 0.0, "Image has no variation (solid colour)."
        return True, 0.5, "Accepted (heuristic — CNN unavailable)."
    except Exception as e:
        return True, 0.5, f"Heuristic check skipped ({e})."


# ── Public API ────────────────────────────────────────────────────────────────

def cnn_validate_image(image_bytes):
    """
    Decide whether an image is a valid histopathology tissue slide.

    Returns dict:
      is_valid    : bool
      confidence  : float 0-100
      reason      : str
      cnn_used    : bool
    """
    model = load_cnn()

    if model is None:
        valid, conf, reason = _heuristic_validate(image_bytes)
        return {'is_valid': valid, 'confidence': round(conf*100,1),
                'reason': reason, 'cnn_used': False}

    try:
        arr   = _decode_image(image_bytes)
        probs = model.predict(arr, verbose=0)[0]

        if _model_is_binary:
            # Binary sigmoid model
            p_mal = float(probs[0]) if probs.shape == (1,) else float(probs)
            p_ben = 1.0 - p_mal

            # H&E stain check first
            he_ok, he_detail = _he_stain_check(image_bytes)
            if not he_ok:
                return {
                    'is_valid':   False,
                    'confidence': round(max(p_ben, p_mal) * 100, 1),
                    'reason': (f"Image rejected: not a valid H&E histopathology slide. "
                               f"{he_detail}. Upload an H&E stained breast tissue image."),
                    'cnn_used': True,
                }

            # Uncertainty zone — model hovering near 0.5 means unrelated image
            if UNCERTAIN_LOW <= p_mal <= UNCERTAIN_HIGH:
                return {
                    'is_valid':   False,
                    'confidence': round(max(p_ben, p_mal) * 100, 1),
                    'reason': (f"Image rejected: CNN uncertain (p={p_mal:.3f}). "
                               f"Does not look like breast tissue. "
                               f"Upload an H&E stained slide."),
                    'cnn_used': True,
                }

            label = "Malignant" if p_mal >= THRESHOLD else "Benign"
            conf  = round(max(p_ben, p_mal) * 100, 1)
            return {
                'is_valid':   True,
                'confidence': conf,
                'reason':     f"Valid tissue slide — CNN: {label} ({conf:.0f}%). {he_detail}.",
                'cnn_used':   True,
            }

        else:
            # 3-class softmax
            p_ben, p_mal, p_unrel = float(probs[0]), float(probs[1]), float(probs[2])
            pred = int(np.argmax(probs))
            he_ok, he_detail = _he_stain_check(image_bytes)

            # Reject if CNN says unrelated OR H&E check fails OR unrelated is dominant secondary
            unrel_dominant = p_unrel > 0.25  # unrelated gets >25% — suspicious
            if pred == 2 or not he_ok or unrel_dominant:
                return {
                    'is_valid':   False,
                    'confidence': round(max(p_ben, p_mal) * 100, 1),
                    'reason': (f"Image rejected: not a valid H&E histopathology slide. "
                               f"CNN={['Benign','Malignant','Unrelated'][pred]} "
                               f"(B={p_ben:.0%}, M={p_mal:.0%}, U={p_unrel:.0%}). "
                               f"{he_detail}. Upload an H&E stained tissue slide."),
                    'cnn_used': True,
                }
            label = "Benign" if pred == 0 else "Malignant"
            conf  = round(probs[pred] * 100, 1)
            return {
                'is_valid':   True,
                'confidence': conf,
                'reason':     f"Valid tissue — CNN: {label} ({conf:.0f}%). {he_detail}.",
                'cnn_used':   True,
            }

    except Exception as e:
        print(f"[CNN] validate error: {e}")
        valid, conf, reason = _heuristic_validate(image_bytes)
        return {'is_valid': valid, 'confidence': round(conf*100,1),
                'reason': f"CNN error ({e}); fallback: {reason}", 'cnn_used': False}


def cnn_predict_image(image_bytes):
    """
    Classify image as Benign (0) or Malignant (1) using the IDC CNN model.

    Returns dict:
      available   : bool
      result      : 0 or 1 (None if unavailable / unrelated)
      confidence  : float 0-100
      probability : float (raw sigmoid or softmax probability for result class)
      unrelated   : bool (True if image is not tissue — only for 3-class model)
    """
    model = load_cnn()
    if model is None:
        return {'available': False, 'result': None, 'confidence': 0,
                'probability': 0, 'unrelated': False}

    try:
        arr   = _decode_image(image_bytes)
        probs = model.predict(arr, verbose=0)[0]

        if _model_is_binary:
            p_mal = float(probs[0]) if probs.shape == (1,) else float(probs)
            p_ben = 1.0 - p_mal
            result = 1 if p_mal >= THRESHOLD else 0
            conf   = round((p_mal if result == 1 else p_ben) * 100, 2)
            return {
                'available':   True,
                'result':      result,
                'confidence':  conf,
                'probability': round(p_mal, 4),
                'p_benign':    round(p_ben * 100, 2),
                'p_malignant': round(p_mal * 100, 2),
                'unrelated':   False,
            }
        else:
            # 3-class
            p_ben, p_mal, p_unrel = float(probs[0]), float(probs[1]), float(probs[2])
            pred = int(np.argmax(probs))
            if pred == 2:
                return {'available': True, 'result': None, 'confidence': round(p_unrel*100,2),
                        'probability': round(p_unrel,4), 'unrelated': True,
                        'p_benign': round(p_ben*100,2), 'p_malignant': round(p_mal*100,2)}
            result = pred
            conf   = round(probs[result] * 100, 2)
            return {
                'available':   True,
                'result':      result,
                'confidence':  conf,
                'probability': round(float(probs[result]), 4),
                'p_benign':    round(p_ben * 100, 2),
                'p_malignant': round(p_mal * 100, 2),
                'unrelated':   False,
            }

    except Exception as e:
        print(f"[CNN] predict error: {e}")
        return {'available': False, 'result': None, 'confidence': 0,
                'probability': 0, 'unrelated': False, 'error': str(e)}


def cnn_available():
    """True if a valid model file exists on disk."""
    for path in [MODEL_PATH, CHECKPOINT_PATH]:
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return True
    return False
