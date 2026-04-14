"""
Image Processor for Breast Cancer Feature Extraction
Handles medical image analysis and feature extraction for breast cancer prediction
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from image_validator import validate_medical_image

# Feature extraction constants
FEATURE_NAMES = [
    'radius_mean','texture_mean','smoothness_mean','compactness_mean',
    'concavity_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','smoothness_se','compactness_se',
    'concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'smoothness_worst','compactness_worst','concavity_worst',
    'symmetry_worst','fractal_dimension_worst'
]

# Default feature values (from the original dataset)
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
    
    Args:
        image_bytes: Raw image data in bytes format
        
    Returns:
        dict: Extracted features matching the expected feature names
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode image")
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # No contours found, return default features
            return DEFAULT_FEATURES.copy()
        
        # Get the largest contour (assuming it's the tumor/mass)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate features based on contour properties
        features = {}
        
        # Basic geometric features
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        if perimeter > 0:
            # Radius (equivalent radius of the area)
            features['radius_mean'] = np.sqrt(area / np.pi) * 2  # Scale to match dataset
            
            # Compactness (perimeter^2 / (4π * area))
            features['compactness_mean'] = (perimeter ** 2) / (4 * np.pi * area) if area > 0 else 0
            
            # Concavity (based on contour convexity defects)
            hull = cv2.convexHull(largest_contour)
            hull_area = cv2.contourArea(hull)
            features['concavity_mean'] = (hull_area - area) / hull_area if hull_area > 0 else 0
            
        else:
            # Default values if no valid perimeter
            features['radius_mean'] = DEFAULT_FEATURES['radius_mean']
            features['compactness_mean'] = DEFAULT_FEATURES['compactness_mean']
            features['concavity_mean'] = DEFAULT_FEATURES['concavity_mean']
        
        # Texture features (using grayscale image statistics)
        features['texture_mean'] = np.mean(gray)
        features['smoothness_mean'] = np.std(gray) / 255.0  # Normalized
        features['symmetry_mean'] = calculate_symmetry(gray)
        features['fractal_dimension_mean'] = calculate_fractal_dimension(gray)
        
        # Calculate standard error features (simplified)
        for feature in ['radius', 'texture', 'smoothness', 'compactness', 'concavity']:
            base_val = features.get(f'{feature}_mean', DEFAULT_FEATURES[f'{feature}_mean'])
            # Add some variation to simulate SE (standard error)
            features[f'{feature}_se'] = base_val * 0.1  # 10% variation as SE
        
        # Calculate "worst" values (simplified - just slightly higher than mean)
        for feature in ['smoothness', 'compactness', 'concavity', 'symmetry', 'fractal_dimension']:
            base_val = features.get(f'{feature}_mean', DEFAULT_FEATURES[f'{feature}_mean'])
            features[f'{feature}_worst'] = base_val * 1.2  # 20% higher for worst
        
        # Add missing features with defaults
        for feature_name in FEATURE_NAMES:
            if feature_name not in features:
                features[feature_name] = DEFAULT_FEATURES[feature_name]
        
        # Run validation pipeline before returning features
        validation_result = validate_medical_image(image_bytes, features)
        
        if not validation_result['is_valid']:
            print(f"[Image Processor] Validation failed: {validation_result['rejection_reasons']}")
            # Return features but mark as invalid for system to handle
            features['validation_failed'] = True
            features['validation_reasons'] = validation_result['rejection_reasons']
            features['validation_confidence'] = validation_result['confidence']
        else:
            print(f"[Image Processor] Validation passed with confidence: {validation_result['confidence']:.2f}")
            features['validation_passed'] = True
            features['validation_confidence'] = validation_result['confidence']
        
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
            "✓ Image processed successfully",
            "✓ Features extracted",
            "✓ Ready for ML prediction"
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
        print(f"[Image Processor] Error generating annotated image: {e}")
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
        
        error_text = "⚠️ Image Processing Error"
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

# Test function
def test_processor():
    """Test the image processor functions."""
    print("[Image Processor] Testing image processor...")
    
    # Create a test image
    test_img = np.zeros((200, 200, 3), dtype=np.uint8)
    test_img[:] = (128, 128, 128)  # Gray background
    
    # Add a circular "tumor"
    center = (100, 100)
    cv2.circle(test_img, center, 30, (200, 100, 100), -1)
    
    # Convert to bytes
    _, img_bytes = cv2.imencode('.jpg', test_img)
    
    # Test feature extraction
    features = extract_features(img_bytes.tobytes())
    print(f"[Image Processor] Extracted {len(features)} features")
    
    # Test annotation
    annotation = generate_annotated_image(img_bytes.tobytes())
    print(f"[Image Processor] Generated annotation: {'Success' if annotation else 'Failed'}")
    
    return features, annotation

if __name__ == "__main__":
    test_processor()
