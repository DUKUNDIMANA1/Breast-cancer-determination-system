"""
Medical Image Validator — Strict version
Requires ALL THREE criteria to pass:
1. H&E color profile (pink+purple mix typical of tissue staining)
2. High texture complexity (tissue has fine-grained patterns)
3. Presence of small circular structures (cell nuclei)
"""
import cv2
import numpy as np


def is_medical_image(image_bytes, strict=False):
    """
    Validate that an image is a histology/FNA tissue slide.

    Returns:
        (is_valid: bool, confidence: float 0-1, reason: str)
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, "Could not decode image."

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        r = img_rgb[:,:,0].astype(float)
        g = img_rgb[:,:,1].astype(float)
        b = img_rgb[:,:,2].astype(float)

        r_mean = float(np.mean(r))
        g_mean = float(np.mean(g))
        b_mean = float(np.mean(b))

        # ── Criteria 1: H&E Color Profile ──────────────────────────────────
        # H&E slides have a mix of pink (eosin) and purple/blue (hematoxylin)
        # Both channels must be significantly present
        # Pink pixels: R high, G moderate, B moderate-high
        pink_mask   = (r > 150) & (g > 80) & (b > 100) & (r > g)
        # Purple pixels: B high relative to G, moderate R
        purple_mask = (b > 100) & (b > g * 1.1) & (r > 80)

        pink_frac   = float(np.mean(pink_mask))
        purple_frac = float(np.mean(purple_mask))

        # Need BOTH pink AND purple to be present (tissue has both stains)
        has_he_color = pink_frac > 0.10 and purple_frac > 0.05

        # ── Hard rejections ─────────────────────────────────────────────────
        # Sky/blue dominant
        if b_mean > r_mean * 1.25 and b_mean > 140:
            return False, 0.0, "Image appears to be a sky/outdoor photo — rejected."
        # Green dominant (vegetation, etc.)
        if g_mean > r_mean * 1.2 and g_mean > b_mean * 1.15 and g_mean > 120:
            return False, 0.0, "Image appears to be vegetation/nature — rejected."
        # Very dark
        if (r_mean + g_mean + b_mean) / 3 < 40:
            return False, 0.0, "Image is too dark to be a valid tissue slide."
        # Very bright uniform (blank/white paper)
        if r_mean > 230 and g_mean > 230 and b_mean > 230:
            return False, 0.0, "Image appears to be blank/white — rejected."
        # Grayscale-dominant (natural photos, documents)
        color_variance = float(np.std([r_mean, g_mean, b_mean]))
        if color_variance < 8:
            return False, 0.0, "Image lacks color variation — not a stained tissue slide."

        # ── Criteria 2: Texture Complexity ──────────────────────────────────
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # Tissue images have very high texture due to cell patterns
        has_texture = laplacian_var > 150  # raised from 100

        # ── Criteria 3: Small circular structures (cell nuclei) ─────────────
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=8,
            param1=60, param2=12, minRadius=2, maxRadius=20
        )
        nucleus_count = len(circles[0]) if circles is not None else 0
        has_nuclei = nucleus_count >= 5  # need at least 5 circles

        # ── Scoring & Decision ───────────────────────────────────────────────
        score = 0.0
        if has_he_color: score += 0.45
        if has_texture:  score += 0.30
        if has_nuclei:   score += 0.25

        # Require ALL THREE for strict mode, at least 2 of 3 for lenient
        if strict:
            is_valid = has_he_color and has_texture and has_nuclei
        else:
            # Must have H&E color + at least one other criterion
            is_valid = has_he_color and (has_texture or has_nuclei) and score >= 0.55

        if not is_valid:
            reasons = []
            if not has_he_color:
                reasons.append(f"H&E color not detected (pink={pink_frac:.0%}, purple={purple_frac:.0%})")
            if not has_texture:
                reasons.append(f"insufficient texture (variance={laplacian_var:.0f})")
            if not has_nuclei:
                reasons.append(f"no cell nuclei detected ({nucleus_count} circles found)")
            reason = "Not a tissue slide: " + "; ".join(reasons) + "."
            return False, round(score, 2), reason

        return True, round(score, 2), f"Valid tissue slide (H&E color, texture, {nucleus_count} nuclei detected)."

    except Exception as e:
        return False, 0.0, f"Validation error: {str(e)}"
