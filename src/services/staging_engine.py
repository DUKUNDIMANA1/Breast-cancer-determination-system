# -*- coding: utf-8 -*-
"""
Histopathology-Based Cancer Staging Engine — BreastCare AI
============================================================
Estimates breast cancer stage (I–IV) from histopathology image features.

Method: Modified Nottingham Grading System proxy
  - Score 1: Tubule / Gland Formation  (structure regularity)
  - Score 2: Nuclear Pleomorphism      (size + shape variation)
  - Score 3: Mitotic Activity Proxy    (high-intensity foci density)

Total Nottingham score (3–9) → Grade:
  3–5 → Grade 1 (well-differentiated)
  6–7 → Grade 2 (moderately differentiated)
  8–9 → Grade 3 (poorly differentiated)

Grade + invasion proxy → Stage I–IV:
  Grade 1, low invasion  → Stage I
  Grade 1–2, mod invasion → Stage II
  Grade 2–3, high invasion → Stage III
  Grade 3, very high density/pleomorphism → Stage IV

All analysis is performed purely from the image bytes using OpenCV/numpy/skimage.
No Wisconsin WBCD features are used.
"""

import os
import numpy as np

# ── Optional imports (graceful fallback) ─────────────────────────────────────
try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

try:
    from skimage.measure import label as sk_label, regionprops
    from skimage.morphology import binary_closing, disk
    _SKIMAGE_OK = True
except ImportError:
    _SKIMAGE_OK = False


# ── Scoring constants ─────────────────────────────────────────────────────────
_SCORE_LOW  = 1
_SCORE_MID  = 2
_SCORE_HIGH = 3

# Stage labels
STAGES = {
    1: 'Stage I',
    2: 'Stage II',
    3: 'Stage III',
    4: 'Stage IV',
}

STAGE_DESCRIPTIONS = {
    'Stage I':   (
        'Small, well-differentiated tumour with no evidence of local invasion. '
        'Glandular architecture is largely preserved. Excellent prognosis with standard therapy.'
    ),
    'Stage II':  (
        'Moderately differentiated tumour with limited local spread. '
        'Some loss of glandular architecture. Good prognosis with appropriate treatment.'
    ),
    'Stage III': (
        'Poorly differentiated tumour with significant local invasion. '
        'Marked nuclear pleomorphism and high mitotic activity observed. '
        'Requires aggressive multi-modal treatment.'
    ),
    'Stage IV':  (
        'Highly aggressive, poorly differentiated tumour with evidence of extensive local invasion. '
        'Severe nuclear atypia and very high cellularity density. '
        'Immediate specialist oncology referral required.'
    ),
}

STAGE_PROGNOSIS = {
    'Stage I':   '5-year survival rate >95% with early treatment.',
    'Stage II':  '5-year survival rate 70–85% with appropriate treatment.',
    'Stage III': '5-year survival rate 40–60% with aggressive treatment.',
    'Stage IV':  '5-year survival rate <25%; palliative and systemic therapy indicated.',
}

STAGE_RECOMMENDATIONS = {
    'Stage I':   [
        'Surgical resection (lumpectomy or mastectomy)',
        'Sentinel lymph node biopsy',
        'Adjuvant radiotherapy (if lumpectomy)',
        'Hormonal therapy if ER/PR positive',
        'Regular follow-up every 6 months',
    ],
    'Stage II':  [
        'Mastectomy or breast-conserving surgery with clear margins',
        'Axillary lymph node dissection or SLNB',
        'Adjuvant chemotherapy (AC-T or CMF regimen)',
        'Radiotherapy post-surgery',
        'Hormonal / targeted therapy based on receptor status',
    ],
    'Stage III': [
        'Neoadjuvant chemotherapy prior to surgery',
        'Modified radical mastectomy',
        'Post-mastectomy radiotherapy',
        'HER2-targeted therapy if HER2-positive',
        'Immunotherapy consideration',
        'Multidisciplinary oncology team review',
    ],
    'Stage IV':  [
        'Systemic chemotherapy (first-line)',
        'Targeted therapy (CDK4/6 inhibitors, PARP inhibitors)',
        'Palliative radiotherapy for symptom control',
        'Bone-modifying agents if bone metastasis suspected',
        'Immediate referral to specialist oncology centre',
        'Enrolment in clinical trials consideration',
        'Palliative care consultation',
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# Internal image analysis helpers
# ══════════════════════════════════════════════════════════════════════════════

def _load_image(image_bytes):
    """Decode bytes → BGR numpy array (None on failure)."""
    if not _CV2_OK:
        return None
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def _preprocess(img):
    """Return (gray, resized_color) standardised to ~300px."""
    h, w = img.shape[:2]
    scale = 300.0 / max(h, w)
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray, img


def _segment_nuclei(gray):
    """
    Segment cell nuclei from grayscale histopathology image.
    Uses Otsu thresholding on inverted image (nuclei are dark in H&E).
    Returns binary mask, contours list.
    """
    # CLAHE enhance
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enh   = clahe.apply(gray)

    # Blur + Otsu threshold (nuclei are dark in H&E → invert first)
    blurred = cv2.GaussianBlur(enh, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN,  kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_area     = gray.shape[0] * gray.shape[1]

    # Keep contours that look like nuclei: 0.01% to 5% of image area
    min_area = img_area * 0.0001
    max_area = img_area * 0.05
    nuclei   = [c for c in contours if min_area < cv2.contourArea(c) < max_area]
    return binary, nuclei


def _score_gland_formation(gray, nuclei, img):
    """
    Score 1: Tubule/Gland Formation (1–3).
    Well-formed glands → 1;  partial → 2;  little/no glandular structure → 3.
    Proxy: ratio of large round regions (gland lumens) to total tissue area.
    """
    if not _CV2_OK:
        return _SCORE_MID, 0.0

    img_area = gray.shape[0] * gray.shape[1]

    # Detect bright circular regions (gland lumens appear bright in H&E)
    _, bright = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    kernel    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    bright    = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel, iterations=1)

    lumen_contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_lumen = img_area * 0.002
    max_lumen = img_area * 0.15
    lumens    = [c for c in lumen_contours if min_lumen < cv2.contourArea(c) < max_lumen]

    lumen_area_ratio = sum(cv2.contourArea(c) for c in lumens) / (img_area + 1e-6)

    if lumen_area_ratio > 0.15:
        score = _SCORE_LOW    # >15% gland lumens → well-formed
    elif lumen_area_ratio > 0.06:
        score = _SCORE_MID
    else:
        score = _SCORE_HIGH   # <6% → poor gland formation

    return score, round(lumen_area_ratio * 100, 2)


def _score_nuclear_pleomorphism(nuclei, gray):
    """
    Score 2: Nuclear Pleomorphism (1–3).
    Uniform, small nuclei → 1;  moderate variation → 2;  marked atypia → 3.
    Proxy: coefficient of variation (CV) of nucleus areas + mean circularity.
    """
    if len(nuclei) < 3:
        return _SCORE_MID, 0.0, 0.0

    areas         = []
    circularities = []

    for c in nuclei:
        a = cv2.contourArea(c)
        p = cv2.arcLength(c, True)
        areas.append(a)
        circ = (4 * np.pi * a) / (p * p + 1e-6)
        circularities.append(min(circ, 1.0))

    areas = np.array(areas, dtype=float)
    cv_area = float(np.std(areas) / (np.mean(areas) + 1e-6))   # coefficient of variation
    mean_circ = float(np.mean(circularities))

    # High CV → high pleomorphism; low circularity → irregular shapes
    if cv_area < 0.30 and mean_circ > 0.70:
        score = _SCORE_LOW    # uniform, round nuclei
    elif cv_area < 0.60 or mean_circ > 0.50:
        score = _SCORE_MID
    else:
        score = _SCORE_HIGH   # high variation + irregular

    return score, round(cv_area, 4), round(mean_circ, 4)


def _score_mitotic_activity(gray, img):
    """
    Score 3: Mitotic Activity Proxy (1–3).
    True mitotic figure detection requires magnification; we approximate by:
    - Detecting very dark, compact, irregular foci (condensed chromatin in mitosis)
    - Density of these foci per unit area.
    """
    if not _CV2_OK:
        return _SCORE_MID, 0.0

    img_area = gray.shape[0] * gray.shape[1]

    # Very dark compact regions (below 15th percentile of grey)
    thresh_val = int(np.percentile(gray, 15))
    _, dark    = cv2.threshold(gray, max(thresh_val, 10), 255, cv2.THRESH_BINARY_INV)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dark   = cv2.morphologyEx(dark, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_a = img_area * 0.0001
    max_a = img_area * 0.003  # small compact foci
    foci  = [c for c in contours if min_a < cv2.contourArea(c) < max_a]

    # Check irregularity: low circularity → mitotic-like
    irregular_foci = []
    for c in foci:
        a  = cv2.contourArea(c)
        p  = cv2.arcLength(c, True)
        ci = (4 * np.pi * a) / (p * p + 1e-6)
        if ci < 0.65:   # irregular shape
            irregular_foci.append(c)

    # Foci per 1000px²
    density = len(irregular_foci) / (img_area / 1000.0 + 1e-6)

    if density < 0.5:
        score = _SCORE_LOW
    elif density < 1.5:
        score = _SCORE_MID
    else:
        score = _SCORE_HIGH

    return score, round(density, 4)


def _invasion_proxy(nuclei, gray, img):
    """
    Local invasion proxy: cellularity density.
    High nucleus density + irregular arrangement → invasion suspected.
    Returns (invasion_level: 1-4, nucleus_density_per_1000px2).
    """
    if not _CV2_OK:
        return 1, 0.0

    img_area   = gray.shape[0] * gray.shape[1]
    n_nuclei   = len(nuclei)
    density    = n_nuclei / (img_area / 1000.0 + 1e-6)

    # Assess spatial regularity via nearest-neighbour distances
    if n_nuclei >= 5:
        centroids = []
        for c in nuclei:
            M = cv2.moments(c)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                centroids.append((cx, cy))
        centroids = np.array(centroids)
        if len(centroids) >= 3:
            dists = []
            for i, pt in enumerate(centroids):
                d = np.linalg.norm(centroids - pt, axis=1)
                d = d[d > 0]
                if len(d) > 0:
                    dists.append(float(np.min(d)))
            cv_dist = float(np.std(dists) / (np.mean(dists) + 1e-6)) if dists else 0.5
        else:
            cv_dist = 0.5
    else:
        cv_dist = 0.5

    # High density + irregular spacing → invasion
    if density < 1.0 and cv_dist < 0.5:
        level = 1
    elif density < 2.5 or cv_dist < 0.7:
        level = 2
    elif density < 5.0 or cv_dist < 1.0:
        level = 3
    else:
        level = 4

    return level, round(density, 4)


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

def determine_stage(image_bytes, cnn_result: dict) -> dict:
    """
    Determine cancer stage from histopathology image.

    Parameters
    ----------
    image_bytes : bytes
        Raw image file bytes (the uploaded tissue slide).
    cnn_result : dict
        Result dict from cnn_predict_image(), e.g.:
          {'result': 1, 'confidence': 87.5, 'p_malignant': 87.5, 'p_benign': 12.5, ...}

    Returns
    -------
    dict with keys:
      stage           : str  e.g. 'Stage II'
      nottingham_score: int  3–9
      grade           : int  1–3
      grade_label     : str  e.g. 'Grade 2 (Moderately Differentiated)'
      scores          : dict  {gland_formation, nuclear_pleomorphism, mitotic_activity}
      invasion_level  : int  1–4
      cellularity_density : float
      lumen_ratio     : float  %
      nuclear_cv      : float
      mean_circularity: float
      mitotic_density : float
      description     : str
      prognosis       : str
      recommendations : list[str]
      image_available : bool
      fallback_used   : bool   True if image could not be processed
    """
    # Defaults in case image processing fails
    _fallback = False
    p_mal     = cnn_result.get('p_malignant', 50.0) / 100.0

    # ── Try image-based analysis ─────────────────────────────────────────────
    s_gland   = _SCORE_MID
    s_pleom   = _SCORE_MID
    s_mitotic = _SCORE_MID
    inv_level = 2
    lumen_ratio    = 0.0
    nuclear_cv     = 0.0
    mean_circ      = 0.0
    mitotic_density = 0.0
    cell_density   = 0.0
    img_available  = False

    if _CV2_OK and image_bytes:
        try:
            img = _load_image(image_bytes)
            if img is not None:
                img_available = True
                gray, img_r  = _preprocess(img)
                _, nuclei    = _segment_nuclei(gray)

                # Score 1: Gland formation
                s_gland, lumen_ratio = _score_gland_formation(gray, nuclei, img_r)

                # Score 2: Nuclear pleomorphism
                s_pleom, nuclear_cv, mean_circ = _score_nuclear_pleomorphism(nuclei, gray)

                # Score 3: Mitotic activity proxy
                s_mitotic, mitotic_density = _score_mitotic_activity(gray, img_r)

                # Invasion proxy
                inv_level, cell_density = _invasion_proxy(nuclei, gray, img_r)

        except Exception as e:
            print(f"[Staging] Image analysis error: {e}")
            _fallback = True
    else:
        _fallback = True

    # ── If image analysis failed, fall back to CNN probability ───────────────
    if _fallback or not img_available:
        if p_mal < 0.65:
            s_gland, s_pleom, s_mitotic = 1, 1, 2
            inv_level = 1
        elif p_mal < 0.80:
            s_gland, s_pleom, s_mitotic = 2, 2, 2
            inv_level = 2
        elif p_mal < 0.92:
            s_gland, s_pleom, s_mitotic = 2, 3, 3
            inv_level = 3
        else:
            s_gland, s_pleom, s_mitotic = 3, 3, 3
            inv_level = 4

    # ── Nottingham score → Grade ─────────────────────────────────────────────
    nottingham = s_gland + s_pleom + s_mitotic   # 3–9

    if nottingham <= 5:
        grade = 1
        grade_label = 'Grade 1 (Well Differentiated)'
    elif nottingham <= 7:
        grade = 2
        grade_label = 'Grade 2 (Moderately Differentiated)'
    else:
        grade = 3
        grade_label = 'Grade 3 (Poorly Differentiated)'

    # ── Grade + invasion → Stage ─────────────────────────────────────────────
    if grade == 1 and inv_level <= 2:
        stage_num = 1
    elif grade <= 2 and inv_level <= 3:
        stage_num = 2
    elif grade == 3 and inv_level <= 3:
        stage_num = 3
    elif inv_level >= 4 or (grade == 3 and nottingham >= 8):
        stage_num = 4
    else:
        stage_num = 2   # safe default

    stage = STAGES[stage_num]

    return {
        'stage':                stage,
        'stage_num':            stage_num,
        'nottingham_score':     nottingham,
        'grade':                grade,
        'grade_label':          grade_label,
        'scores': {
            'gland_formation':    s_gland,
            'nuclear_pleomorphism': s_pleom,
            'mitotic_activity':   s_mitotic,
        },
        'invasion_level':       inv_level,
        'cellularity_density':  cell_density,
        'lumen_ratio':          lumen_ratio,
        'nuclear_cv':           nuclear_cv,
        'mean_circularity':     mean_circ,
        'mitotic_density':      mitotic_density,
        'description':          STAGE_DESCRIPTIONS[stage],
        'prognosis':            STAGE_PROGNOSIS[stage],
        'recommendations':      STAGE_RECOMMENDATIONS[stage],
        'image_available':      img_available,
        'fallback_used':        _fallback or not img_available,
    }
