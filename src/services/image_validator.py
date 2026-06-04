"""
Medical Image Validator — Strict version v2
Rejects icons, diagrams, documents, and non-tissue images.
Requires genuine H&E tissue characteristics.
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

        h, w = img.shape[:2]
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        r = img_rgb[:,:,0].astype(float)
        g = img_rgb[:,:,1].astype(float)
        b = img_rgb[:,:,2].astype(float)

        r_mean = float(np.mean(r))
        g_mean = float(np.mean(g))
        b_mean = float(np.mean(b))
        brightness = (r_mean + g_mean + b_mean) / 3

        # ── Hard rejections ──────────────────────────────────────────────────

        # White/near-white background > 60% (documents, icons, diagrams)
        white_mask = (r > 220) & (g > 220) & (b > 220)
        white_frac = float(np.mean(white_mask))
        if white_frac > 0.50:
            return False, 0.0, f"Too much white background ({white_frac:.0%}) — appears to be a document or icon, not a tissue slide."

        # Very bright overall (blank paper, screenshot)
        if brightness > 210:
            return False, 0.0, "Image is too bright/washed out to be a tissue slide."

        # Very dark
        if brightness < 35:
            return False, 0.0, "Image is too dark."

        # Sky/blue dominant
        if b_mean > r_mean * 1.25 and b_mean > 140 and blue_frac_check(img_rgb) > 0.30:
            return False, 0.0, "Image appears to be a sky/outdoor photo."

        # Green dominant
        if g_mean > r_mean * 1.2 and g_mean > b_mean * 1.15 and g_mean > 120:
            return False, 0.0, "Image appears to be vegetation/nature."

        # Few unique colors = icon/diagram (tissue slides have continuous color gradients)
        # Sample 5000 random pixels and count distinct color clusters
        flat = img_rgb.reshape(-1, 3)
        sample_idx = np.random.choice(len(flat), min(3000, len(flat)), replace=False)
        sample = flat[sample_idx].astype(np.float32)
        # Count pixels that are pure red, pure blue, pure black, pure white (icon colors)
        is_pure_red   = (r[img_rgb[:,:,0] > 180] > 150).any() if True else False
        pure_colors = 0
        pure_colors += int(np.mean((r > 200) & (g < 80) & (b < 80)) > 0.05)   # red
        pure_colors += int(np.mean((b > 200) & (r < 80) & (g < 80)) > 0.05)   # blue
        pure_colors += int(np.mean((r < 30)  & (g < 30) & (b < 30)) > 0.05)   # black
        if pure_colors >= 2 and white_frac > 0.30:
            return False, 0.0, "Image appears to be an icon or diagram (contains pure primary colors on white background)."

        # ── Color variance check ─────────────────────────────────────────────
        # Tissue slides have rich color variation across the image
        r_std = float(np.std(r))
        g_std = float(np.std(g))
        b_std = float(np.std(b))
        color_richness = (r_std + g_std + b_std) / 3

        if color_richness < 25:
            return False, 0.0, f"Image lacks color richness (std={color_richness:.1f}) — not a stained tissue slide."

        # ── Criteria 1: H&E Color Profile ────────────────────────────────────
        img_arr = img_rgb.astype(float)
        # Pink pixels: high R, moderate G+B, R dominant
        pink_mask   = (img_arr[:,:,0] > 160) & (img_arr[:,:,1] > 80) & (img_arr[:,:,2] > 100) & (img_arr[:,:,0] > img_arr[:,:,1])
        # Purple/blue pixels: B elevated, G lower, moderate R
        purple_mask = (img_arr[:,:,2] > 110) & (img_arr[:,:,2] > img_arr[:,:,1] * 1.05) & (img_arr[:,:,0] > 70)

        pink_frac   = float(np.mean(pink_mask))
        purple_frac = float(np.mean(purple_mask))

        has_he_color = pink_frac > 0.12 and purple_frac > 0.08

        # ── Criteria 2: Texture Complexity ───────────────────────────────────
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        has_texture = laplacian_var > 200  # tissue is very textured

        # ── Criteria 3: Small circular structures ────────────────────────────
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=8,
            param1=60, param2=12, minRadius=2, maxRadius=18
        )
        nucleus_count = len(circles[0]) if circles is not None else 0
        has_nuclei = nucleus_count >= 8  # raised from 5

        # ── Score ─────────────────────────────────────────────────────────────
        score = 0.0
        if has_he_color: score += 0.45
        if has_texture:  score += 0.30
        if has_nuclei:   score += 0.25

        # ALL THREE required
        is_valid = has_he_color and has_texture and has_nuclei

        if not is_valid:
            reasons = []
            if not has_he_color:
                reasons.append(f"H&E staining not detected (pink={pink_frac:.0%}, purple={purple_frac:.0%})")
            if not has_texture:
                reasons.append(f"insufficient texture (variance={laplacian_var:.0f}, need >200)")
            if not has_nuclei:
                reasons.append(f"insufficient cell nuclei ({nucleus_count} found, need ≥8)")
            reason = "Not a valid tissue slide: " + "; ".join(reasons) + "."
            return False, round(score, 2), reason

        return True, round(score, 2), f"Valid H&E tissue slide ({nucleus_count} nuclei, texture={laplacian_var:.0f})."

    except Exception as e:
        return False, 0.0, f"Validation error: {str(e)}"


def blue_frac_check(img_rgb):
    """Helper: fraction of pixels where blue dominates."""
    b = img_rgb[:,:,2].astype(float)
    r = img_rgb[:,:,0].astype(float)
    g = img_rgb[:,:,1].astype(float)
    return float(np.mean((b > r * 1.2) & (b > g * 1.1) & (b > 120)))
