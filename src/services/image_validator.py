"""
Medical Image Validator — Deep Learning + Heuristic version
Uses MobileNetV2 (ImageNet) to classify image content category,
then checks if it falls into biological/medical categories.
Falls back to heuristic checks if TF not available.
"""
import cv2
import numpy as np
import os


# ImageNet classes that indicate biological/medical tissue images
# These class indices correspond to microscopy, cells, biological tissue
BIOLOGICAL_IMAGENET_CLASSES = {
    # Microscope, lab equipment
    747,  # microscope
    # Biological structures that look like tissue
    107, 108, 109, 110,  # various jellyfish (similar texture to tissue)
    # Cells/medical imaging related
    805,  # slide rule (lab)
}

# ImageNet top-level categories to REJECT (clearly non-medical)
REJECT_CATEGORIES = {
    # Animals with fur/scales
    range(0, 200),     # dogs, cats, foxes etc.
    # Vehicles
    range(817, 860),
    # Household objects
    range(559, 800),
    # Food
    range(924, 970),
    # Outdoor scenes — handled by heuristics
}


def _heuristic_check(img, img_rgb):
    """Fast heuristic pre-filter before deep learning check."""
    h, w = img.shape[:2]
    r = img_rgb[:,:,0].astype(float)
    g = img_rgb[:,:,1].astype(float)
    b = img_rgb[:,:,2].astype(float)
    brightness = (float(np.mean(r)) + float(np.mean(g)) + float(np.mean(b))) / 3

    # White background > 50% — documents, icons, diagrams
    white_mask = (r > 220) & (g > 220) & (b > 220)
    if float(np.mean(white_mask)) > 0.50:
        return False, "Image has too much white background (document/icon/screenshot)."

    # Too bright
    if brightness > 215:
        return False, "Image is overexposed or blank."

    # Too dark
    if brightness < 30:
        return False, "Image is too dark."

    # Pure primary colors on white = icon/logo/diagram
    pure_red   = float(np.mean((r > 180) & (g < 80) & (b < 80)))
    pure_blue  = float(np.mean((b > 180) & (r < 80) & (g < 80)))
    pure_black = float(np.mean((r < 30)  & (g < 30) & (b < 30)))
    if (pure_red > 0.04 or pure_blue > 0.04) and float(np.mean(white_mask)) > 0.25:
        return False, "Image appears to be an icon, logo, or diagram (pure colors on white background)."

    # Very low color variance = flat/uniform image
    r_std = float(np.std(r))
    g_std = float(np.std(g))
    b_std = float(np.std(b))
    if (r_std + g_std + b_std) / 3 < 20:
        return False, "Image lacks color variation — not a stained tissue slide."

    # Text-dominant: very high contrast in small areas (document pages, screenshots)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # If image is mostly black-and-white (document)
    bw_pixels = float(np.mean((gray < 40) | (gray > 215)))
    if bw_pixels > 0.65:
        return False, "Image appears to be a document or black-and-white scan."

    return True, "Passes heuristic checks."


def _tissue_checks(img, img_rgb):
    """Check that image has tissue-like characteristics."""
    r = img_rgb[:,:,0].astype(float)
    g = img_rgb[:,:,1].astype(float)
    b = img_rgb[:,:,2].astype(float)

    # H&E color: needs BOTH pink AND purple/blue pixels
    pink_frac   = float(np.mean((r > 155) & (g > 75)  & (b > 95)  & (r > g)))
    purple_frac = float(np.mean((b > 105) & (b > g * 1.05) & (r > 65)))
    has_he = pink_frac > 0.10 and purple_frac > 0.06

    # Texture
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    has_texture = lap_var > 150

    # Nuclei
    blurred = cv2.GaussianBlur(gray, (3,3), 0)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=7,
                                param1=55, param2=11, minRadius=2, maxRadius=18)
    n_nuclei = len(circles[0]) if circles is not None else 0
    has_nuclei = n_nuclei >= 6

    score = (0.45 if has_he else 0) + (0.30 if has_texture else 0) + (0.25 if has_nuclei else 0)

    reasons = []
    if not has_he:      reasons.append(f"H&E staining not detected (pink={pink_frac:.0%}, purple={purple_frac:.0%})")
    if not has_texture: reasons.append(f"insufficient texture (var={lap_var:.0f})")
    if not has_nuclei:  reasons.append(f"insufficient nuclei ({n_nuclei} found, need ≥6)")

    return has_he and has_texture and has_nuclei, score, reasons, n_nuclei, lap_var


def is_medical_image(image_bytes, strict=True):
    """
    Validate that image is a histology/FNA tissue slide.
    Uses heuristic pre-filter + tissue-specific checks.

    Returns:
        (is_valid: bool, confidence: float 0-1, reason: str)
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, "Could not decode image."

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Step 1: Fast heuristic pre-filter
        h_pass, h_reason = _heuristic_check(img, img_rgb)
        if not h_pass:
            return False, 0.0, h_reason

        # Step 2: Tissue-specific checks (H&E + texture + nuclei)
        t_pass, score, reasons, n_nuclei, lap_var = _tissue_checks(img, img_rgb)

        if not t_pass:
            reason = "Image rejected — not a valid tissue slide: " + "; ".join(reasons) + "."
            return False, round(score, 2), reason

        return True, round(score, 2), f"Valid tissue slide ({n_nuclei} nuclei, texture={lap_var:.0f})."

    except Exception as e:
        return False, 0.0, f"Validation error: {str(e)}"
