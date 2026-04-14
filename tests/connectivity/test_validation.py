import numpy as np
import cv2
from image_processor import extract_features
from image_validator import validate_medical_image

# Create a simple test image
test_img = np.zeros((200, 200, 3), dtype=np.uint8)
test_img[:] = (128, 128, 128)  # Gray background

# Add a simple circular 'tumor'
center = (100, 100)
cv2.circle(test_img, center, 30, (200, 100, 100), -1)

# Convert to bytes
_, img_bytes = cv2.imencode('.jpg', test_img)

print('Testing image validation...')
try:
    # Test feature extraction
    features = extract_features(img_bytes.tobytes())
    print(f'Features extracted: {len(features)}')
    
    # Test validation
    validation_result = validate_medical_image(img_bytes.tobytes(), features)
    print(f'Validation passed: {validation_result["is_valid"]}')
    print(f'Validation confidence: {validation_result["confidence"]:.2f}')
    if not validation_result['is_valid']:
        print(f'Rejection reasons: {validation_result["rejection_reasons"]}')
    
except Exception as e:
    print(f'Error: {e}')
