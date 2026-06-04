"""
Out-of-Distribution (OOD) Detector for BreastCare AI
=====================================================
Uses Mahalanobis distance to detect when input features are far from
the training data distribution — indicating the input may not be a
valid FNA breast tissue sample.

When OOD is detected:
- Prediction is flagged as "Uncertain"
- Doctor is warned not to rely on the AI result
- Prevents false malignant/benign results from unrelated images

Methods:
1. Mahalanobis distance (primary) — measures how many standard deviations
   the input is from the training mean in feature space
2. Feature range check (secondary) — checks if values are within
   observed training data min/max bounds
"""

import os
import pickle
import numpy as np

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OOD_PATH     = os.path.join(BASE_DIR, 'artifacts', 'ood_detector.pkl')

# Threshold: Mahalanobis distance above this = OOD
# ~95th percentile of training distances → 5% false OOD rate on real data
MAHAL_THRESHOLD = 7.0
RANGE_VIOLATIONS_THRESHOLD = 5  # allow up to 5 features slightly out of range


def build_ood_detector(X_train_scaled, X_train_raw, feature_names):
    """
    Build OOD detector from training data.
    Call this once after training the model.
    
    Args:
        X_train_scaled : np.ndarray — scaled training features
        X_train_raw    : np.ndarray — raw (unscaled) training features
        feature_names  : list of str
    """
    # Compute training distribution in scaled space
    mean_vec = np.mean(X_train_scaled, axis=0)
    
    # Covariance matrix (regularized to avoid singular matrix)
    cov = np.cov(X_train_scaled.T)
    cov += np.eye(cov.shape[0]) * 1e-6  # regularization

    try:
        inv_cov = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        inv_cov = np.linalg.pinv(cov)

    # Compute training distances (for threshold calibration)
    diffs = X_train_scaled - mean_vec
    train_distances = np.array([
        np.sqrt(d @ inv_cov @ d) for d in diffs
    ])

    # Set threshold at 97.5th percentile of training distances
    threshold = float(np.percentile(train_distances, 97.5))

    # Feature ranges from raw training data
    feat_min = np.min(X_train_raw, axis=0)
    feat_max = np.max(X_train_raw, axis=0)
    # Add 20% buffer to avoid flagging near-boundary valid samples
    buffer = (feat_max - feat_min) * 0.20
    feat_min = feat_min - buffer
    feat_max = feat_max + buffer

    detector = {
        'mean_vec':      mean_vec,
        'inv_cov':       inv_cov,
        'threshold':     threshold,
        'feat_min':      feat_min,
        'feat_max':      feat_max,
        'feature_names': feature_names,
        'train_dist_p50': float(np.percentile(train_distances, 50)),
        'train_dist_p95': float(np.percentile(train_distances, 95)),
    }

    with open(OOD_PATH, 'wb') as f:
        pickle.dump(detector, f)

    print(f"[OOD] Detector built. Threshold: {threshold:.2f} "
          f"(p50={detector['train_dist_p50']:.2f}, p95={detector['train_dist_p95']:.2f})")
    return detector


def load_ood_detector():
    """Load OOD detector from disk."""
    if not os.path.exists(OOD_PATH):
        return None
    with open(OOD_PATH, 'rb') as f:
        return pickle.load(f)


def check_ood(feat_dict, scaler, feature_names):
    """
    Check if input features are out-of-distribution.

    Args:
        feat_dict     : dict of {feature_name: value}
        scaler        : fitted StandardScaler
        feature_names : list of feature names in order

    Returns:
        dict:
          is_ood       : bool
          distance     : float — Mahalanobis distance
          threshold    : float
          confidence   : float 0-100 (how in-distribution, 100=definitely in)
          reason       : str — human-readable explanation
          violations   : list of out-of-range features
    """
    detector = load_ood_detector()
    if detector is None:
        return {
            'is_ood': False, 'distance': 0, 'threshold': 0,
            'confidence': 100, 'reason': 'OOD detector not available.',
            'violations': []
        }

    # Build feature vector in correct order
    x_raw = np.array([feat_dict.get(k, 0) for k in feature_names], dtype=float)

    # Scale features
    try:
        x_scaled = scaler.transform(x_raw.reshape(1, -1))[0]
    except Exception:
        return {'is_ood': True, 'distance': 999, 'threshold': detector['threshold'],
                'confidence': 0, 'reason': 'Feature scaling failed.', 'violations': []}

    # ── Mahalanobis distance ───────────────────────────────────────────────────
    diff = x_scaled - detector['mean_vec']
    try:
        dist = float(np.sqrt(diff @ detector['inv_cov'] @ diff))
    except Exception:
        dist = 999.0

    threshold = detector['threshold']
    is_ood_mahal = dist > threshold

    # ── Feature range check ───────────────────────────────────────────────────
    violations = []
    for i, name in enumerate(feature_names):
        val = x_raw[i]
        if val < detector['feat_min'][i] or val > detector['feat_max'][i]:
            violations.append(name)

    is_ood_range = len(violations) > RANGE_VIOLATIONS_THRESHOLD

    is_ood = is_ood_mahal or is_ood_range

    # Confidence score: 100 = center of distribution, 0 = far outside
    # Based on ratio of distance to threshold
    if dist <= threshold:
        confidence = round(100 * (1 - dist / (threshold * 1.5)), 1)
        confidence = max(50.0, min(100.0, confidence))
    else:
        confidence = round(max(0, 100 * (1 - (dist - threshold) / threshold)), 1)
        confidence = max(0.0, min(45.0, confidence))

    # Build reason
    if is_ood_mahal and is_ood_range:
        reason = (f"Features are far outside the training distribution "
                  f"(distance={dist:.1f}, threshold={threshold:.1f}) "
                  f"and {len(violations)} feature(s) are out of expected range.")
    elif is_ood_mahal:
        reason = (f"Feature values are statistically unusual "
                  f"(Mahalanobis distance={dist:.1f} > threshold={threshold:.1f}). "
                  f"This may indicate an unrelated image was used.")
    elif is_ood_range:
        reason = (f"{len(violations)} feature(s) are outside the normal range "
                  f"observed in training data: {', '.join(violations[:5])}.")
    else:
        reason = f"Features are within normal distribution (distance={dist:.1f})."

    return {
        'is_ood':     is_ood,
        'distance':   round(dist, 2),
        'threshold':  round(threshold, 2),
        'confidence': confidence,
        'reason':     reason,
        'violations': violations
    }
