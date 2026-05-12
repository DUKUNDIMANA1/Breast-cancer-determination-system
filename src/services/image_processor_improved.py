"""
Improved Image Processor for Breast Cancer Feature Extraction
Handles medical image analysis and feature extraction for breast cancer prediction
This version better matches the Wisconsin Breast Cancer dataset feature extraction
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# Feature extraction constants
FEATURE_NAMES = [
    'radius_mean','texture_mean','smoothness_mean','compactness_mean',
    'concavity_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','smoothness_se','compactness_se',
    'concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'smoothness_worst','compactness_worst','concavity_worst',
    'symmetry_worst','fractal_dimension_worst'
]

# Default feature values (from original dataset)
DEFAULT_FEATURES = {
    'radius_mean':13.37,'texture_mean':18.84,'smoothness_mean':0.0962,
    'compactness_mean':0.1043,'concavity_mean':0.0888,'symmetry_mean':0.1812,
    'fractal_dimension_mean':0.0628,'radius_se':0.4051,'texture_se':1.2169,
    'smoothness_se':0.00638,'compactness_se':0.0210,'concavity_se':0.0259,
    'concave points_se':0.0111,'symmetry_se':0.0207,'fractal_dimension_se':0.00380,
    'smoothness_worst':0.1323,'compactness_worst':0.2534,'concavity_worst':0.2720,
    'symmetry_worst':0.2900,'fractal_dimension_worst':0.0839
}

def extract_features(image_bytes):
    """
    Extract features from medical image for breast cancer prediction.
    This implementation uses multiple contours to simulate cell nuclei analysis.

    Args:
        image_bytes: Raw image data in bytes format

    Returns:
        dict: Extracted features matching expected feature names
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image")

        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding to better handle varying lighting
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        # Find contours (potential cell nuclei)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            print("[Image Processor] No contours found, returning default features")
            return DEFAULT_FEATURES.copy()

        # Filter contours by size to focus on cell-like structures
        # Cell nuclei typically have area between 100 and 5000 pixels
        filtered_contours = [c for c in contours if 100 < cv2.contourArea(c) < 5000]

        if not filtered_contours:
            print("[Image Processor] No valid cell-like contours found, returning default features")
            return DEFAULT_FEATURES.copy()

        # Calculate features for each contour (cell nucleus)
        contour_features = []
        for contour in filtered_contours:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)

            if perimeter == 0 or area == 0:
                continue

            # Radius (equivalent radius of area)
            radius = np.sqrt(area / np.pi)

            # Compactness (perimeter^2 / (4π * area))
            compactness = (perimeter ** 2) / (4 * np.pi * area)

            # Concavity (based on contour convexity defects)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            concavity = (hull_area - area) / hull_area if hull_area > 0 else 0

            # Concave points (number of convexity defects)
            try:
                defects = cv2.convexityDefects(contour, cv2.convexHull(contour, returnPoints=False))
                concave_points = len(defects) if defects is not None else 0
            except:
                concave_points = 0

            # Symmetry (using moment-based approach)
            M = cv2.moments(contour)
            if M['m00'] > 0:
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                # Calculate symmetry by comparing left and right halves
                left_half = gray[int(cy-50):int(cy+50), int(cx-50):int(cx)]
                right_half = cv2.flip(gray[int(cy-50):int(cy+50), int(cx):int(cx+50)], 1)
                if left_half.size > 0 and right_half.size > 0:
                    min_shape = min(left_half.shape, right_half.shape)
                    left_half = left_half[:min_shape[0], :min_shape[1]]
                    right_half = right_half[:min_shape[0], :min_shape[1]]
                    diff = cv2.absdiff(left_half, right_half)
                    symmetry = 1.0 - (np.mean(diff) / 255.0)
                else:
                    symmetry = 0.5
            else:
                symmetry = 0.5

            # Fractal dimension (simplified box-counting)
            try:
                x, y, w, h = cv2.boundingRect(contour)
                roi = gray[y:y+h, x:x+w]
                if roi.size > 0:
                    fractal_dim = calculate_fractal_dimension(roi)
                else:
                    fractal_dim = DEFAULT_FEATURES['fractal_dimension_mean']
            except:
                fractal_dim = DEFAULT_FEATURES['fractal_dimension_mean']

            # Texture (using GLCM-like statistics)
            x, y, w, h = cv2.boundingRect(contour)
            roi = gray[y:y+h, x:x+w]
            if roi.size > 0:
                texture = np.std(roi) / 255.0
            else:
                texture = DEFAULT_FEATURES['texture_mean'] / 255.0

            contour_features.append({
                'radius': radius,
                'texture': texture,
                'smoothness': 1.0 - compactness,
                'compactness': compactness,
                'concavity': concavity,
                'concave_points': concave_points,
                'symmetry': symmetry,
                'fractal_dimension': fractal_dim
            })

        if not contour_features:
            print("[Image Processor] No valid contour features calculated, returning defaults")
            return DEFAULT_FEATURES.copy()

        # Calculate mean values
        features = {}
        for key in ['radius', 'texture', 'smoothness', 'compactness', 'concavity', 'concave_points', 'symmetry', 'fractal_dimension']:
            values = [f[key] for f in contour_features if key in f]
            if values:
                features[f'{key}_mean'] = np.mean(values)
                # Scale to match dataset ranges
                if key == 'radius':
                    features[f'{key}_mean'] *= 1.5  # Scale factor for radius
                elif key == 'texture':
                    features[f'{key}_mean'] *= 255.0  # Scale texture back
                elif key == 'concave_points':
                    features[f'{key}_mean'] *= 0.01  # Scale concave points
            else:
                features[f'{key}_mean'] = DEFAULT_FEATURES[f'{key}_mean']

        # Calculate standard error (SE) values
        for key in ['radius', 'texture', 'smoothness', 'compactness', 'concavity', 'concave_points', 'symmetry', 'fractal_dimension']:
            values = [f[key] for f in contour_features if key in f]
            if values:
                features[f'{key}_se'] = np.std(values) / np.sqrt(len(values))
                # Apply same scaling as mean values
                if key == 'radius':
                    features[f'{key}_se'] *= 1.5
                elif key == 'texture':
                    features[f'{key}_se'] *= 255.0
                elif key == 'concave_points':
                    features[f'{key}_se'] *= 0.01
            else:
                features[f'{key}_se'] = DEFAULT_FEATURES[f'{key}_se']

        # Calculate worst values (top 25% most extreme values)
        for key in ['smoothness', 'compactness', 'concavity', 'symmetry', 'fractal_dimension']:
            values = [f[key] for f in contour_features if key in f]
            if values:
                sorted_values = sorted(values, reverse=True)
                worst_idx = int(len(sorted_values) * 0.25)
                worst_values = sorted_values[:max(1, worst_idx)]
                features[f'{key}_worst'] = np.mean(worst_values)
            else:
                features[f'{key}_worst'] = DEFAULT_FEATURES[f'{key}_worst']

        # Add missing features with defaults
        for feature_name in FEATURE_NAMES:
            if feature_name not in features:
                features[feature_name] = DEFAULT_FEATURES[feature_name]

        # Validation module removed - features returned without validation
        print(f"[Image Processor Improved] Features extracted successfully")

        return features

    except Exception as e:
        print(f"[Image Processor] Error extracting features: {e}")
        error_features = DEFAULT_FEATURES.copy()
        error_features['validation_failed'] = True
        error_features['validation_reasons'] = [f"Processing error: {str(e)}"]
        error_features['validation_confidence'] = 0.0
        return error_features

def calculate_symmetry(gray_image):
    """Calculate symmetry measure of grayscale image."""
    h, w = gray_image.shape
    left_half = gray_image[:, :w//2]
    right_half = cv2.flip(gray_image[:, w//2:], 1)

    # Resize to match if dimensions don't align
    min_width = min(left_half.shape[1], right_half.shape[1])
    left_half = left_half[:, :min_width]
    right_half = right_half[:, :min_width]

    # Calculate difference
    diff = cv2.absdiff(left_half, right_half)
    symmetry_score = 1.0 - (np.mean(diff) / 255.0)

    return max(0.0, min(1.0, symmetry_score))

def calculate_fractal_dimension(gray_image):
    """Calculate simplified fractal dimension."""
    # Simplified box-counting method
    sizes = [2, 4, 8, 16]
    counts = []

    for size in sizes:
        h, w = gray_image.shape
        h_box, w_box = h // size, w // size

        # Count non-empty boxes
        boxes = 0
        for i in range(0, h_box):
            for j in range(0, w_box):
                box = gray_image[i*size:(i+1)*size, j*size:(j+1)*size]
                if np.any(box > 0):
                    boxes += 1
        counts.append(boxes)

    # Calculate fractal dimension
    if len(counts) > 1 and counts[0] > 0:
        coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)
        return -coeffs[0]  # Negative slope is fractal dimension

    return DEFAULT_FEATURES['fractal_dimension_mean']

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

        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by size
        filtered_contours = [c for c in contours if 100 < cv2.contourArea(c) < 5000]

        # Draw contours on original image
        annotated = img.copy()
        for contour in filtered_contours:
            # Draw contour in green
            cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)

            # Draw convex hull in blue
            hull = cv2.convexHull(contour)
            cv2.drawContours(annotated, [hull], -1, (255, 0, 0), 1)

            # Calculate and display features
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)

            # Calculate center
            M = cv2.moments(contour)
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                # Display radius
                radius = np.sqrt(area / np.pi)
                cv2.putText(annotated, f"R:{radius:.1f}", (cx, cy), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Convert to base64
        _, buffer = cv2.imencode('.jpg', annotated)
        img_str = base64.b64encode(buffer).decode('utf-8')

        return img_str

    except Exception as e:
        print(f"[Image Processor] Error generating annotated image: {e}")
        return None
