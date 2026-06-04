"""
CNN Predictor — classifies tissue images as Benign or Malignant.
Loaded once at startup; used by the Flask app for image-based predictions.
"""

import os
import numpy as np

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, 'artifacts', 'cnn_model.h5')
IMG_SIZE   = 50

_cnn_model = None

def load_cnn():
    """Load CNN model lazily on first use."""
    global _cnn_model
    if _cnn_model is not None:
        return _cnn_model
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        import tensorflow as tf
        _cnn_model = tf.keras.models.load_model(MODEL_PATH)
        print("[CNN] Model loaded successfully.")
        return _cnn_model
    except Exception as e:
        print(f"[CNN] Failed to load model: {e}")
        return None

def cnn_predict_image(image_bytes):
    """
    Predict Benign/Malignant from raw image bytes.

    Returns:
        dict with keys:
          result     : 0 (Benign) or 1 (Malignant)
          confidence : float 0-100
          available  : bool — False if CNN model not loaded
    """
    model = load_cnn()
    if model is None:
        return {'available': False, 'result': None, 'confidence': 0}

    try:
        import cv2
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")

        # Resize and normalize
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)  # (1, 50, 50, 3)

        # Predict
        prob      = float(model.predict(img, verbose=0)[0][0])
        result    = 1 if prob >= 0.5 else 0
        confidence= prob * 100 if result == 1 else (1 - prob) * 100

        return {
            'available':  True,
            'result':     result,
            'confidence': round(confidence, 2),
            'raw_prob':   round(prob, 4)
        }
    except Exception as e:
        print(f"[CNN] Prediction error: {e}")
        return {'available': False, 'result': None, 'confidence': 0, 'error': str(e)}

def cnn_available():
    """Return True if CNN model is loaded and ready."""
    return os.path.exists(MODEL_PATH)
