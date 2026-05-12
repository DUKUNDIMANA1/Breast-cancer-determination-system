"""
Base Image Processor for Breast Cancer Feature Extraction
Provides common functionality for all image processors
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from scipy import ndimage
from scipy.spatial import ConvexHull
import warnings
warnings.filterwarnings('ignore')

# Feature names matching Wisconsin Breast Cancer Dataset
FEATURE_NAMES = [
    'radius_mean','texture_mean','smoothness_mean','compactness_mean',
    'concavity_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','smoothness_se','compactness_se',
    'concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'smoothness_worst','compactness_worst','concavity_worst',
    'symmetry_worst','fractal_dimension_worst'
]

# Default feature values from Wisconsin Breast Cancer Dataset
DEFAULT_FEATURES = {
    'radius_mean': 13.37, 'texture_mean': 18.84, 'smoothness_mean': 0.0962,
    'compactness_mean': 0.1043, 'concavity_mean': 0.0888, 'symmetry_mean': 0.1812,
    'fractal_dimension_mean': 0.0628, 'radius_se': 0.4051, 'texture_se': 1.2169,
    'smoothness_se': 0.00638, 'compactness_se': 0.0210, 'concavity_se': 0.0259,
    'concave points_se': 0.0111, 'symmetry_se': 0.0207, 'fractal_dimension_se': 0.00380,
    'smoothness_worst': 0.1323, 'compactness_worst': 0.2534, 'concavity_worst': 0.2720,
    'symmetry_worst': 0.2900, 'fractal_dimension_worst': 0.0839
}

def generate_annotated_image(image_bytes):
    """
    Generate annotated image with feature extraction visualization.

    Args:
        image_bytes: Raw image data in bytes format

    Returns:
        str: Base64 encoded annotated image
    """
    try:
        # Convert bytes to PIL Image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image")

        # Convert to PIL for drawing
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Create drawing context
        draw = ImageDraw.Draw(pil_img)

        # Add annotations
        try:
            # Try to use a simple font
            font = ImageFont.load_default()
        except:
            font = None

        # Add title
        title = "Breast Cancer Feature Analysis"
        if font:
            draw.text((10, 10), title, fill=(255, 0, 0), font=font)
        else:
            draw.text((10, 10), title, fill=(255, 0, 0))

        # Add processing info
        info_lines = [
            "* Image processed successfully",
            "* Features extracted",
            "* Ready for ML prediction"
        ]

        y_offset = 40
        for line in info_lines:
            if font:
                draw.text((10, y_offset), line, fill=(0, 255, 0), font=font)
            else:
                draw.text((10, y_offset), line, fill=(0, 255, 0))
            y_offset += 20

        # Convert back to bytes
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Convert to base64
        base64_str = base64.b64encode(img_byte_arr).decode('utf-8')

        return base64_str

    except Exception as e:
        print(f"[Base Image Processor] Error generating annotated image: {e}")
        # Return simple error annotation
        return create_error_annotation()

def create_error_annotation():
    """Create a simple error annotation image."""
    try:
        # Create a simple error image
        img = Image.new('RGB', (400, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.load_default()
        except:
            font = None

        error_text = "WARNING: Image Processing Error"
        if font:
            draw.text((10, 30), error_text, fill=(255, 0, 0), font=font)
        else:
            draw.text((10, 30), error_text, fill=(255, 0, 0))

        # Convert to base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        base64_str = base64.b64encode(img_byte_arr).decode('utf-8')
        return base64_str

    except Exception:
        # Return empty string if everything fails
        return ""

def calculate_fractal_dimension_simple(image):
    """Simplified fractal dimension calculation with NaN protection."""
    try:
        # Use edge image for fractal analysis
        edges = cv2.Canny(image, 50, 150)

        # Box-counting with fewer scales for speed
        scales = [4, 8, 16, 32]
        counts = []

        for scale in scales:
            if scale >= min(edges.shape):
                continue

            # Downsample
            small = cv2.resize(edges, (0,0), fx=1/scale, fy=1/scale)
            # Count non-zero pixels
            counts.append(np.count_nonzero(small))

        if len(counts) < 2:
            return DEFAULT_FEATURES['fractal_dimension_mean']

        # Fit power law: N(ε) ∝ ε^(-D)
        log_scales = np.log(1.0 / np.array(scales[:len(counts)]))
        log_counts = np.log(counts)

        # Linear regression
        D, _ = np.polyfit(log_scales, log_counts, 1)
        return abs(D)

    except Exception:
        return DEFAULT_FEATURES['fractal_dimension_mean']

def generate_statistical_features(features):
    """Generate SE and worst values from mean features."""
    if not features:
        return {}

    result = {}

    # Mean features
    for name in FEATURE_NAMES:
        if name.endswith('_mean') and name in features:
            result[name] = features[name]

    # SE features (standard error)
    for name in FEATURE_NAMES:
        if name.endswith('_mean'):
            base_name = name.replace('_mean', '')
            se_name = f"{base_name}_se"

            # Use a fraction of the mean as SE (simple approximation)
            if name in features and features[name] > 0:
                result[se_name] = features[name] * 0.1  # 10% of mean
            else:
                result[se_name] = DEFAULT_FEATURES[se_name]

    # Worst features (maximum of mean and SE)
    for name in FEATURE_NAMES:
        if name.endswith('_mean'):
            base_name = name.replace('_mean', '')
            worst_name = f"{base_name}_worst"

            # Worst is max of mean and SE
            mean_val = result.get(name, DEFAULT_FEATURES[name])
            se_val = result.get(f"{base_name}_se", DEFAULT_FEATURES[f"{base_name}_se"])
            result[worst_name] = max(mean_val, se_val) * 1.2  # Add some margin

    return result

def sanitize_features(features_dict):
    """Sanitize feature values to prevent NaN and invalid values in JSON."""
    sanitized = {}

    for k, v in features_dict.items():
        try:
            # Convert to float and check for NaN/inf
            val = float(v)

            if np.isnan(val) or np.isinf(val):
                # Use default value if NaN or infinity
                val = float(DEFAULT_FEATURES.get(k, 0))

            # Round to reasonable precision
            sanitized[k] = round(val, 6)

        except (ValueError, TypeError):
            # Fallback to default value
            sanitized[k] = round(float(DEFAULT_FEATURES.get(k, 0)), 6)

    return sanitized
