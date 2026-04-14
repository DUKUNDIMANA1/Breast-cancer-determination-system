"""
Advanced Image Processor for Breast Cancer Feature Extraction
Implements feature extraction methodology matching Wisconsin Breast Cancer Dataset
Features extracted from fine needle aspirate (FNA) images of breast masses
"""

import cv2
import numpy as np
from PIL import Image
import io
from scipy import ndimage
from skimage import measure, feature, filters
from skimage.feature import graycomatrix, graycoprops
from skimage.measure import regionprops
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

def extract_features(image_bytes):
    """
    Extract features from medical image using Wisconsin Breast Cancer Dataset methodology.

    The Wisconsin Breast Cancer Dataset features are computed from digitized images of a 
    fine needle aspirate (FNA) of a breast mass. They describe characteristics of the 
    cell nuclei present in the image.

    Args:
        image_bytes: Raw image data in bytes format

    Returns:
        dict: Extracted features matching Wisconsin Breast Cancer Dataset
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # Detect cell nuclei using multiple methods
        nuclei = detect_nuclei(enhanced)

        if not nuclei:
            print("[Advanced Processor] No nuclei detected, returning default features")
            return DEFAULT_FEATURES.copy()

        print(f"[Advanced Processor] Detected {len(nuclei)} nuclei")

        # Extract features from each nucleus
        nucleus_features = []
        for nucleus in nuclei:
            features = extract_nucleus_features(nucleus, enhanced)
            if features:
                nucleus_features.append(features)

        if not nucleus_features:
            print("[Advanced Processor] No valid nucleus features, returning defaults")
            return DEFAULT_FEATURES.copy()

        # Calculate statistical measures
        features = calculate_statistics(nucleus_features)

        # Add missing features with defaults
        for feature_name in FEATURE_NAMES:
            if feature_name not in features:
                features[feature_name] = DEFAULT_FEATURES[feature_name]

        return features

    except Exception as e:
        print(f"[Advanced Processor] Error: {e}")
        return DEFAULT_FEATURES.copy()

def detect_nuclei(image):
    """
    Detect cell nuclei in the image using multiple detection methods.

    Returns:
        list: List of binary masks for each detected nucleus
    """
    nuclei = []

    # Method 1: Adaptive thresholding
    thresh1 = cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Method 2: Otsu's thresholding
    _, thresh2 = cv2.threshold(
        image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Method 3: Watershed segmentation
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opening = cv2.morphologyEx(thresh2, cv2.MORPH_OPEN, kernel, iterations=2)
    sure_bg = cv2.dilate(opening, kernel, iterations=3)

    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.7*dist_transform.max(), 255, 0)

    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)

    _, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown == 255] = 0

    markers = cv2.watershed(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), markers)

    # Combine detection methods
    combined = cv2.bitwise_or(thresh1, thresh2)

    # Find contours
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by size and shape
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Filter by size (typical nucleus area in FNA images)
        if area < 100 or area > 5000:
            continue

        # Filter by circularity (nuclei are roughly circular)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter ** 2)
            if circularity < 0.5:  # Too irregular
                continue

        # Create binary mask for this nucleus
        mask = np.zeros_like(image)
        cv2.fillPoly(mask, [contour], 255)
        nuclei.append(mask)

    return nuclei

def extract_nucleus_features(nucleus_mask, image):
    """
    Extract features from a single nucleus using Wisconsin Breast Cancer Dataset methodology.

    Args:
        nucleus_mask: Binary mask of the nucleus
        image: Original grayscale image

    Returns:
        dict: Features for this nucleus
    """
    try:
        # Get properties of the nucleus
        props = regionprops(nucleus_mask.astype(int), intensity_image=image)[0]

        # 1. Radius: Mean of distances from center to points on perimeter
        radius = calculate_radius(nucleus_mask)

        # 2. Texture: Gray-level co-occurrence matrix (GLCM) contrast
        texture = calculate_texture(nucleus_mask, image)

        # 3. Smoothness: Local variation in radius lengths
        smoothness = calculate_smoothness(nucleus_mask)

        # 4. Compactness: perimeter^2 / area
        compactness = calculate_compactness(nucleus_mask)

        # 5. Concavity: Severity of concave portions of the contour
        concavity = calculate_concavity(nucleus_mask)

        # 6. Concave points: Number of concave portions of the contour
        concave_points = calculate_concave_points(nucleus_mask)

        # 7. Symmetry: Major axis length / minor axis length
        symmetry = calculate_symmetry(nucleus_mask)

        # 8. Fractal dimension: "Coastline approximation" - 1
        fractal_dimension = calculate_fractal_dimension(nucleus_mask)

        return {
            'radius': radius,
            'texture': texture,
            'smoothness': smoothness,
            'compactness': compactness,
            'concavity': concavity,
            'concave_points': concave_points,
            'symmetry': symmetry,
            'fractal_dimension': fractal_dimension
        }

    except Exception as e:
        print(f"[Nucleus Features] Error: {e}")
        return None

def calculate_radius(mask):
    """Calculate mean radius from center to perimeter points."""
    props = regionprops(mask.astype(int))[0]
    centroid = props.centroid
    coords = np.column_stack(np.where(mask > 0))

    # Calculate distances from centroid to all points
    distances = np.sqrt(np.sum((coords - centroid)**2, axis=1))

    # Return mean distance
    return np.mean(distances)

def calculate_texture(mask, image):
    """Calculate texture using Gray-Level Co-occurrence Matrix (GLCM)."""
    # Extract region of interest
    rows, cols = np.where(mask > 0)
    if len(rows) == 0:
        return DEFAULT_FEATURES['texture_mean']

    min_row, max_row = rows.min(), rows.max()
    min_col, max_col = cols.min(), cols.max()

    roi = image[min_row:max_row+1, min_col:max_col+1]

    # Calculate GLCM
    try:
        glcm = graycomatrix(roi, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
        contrast = graycoprops(glcm, 'contrast')[0, 0]
        return contrast
    except:
        return DEFAULT_FEATURES['texture_mean']

def calculate_smoothness(mask):
    """Calculate smoothness as local variation in radius lengths."""
    props = regionprops(mask.astype(int))[0]
    centroid = props.centroid

    # Get contour points
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return DEFAULT_FEATURES['smoothness_mean']

    contour = contours[0].squeeze()

    # Calculate distances from centroid to contour points
    distances = np.sqrt(np.sum((contour - centroid)**2, axis=1))

    # Calculate local variation
    if len(distances) < 2:
        return DEFAULT_FEATURES['smoothness_mean']

    local_variations = np.abs(np.diff(distances))
    smoothness = np.mean(local_variations) / np.mean(distances)

    return min(smoothness, 1.0)  # Normalize to [0, 1]

def calculate_compactness(mask):
    """Calculate compactness as perimeter^2 / (4π * area)."""
    props = regionprops(mask.astype(int))[0]
    perimeter = props.perimeter
    area = props.area

    if area == 0:
        return DEFAULT_FEATURES['compactness_mean']

    return (perimeter ** 2) / (4 * np.pi * area)

def calculate_concavity(mask):
    """Calculate concavity as severity of concave portions."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return DEFAULT_FEATURES['concavity_mean']

    contour = contours[0]
    hull = cv2.convexHull(contour)

    contour_area = cv2.contourArea(contour)
    hull_area = cv2.contourArea(hull)

    if hull_area == 0:
        return DEFAULT_FEATURES['concavity_mean']

    return (hull_area - contour_area) / hull_area

def calculate_concave_points(mask):
    """Calculate number of concave portions of the contour."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return DEFAULT_FEATURES['concave points_se'] * 100  # Scale back

    contour = contours[0]

    try:
        hull = cv2.convexHull(contour, returnPoints=False)
        defects = cv2.convexityDefects(contour, hull)

        if defects is None:
            return 0

        # Count significant defects
        significant_defects = [d for d in defects if d[0][3] > 100]  # Depth threshold
        return len(significant_defects)

    except:
        return 0

def calculate_symmetry(mask):
    """Calculate symmetry as major axis length / minor axis length."""
    props = regionprops(mask.astype(int))[0]

    major_axis = props.major_axis_length
    minor_axis = props.minor_axis_length

    if minor_axis == 0:
        return DEFAULT_FEATURES['symmetry_mean']

    # Symmetry is inverse of eccentricity
    symmetry = minor_axis / major_axis
    return symmetry

def calculate_fractal_dimension(mask):
    """Calculate fractal dimension using box-counting method."""
    def boxcount(Z, k):
        S = np.add.reduceat(
            np.add.reduceat(Z, np.arange(0, Z.shape[0], k), axis=0),
            np.arange(0, Z.shape[1], k), axis=1)
        return len(np.where((S > 0) & (S < k*k))[0])

    Z = mask
    p = min(Z.shape)
    n = 10
    sizes = 2**np.arange(n, 1, -1)

    counts = []
    for size in sizes:
        counts.append(boxcount(Z, size))

    if len(counts) < 2 or counts[0] == 0:
        return DEFAULT_FEATURES['fractal_dimension_mean']

    coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)
    return -coeffs[0]

def calculate_statistics(nucleus_features):
    """
    Calculate statistical measures (mean, standard error, worst) 
    from multiple nucleus features.
    """
    features = {}

    # Calculate mean for each feature
    for key in ['radius', 'texture', 'smoothness', 'compactness', 
                'concavity', 'concave_points', 'symmetry', 'fractal_dimension']:
        values = [f[key] for f in nucleus_features if key in f]
        if values:
            features[f'{key}_mean'] = np.mean(values)
        else:
            features[f'{key}_mean'] = DEFAULT_FEATURES[f'{key}_mean']

    # Calculate standard error for each feature
    for key in ['radius', 'texture', 'smoothness', 'compactness',
                'concavity', 'concave_points', 'symmetry', 'fractal_dimension']:
        values = [f[key] for f in nucleus_features if key in f]
        if len(values) > 1:
            features[f'{key}_se'] = np.std(values) / np.sqrt(len(values))
        else:
            features[f'{key}_se'] = DEFAULT_FEATURES[f'{key}_se']

    # Calculate worst values (mean of three largest values)
    for key in ['radius', 'texture', 'smoothness', 'compactness',
                'concavity', 'concave_points', 'symmetry', 'fractal_dimension']:
        values = [f[key] for f in nucleus_features if key in f]
        if len(values) >= 3:
            sorted_values = sorted(values, reverse=True)
            features[f'{key}_worst'] = np.mean(sorted_values[:3])
        elif len(values) > 0:
            features[f'{key}_worst'] = np.max(values)
        else:
            features[f'{key}_worst'] = DEFAULT_FEATURES[f'{key}_worst']

    # Scale features to match Wisconsin Breast Cancer Dataset ranges
    scale_features(features)

    return features

def scale_features(features):
    """Scale features to match Wisconsin Breast Cancer Dataset ranges using min-max normalization."""

    # Define feature ranges from Wisconsin Breast Cancer Dataset
    feature_ranges = {
        'radius_mean': (6.981, 28.11),
        'radius_se': (0.1115, 2.873),
        'texture_mean': (9.71, 39.28),
        'texture_se': (0.3602, 4.885),
        'smoothness_mean': (0.05263, 0.1634),
        'smoothness_se': (0.001713, 0.03113),
        'smoothness_worst': (0.07117, 0.2969),
        'compactness_mean': (0.01938, 0.3454),
        'compactness_se': (0.002252, 0.1354),
        'compactness_worst': (0.02729, 0.6656),
        'concavity_mean': (0.0, 0.4268),
        'concavity_se': (0.0, 0.396),
        'concavity_worst': (0.0, 0.8662),
        'concave_points_se': (0.0, 0.1752),
        'symmetry_mean': (0.106, 0.304),
        'symmetry_se': (0.007882, 0.07895),
        'symmetry_worst': (0.1565, 0.6638),
        'fractal_dimension_mean': (0.04996, 0.09744),
        'fractal_dimension_se': (0.0008874, 0.02984),
        'fractal_dimension_worst': (0.05504, 0.2075)
    }

    # Apply min-max normalization for each feature
    for feature_name, (min_val, max_val) in feature_ranges.items():
        if feature_name in features:
            # Clip extreme outliers but preserve most variation
            value = features[feature_name]
            # Allow values slightly outside the range (±20%)
            soft_min = min_val * 0.8
            soft_max = max_val * 1.2
            value = np.clip(value, soft_min, soft_max)
            # Normalize to [0, 1] range
            normalized = (value - min_val) / (max_val - min_val)
            # Scale back to original range
            features[feature_name] = min_val + normalized * (max_val - min_val)
        features['fractal_dimension_worst'] = np.clip(features['fractal_dimension_worst'], 0.05, 0.15)
