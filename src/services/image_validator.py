"""
Medical Image Validator
Checks whether an uploaded image is likely a tissue/histology slide
before allowing feature extraction and prediction.
"""
import cv2
import numpy as np


def is_medical_image(image_bytes, strict=False):
    """
    Check if image is likely a histological/medical tissue image.

    Histology images characteristics:
    - Pink/purple color profile (H&E staining)
    - High texture complexity
    - Many small circular structures (cell nuclei)

    Returns:
        (is_valid: bool, confidence: float 0-1, reason: str)
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, 0.0, "Could not decode image"

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        r_mean = float(np.mean(img_rgb[:,:,0]))
        g_mean = float(np.mean(img_rgb[:,:,1]))
        b_mean = float(np.mean(img_rgb[:,:,2]))

        # H&E stained: pink or purple tones
        is_pinkish  = r_mean > 150 and g_mean > 100 and b_mean > 130
        is_purplish = r_mean > 100 and g_mean < 130 and b_mean > 120
        is_hematox  = is_pinkish or is_purplish

        # Obvious non-medical rejections
        is_sky   = (b_mean > r_mean * 1.3 and b_mean > 160) and not is_hematox
        is_green = (g_mean > r_mean * 1.2 and g_mean > b_mean * 1.2 and g_mean > 130) and not is_hematox
        is_dark  = (r_mean + g_mean + b_mean) / 3 < 30

        if is_sky:
            return False, 0.1, "Image appears to be a sky/outdoor photo, not a tissue slide."
        if is_green:
            return False, 0.1, "Image appears to be vegetation/nature, not a tissue slide."
        if is_dark:
            return False, 0.1, "Image is too dark to be a valid tissue slide."

        # Texture complexity
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        has_texture = laplacian_var > 100

        # Circular structures (cell nuclei)
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=10,
            param1=50, param2=15, minRadius=3, maxRadius=25
        )
        has_circles = circles is not None and len(circles[0]) >= 3

        # Score
        score = 0.0
        if is_hematox:  score += 0.4
        if has_texture: score += 0.3
        if has_circles: score += 0.3

        threshold = 0.7 if strict else 0.4
        is_valid  = score >= threshold

        if not is_valid:
            parts = []
            if not is_hematox:  parts.append("color doesn't match H&E staining")
            if not has_texture: parts.append("insufficient texture")
            if not has_circles: parts.append("no cell-like structures detected")
            reason = "Image may not be a tissue slide: " + ", ".join(parts) + "."
            return False, score, reason

        return True, score, "Image appears to be a valid tissue slide."

    except Exception as e:
        return False, 0.0, f"Validation error: {str(e)}"
