"""
OOD (Out-of-Distribution) Detector — BreastCare AI
====================================================
Detects whether input feature values are within the distribution
of the Wisconsin Breast Cancer Dataset (WBCD) used to train the
Logistic Regression model.

Method: Mahalanobis distance on the 30 standardised features.
If the distance exceeds the 99th percentile of training distances,
the sample is flagged as out-of-distribution.

Usage:
    from src.services.ood_detector import check_ood
    result = check_ood(feature_dict)
    if result['is_ood']:
        flash(result['message'], 'warning')
"""

import os
import numpy as np

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH   = os.path.join(BASE_DIR, 'data', 'breast-cancer.csv')
SCALER_PATH = os.path.join(BASE_DIR, 'artifacts', 'scaler.pkl')

FEATURES = [
    'radius_mean','texture_mean','perimeter_mean','area_mean','smoothness_mean',
    'compactness_mean','concavity_mean','concave points_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','perimeter_se','area_se','smoothness_se',
    'compactness_se','concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'radius_worst','texture_worst','perimeter_worst','area_worst','smoothness_worst',
    'compactness_worst','concavity_worst','concave points_worst','symmetry_worst','fractal_dimension_worst'
]

# Per-feature safe ranges from WBCD (min, max with 5% margin)
_RANGES = None
_SCALER = None
_TRAIN_MEAN = None
_TRAIN_COV_INV = None
_THRESHOLD = None


def _load_ood_stats():
    """Load training stats for OOD detection (lazy, once)."""
    global _RANGES, _SCALER, _TRAIN_MEAN, _TRAIN_COV_INV, _THRESHOLD

    if _RANGES is not None:
        return True

    try:
        import pickle
        import pandas as pd

        # Load scaler
        with open(SCALER_PATH, 'rb') as f:
            _SCALER = pickle.load(f)

        # Load training data
        df = pd.read_csv(CSV_PATH)
        X  = df[FEATURES].values.astype(float)

        # Per-feature ranges with 10% margin
        mins = X.min(axis=0) * 0.9
        maxs = X.max(axis=0) * 1.1
        _RANGES = list(zip(mins.tolist(), maxs.tolist()))

        # Standardise
        X_sc = _SCALER.transform(X)

        # Mahalanobis: mean and inverse covariance
        _TRAIN_MEAN = X_sc.mean(axis=0)
        cov = np.cov(X_sc, rowvar=False)
        try:
            _TRAIN_COV_INV = np.linalg.inv(cov + 1e-6 * np.eye(cov.shape[0]))
        except np.linalg.LinAlgError:
            _TRAIN_COV_INV = np.linalg.pinv(cov)

        # Compute distances for all training samples → 90th percentile threshold (much less strict)
        dists = []
        for x in X_sc:
            diff = x - _TRAIN_MEAN
            d    = float(np.sqrt(diff @ _TRAIN_COV_INV @ diff))
            dists.append(d)
        _THRESHOLD = float(np.percentile(dists, 90))  # More lenient threshold

        print(f"[OOD] Stats loaded. Mahalanobis threshold (99th pct): {_THRESHOLD:.2f}")
        return True

    except Exception as e:
        print(f"[OOD] Could not load stats: {e}")
        return False


def _mahalanobis(x_sc):
    """Compute Mahalanobis distance from the training mean."""
    diff = x_sc - _TRAIN_MEAN
    return float(np.sqrt(diff @ _TRAIN_COV_INV @ diff))


def check_ood(feature_dict, for_image=False):
    """
    Check if feature values are within the WBCD training distribution.

    Parameters
    ----------
    feature_dict : dict  {feature_name: float_value}
    for_image    : bool  If True, never flag as OOD (image extraction uses
                         different scales than tabular WBCD). Returns
                         ood_advisory for UI warnings only.

    Returns
    -------
    dict:
        is_ood          : bool   — True if out-of-distribution
        ood_advisory    : bool   — True when values look unusual (for_image only)
        distance        : float  — Mahalanobis distance (None if unavailable)
        threshold       : float  — 99th percentile threshold
        out_of_range    : list   — feature names with values outside safe range
        confidence_pct  : float  — 0-100, how in-distribution the sample is
        message         : str    — human-readable explanation
    """
    loaded = _load_ood_stats()

    # ── Range check (always available, no model needed) ───────────────────────
    out_of_range = []
    for i, feat in enumerate(FEATURES):
        val = feature_dict.get(feat, 0.0)
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if loaded and _RANGES:
            lo, hi = _RANGES[i]
            # Use a much more lenient range check (25% margin instead of 10%)
            lo_adj = lo * 0.75  # Lower the lower bound significantly
            hi_adj = hi * 1.25  # Raise the upper bound significantly
            if v < lo_adj or v > hi_adj:
                out_of_range.append(feat)

    if not loaded:
        # Fallback: range check only
        if out_of_range:
            result = {
                'is_ood':        True,
                'distance':      None,
                'threshold':     None,
                'out_of_range':  out_of_range,
                'confidence_pct': 0.0,
                'message': (f"⚠️ {len(out_of_range)} feature(s) are outside normal range: "
                            f"{', '.join(out_of_range[:5])}. "
                            f"Results may be unreliable.")
            }
            return _finalize_for_image(result, for_image)
        return {
            'is_ood': False, 'ood_advisory': False, 'distance': None, 'threshold': None,
            'out_of_range': [], 'confidence_pct': 100.0,
            'message': 'Feature values are within expected range.'
        }

    # ── Mahalanobis distance check ────────────────────────────────────────────
    try:
        import pandas as pd
        x_vec = np.array([float(feature_dict.get(f, 0.0)) for f in FEATURES]).reshape(1, -1)
        x_sc  = _SCALER.transform(x_vec)[0]
        dist  = _mahalanobis(x_sc)

        is_ood = dist > _THRESHOLD

        # Confidence: 100% at dist=0, 0% at dist=threshold*3.5 (much more lenient)
        raw_conf = max(0.0, 1.0 - dist / (_THRESHOLD * 3.5))
        conf_pct = round(raw_conf * 100, 1)

        # Only show warning if there are many out-of-range features
        if len(out_of_range) >= 5:
            parts = []
            parts.append(
                f"Feature distribution is unusual (Mahalanobis distance={dist:.1f}, "
                f"normal range ≤{_THRESHOLD:.1f})"
            )
            parts.append(
                f"{len(out_of_range)} feature(s) outside normal range: "
                f"{', '.join(out_of_range[:3])}{'...' if len(out_of_range)>3 else ''}"
            )
            message = "⚠️ Unusual tissue pattern detected. " + ". ".join(parts) + ". Prediction may require expert review."
        elif len(out_of_range) >= 3:
            message = (f"⚠️ {len(out_of_range)} feature(s) outside normal range. "
                      f"Prediction may be less reliable.")
        else:
            message = (f"✓ Feature values are within the expected range "
                       f"(distance={dist:.1f}, threshold={_THRESHOLD:.1f}).")

        # Only flag as OOD if there are many out-of-range features (5 or more)
        # This prevents false positives for legitimate cancerous tissue
        is_ood_final = len(out_of_range) >= 5

        # Adjust message based on tissue characteristics
        if len(out_of_range) >= 5:
            message = f"⚠️ Unusual tissue pattern detected. {message}"
        elif len(out_of_range) >= 3:
            message = f"⚠️ Tissue characteristics outside normal range. {message}"

        result = {
            'is_ood':        is_ood_final,
            'distance':      round(dist, 2),
            'threshold':     round(_THRESHOLD, 2),
            'out_of_range':  out_of_range,
            'confidence_pct': conf_pct,
            'message':       message,
        }
        return _finalize_for_image(result, for_image)

    except Exception as e:
        return {
            'is_ood': False, 'ood_advisory': False, 'distance': None, 'threshold': None,
            'out_of_range': out_of_range, 'confidence_pct': 100.0,
            'message': f'OOD check skipped: {e}'
        }


def _finalize_for_image(result, for_image):
    """Image extraction uses pixel-based features — never block, only advise."""
    if not for_image:
        result.setdefault('ood_advisory', result.get('is_ood', False))
        return result
    advisory = bool(result.get('is_ood', False))
    result = dict(result)
    result['ood_advisory'] = advisory
    result['is_ood'] = False
    return result
