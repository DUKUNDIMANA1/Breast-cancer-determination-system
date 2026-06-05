"""
CNN Predictor — BreastCare AI
==============================
Two roles:
  1. cnn_validate_image()  — gate keeper: is this a tissue image at all?
  2. cnn_predict_image()   — classifier: Benign (0) or Malignant (1)?

Both use the same MobileNetV2 model trained on the merged dataset
(IDC histopathology patches + Wisconsin CSV heatmaps).

Validation logic
----------------
The CNN outputs a probability p in [0, 1]:
  p ~ 0   → strongly Benign tissue
  p ~ 1   → strongly Malignant tissue
  p ~ 0.5 → uncertain / unrelated image

An unrelated image (cat, document, screenshot, etc.) has no tissue
features so the model is uncertain — its output hovers near 0.5.
We reject images where the raw probability is in the dead-zone
[UNCERTAIN_LOW, UNCERTAIN_HIGH], i.e. the model can't confidently
decide either way.

If the CNN model is not yet available (not trained), validation
falls back to a lightweight heuristic check so the app stays usable.
"""

import os
import numpy as np

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH      = os.path.join(BASE_DIR, 'artifacts', 'cnn_model.h5')
CHECKPOINT_PATH = os.path.join(BASE_DIR, 'artifacts', 'cnn_best.keras')
IMG_SIZE   = 50

# Images whose raw CNN probability falls in this range are considered
# "uncertain" = likely unrelated to breast tissue.
UNCERTAIN_LOW  = 0.35
UNCERTAIN_HIGH = 0.65

_cnn_model = None


def load_cnn():
    """Load CNN model lazily on first use. Tries .h5 then .keras checkpoint."""
    global _cnn_model
    if _cnn_model is not None:
        return _cnn_model

    import tensorflow as tf

    # Try primary .h5 path first
    for path in [MODEL_PATH, CHECKPOINT_PATH]:
        if not os.path.exists(path):
            continue
        if os.path.getsize(path) < 1000:   # corrupt / empty file
            print(f"[CNN] Skipping {os.path.basename(path)} — file is empty/corrupt.")
            continue
        try:
            _cnn_model = tf.keras.models.load_model(path)
            print(f"[CNN] Model loaded from {os.path.basename(path)}.")
            return _cnn_model
        except Exception as e:
            print(f"[CNN] Could not load {os.path.basename(path)}: {e}")

    print("[CNN] No valid model found — validation will use heuristic fallback.")
    return None


def _decode_and_resize(image_bytes):
    """Decode image bytes → normalised (1, IMG_SIZE, IMG_SIZE, 3) array."""
    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — unsupported format or corrupted file.")
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)   # (1, 50, 50, 3)


def _heuristic_validate(image_bytes):
    """
    Lightweight heuristic fallback used when CNN model is not available.
    Only blocks obviously wrong images — keeps false-reject rate very low.

    Returns (is_valid: bool, confidence: float 0-1, reason: str)
    """
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, "Could not decode the image file. Make sure it is a valid JPG or PNG."

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        r = img_rgb[:, :, 0].astype(float)
        g = img_rgb[:, :, 1].astype(float)
        b = img_rgb[:, :, 2].astype(float)

        brightness  = float((r.mean() + g.mean() + b.mean()) / 3)
        overall_std = float(gray.astype(float).std())

        # Only block completely blank / pure-white images
        if brightness > 245 and overall_std < 5:
            return False, 0.0, "Image appears to be blank or empty."

        # Only block completely black images
        if brightness < 5:
            return False, 0.0, "Image is completely black — no content detected."

        # Completely flat colour (solid block) with zero variation
        if overall_std < 3:
            return False, 0.0, "Image has no variation — appears to be a solid colour block."

        # Accept everything else — let the CNN decide on next request
        return True, 0.5, "Image accepted (heuristic fallback — CNN not yet loaded)."

    except Exception as e:
        # On any error, accept the image and let feature extraction handle it
        return True, 0.5, f"Heuristic check skipped ({e}). Image accepted."


def cnn_validate_image(image_bytes):
    """
    Use the trained CNN to decide whether an image is valid breast tissue.

    Returns
    -------
    dict:
      is_valid    : bool   — True if the image looks like breast tissue
      confidence  : float  — 0-100, how confident the model is
      raw_prob    : float  — raw sigmoid output (0=benign, 1=malignant, ~0.5=uncertain)
      reason      : str    — human-readable explanation
      cnn_used    : bool   — False when falling back to heuristics
    """
    model = load_cnn()

    # ── CNN not available → heuristic fallback ────────────────────────────────
    if model is None:
        valid, conf, reason = _heuristic_validate(image_bytes)
        return {
            'is_valid':   valid,
            'confidence': round(conf * 100, 1),
            'raw_prob':   None,
            'reason':     reason,
            'cnn_used':   False,
        }

    # ── CNN available ─────────────────────────────────────────────────────────
    try:
        img_arr   = _decode_and_resize(image_bytes)
        probs     = model.predict(img_arr, verbose=0)[0]   # shape (3,) or (1,)
        n_classes = len(probs)

        if n_classes == 3:
            # 3-class model: 0=Benign, 1=Malignant, 2=Unrelated
            p_benign, p_malignant, p_unrelated = float(probs[0]), float(probs[1]), float(probs[2])
            predicted_class = int(np.argmax(probs))

            # ── Histopathology colour check (H&E staining requirement) ────────
            # Real H&E tissue slides have characteristic pink (eosin) and
            # purple/blue (haematoxylin) tones. We check for these BEFORE
            # accepting, as an independent second layer on top of the CNN.
            import cv2 as _cv2
            _nparr = np.frombuffer(image_bytes, np.uint8)
            _img   = _cv2.imdecode(_nparr, _cv2.IMREAD_COLOR)
            _he_pass = False
            _he_reason = ""
            if _img is not None:
                _rgb = _cv2.cvtColor(_img, _cv2.COLOR_BGR2RGB).astype(float)
                _r, _g, _b = _rgb[:,:,0], _rgb[:,:,1], _rgb[:,:,2]
                # Pink (eosin): high R, moderate G and B, R > G
                _pink   = float(np.mean((_r > 140) & (_g > 60) & (_b > 80) & (_r > _g)))
                # Purple/blue (haematoxylin): B dominant over G, moderate R
                _purple = float(np.mean((_b > 90) & (_b > _g * 1.05) & (_r > 50)))
                # Laplacian variance — texture (tissue slides are always textured)
                _gray   = _cv2.cvtColor(_img, _cv2.COLOR_BGR2GRAY)
                _lap    = float(_cv2.Laplacian(_gray, _cv2.CV_64F).var())
                # Require: meaningful pink OR purple AND some texture
                _he_pass = (_pink > 0.04 or _purple > 0.04) and _lap > 50
                _he_reason = (f"H&E pink={_pink:.0%}, purple={_purple:.0%}, "
                              f"texture={_lap:.0f}")

            # Minimum CNN confidence required to accept as tissue
            TISSUE_MIN_CONF = 0.65   # 65% — must clearly win over other classes

            if predicted_class == 2:
                # CNN explicitly says unrelated
                is_valid   = False
                confidence = round(p_unrelated * 100, 1)
                reason = (
                    f"Image rejected: not a histopathology slide "
                    f"(CNN: Unrelated={p_unrelated:.0%}, "
                    f"Benign={p_benign:.0%}, Malignant={p_malignant:.0%}). "
                    f"Upload an H&E stained breast tissue slide."
                )
            elif max(p_benign, p_malignant) < TISSUE_MIN_CONF:
                # CNN not confident enough → reject
                is_valid   = False
                confidence = round(max(p_benign, p_malignant) * 100, 1)
                reason = (
                    f"Image rejected: CNN confidence too low for histopathology "
                    f"({confidence:.0f}%, need ≥{TISSUE_MIN_CONF*100:.0f}%). "
                    f"Benign={p_benign:.0%}, Malignant={p_malignant:.0%}, "
                    f"Unrelated={p_unrelated:.0%}. "
                    f"Upload a clear H&E stained breast tissue slide."
                )
            elif not _he_pass:
                # CNN confident but no H&E staining detected → reject
                is_valid   = False
                confidence = round(max(p_benign, p_malignant) * 100, 1)
                reason = (
                    f"Image rejected: H&E staining not detected "
                    f"({_he_reason}). "
                    f"Only haematoxylin & eosin stained histopathology images "
                    f"are accepted."
                )
            else:
                # Both CNN and H&E check pass → accept
                is_valid   = True
                label      = "Benign" if p_benign > p_malignant else "Malignant"
                confidence = round(max(p_benign, p_malignant) * 100, 1)
                reason = (
                    f"Valid histopathology slide accepted "
                    f"({label}, CNN={confidence:.0f}%, {_he_reason})."
                )

            return {
                'is_valid':   is_valid,
                'confidence': confidence,
                'raw_prob':   round(float(probs[predicted_class]), 4),
                'reason':     reason,
                'cnn_used':   True,
            }
        else:
            # Legacy binary model: use uncertainty zone
            raw_prob = float(probs[0]) if n_classes == 1 else float(probs[1])
            is_uncertain = UNCERTAIN_LOW <= raw_prob <= UNCERTAIN_HIGH
            is_valid     = not is_uncertain
            distance_from_centre = abs(raw_prob - 0.5)
            confidence = round(min(distance_from_centre / 0.5 * 100, 100), 1)
            if is_uncertain:
                reason = (
                    f"CNN uncertain (prob={raw_prob:.3f}). "
                    f"Image does not appear to be breast tissue."
                )
            else:
                label  = "Malignant" if raw_prob >= 0.5 else "Benign"
                reason = f"CNN: {label} tissue (prob={raw_prob:.3f})."
            return {
                'is_valid':   is_valid,
                'confidence': confidence,
                'raw_prob':   round(raw_prob, 4),
                'reason':     reason,
                'cnn_used':   True,
            }
    except Exception as e:
        print(f"[CNN] Validation error: {e}")
        valid, conf, reason = _heuristic_validate(image_bytes)
        return {
            'is_valid':   valid,
            'confidence': round(conf * 100, 1),
            'raw_prob':   None,
            'reason':     f"CNN error ({e}); heuristic fallback: {reason}",
            'cnn_used':   False,
        }


def cnn_predict_image(image_bytes):
    """
    Predict Benign (0) or Malignant (1) from raw image bytes.

    Returns
    -------
    dict:
      result     : 0 (Benign) or 1 (Malignant)
      confidence : float 0-100
      available  : bool — False if CNN model not loaded
      raw_prob   : float sigmoid output
    """
    model = load_cnn()
    if model is None:
        return {'available': False, 'result': None, 'confidence': 0}

    try:
        img_arr = _decode_and_resize(image_bytes)
        probs   = model.predict(img_arr, verbose=0)[0]
        n_classes = len(probs)

        if n_classes == 3:
            # 3-class: class 2 = unrelated, classes 0/1 = tissue
            predicted = int(np.argmax(probs))
            if predicted == 2:
                # Unrelated — return unavailable so caller knows to reject
                return {
                    'available':  True,
                    'result':     None,
                    'confidence': round(float(probs[2]) * 100, 2),
                    'raw_prob':   round(float(probs[2]), 4),
                    'unrelated':  True,
                }
            result = predicted   # 0 or 1
            conf   = round(float(probs[result]) * 100, 2)
        else:
            raw_prob = float(probs[0]) if n_classes == 1 else float(probs[1])
            result   = 1 if raw_prob >= 0.5 else 0
            conf     = round((raw_prob if result == 1 else 1 - raw_prob) * 100, 2)

        return {
            'available':  True,
            'result':     result,
            'confidence': conf,
            'raw_prob':   round(float(probs[result]), 4),
            'unrelated':  False,
        }
    except Exception as e:
        print(f"[CNN] Prediction error: {e}")
        return {'available': False, 'result': None, 'confidence': 0, 'error': str(e)}


def cnn_available():
    """Return True if a valid CNN model file exists on disk."""
    for path in [MODEL_PATH, CHECKPOINT_PATH]:
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return True
    return False
