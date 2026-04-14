"""
Image Validation Module for Breast Cancer Prediction System
Implements multistage validation pipeline to prevent non-medical images
"""
import io
import numpy as np
import cv2
from PIL import Image, ImageStat
import joblib
from sklearn.covariance import EmpiricalCovariance
from scipy.spatial.distance import mahalanobis
from scipy.spatial.distance import cosine
import warnings
warnings.filterwarnings('ignore')

class MedicalImageValidator:
    def __init__(self):
        self.ood_threshold = 0.3  # Reduced OOD threshold - more permissive
        self.mahalanobis_threshold = 1000.0  # Increased Mahalanobis threshold - more permissive
        self.reconstruction_threshold = 0.3  # Increased reconstruction threshold - more permissive
        self.medical_classifier_threshold = 0.5  # Reduced medical classifier threshold - more permissive
        
        # Load pre-trained models (these would be trained separately)
        self.feature_mean = None
        self.feature_cov = None
        self.autoencoder = None
        self.medical_classifier = None
        
        # Initialize with training data statistics
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize validation models with training data statistics"""
        try:
            # Load training feature statistics (would be computed from training dataset)
            self.feature_mean = np.array([
                15.0,  # radius_mean
                18.0,  # texture_mean
                0.1,   # perimeter_mean
                0.2,   # area_mean
                0.001, # smoothness_mean
                0.002, # compactness_mean
                0.15,  # concavity_mean
                0.25,  # concave_points_mean
                0.1,   # symmetry_mean
                0.3,   # fractal_dimension_mean
                20.0,  # radius_se
                25.0,  # texture_se
                0.15,  # perimeter_se
                0.3,   # area_se
                0.003, # smoothness_se
                0.004, # compactness_se
                0.2,   # concavity_se
                0.35,  # concave_points_se
                0.15,  # symmetry_se
                0.4    # fractal_dimension_se
            ])
            
            # Initialize covariance matrix (simplified for demo)
            self.feature_cov = np.eye(20) * 0.1
            
        except Exception as e:
            print(f"Warning: Could not initialize models: {e}")
            # Fallback to default values
            self.feature_mean = np.zeros(20)
            self.feature_cov = np.eye(20)
    
    def validate_image_pipeline(self, image_bytes, features):
        """
        Run complete validation pipeline
        Returns: dict with validation results and overall decision
        """
        validation_results = {
            'is_valid': True,
            'rejection_reasons': [],
            'confidence': 1.0,
            'stage_results': {}
        }
        
        try:
            # Stage 1: Basic Image Properties Check
            basic_check = self._basic_image_validation(image_bytes)
            validation_results['stage_results']['basic_validation'] = basic_check
            
            if not basic_check['passed']:
                validation_results['is_valid'] = False
                validation_results['rejection_reasons'].append(basic_check['reason'])
                return validation_results
            
            # Stage 2: Out-of-Distribution Detection (MSP)
            ood_result = self._ood_detection(features)
            validation_results['stage_results']['ood_detection'] = ood_result
            
            if not ood_result['is_in_distribution']:
                validation_results['is_valid'] = False
                validation_results['rejection_reasons'].append(ood_result['reason'])
                validation_results['confidence'] *= ood_result['confidence']
            
            # Stage 3: Feature-based Detection (Mahalanobis)
            mahalanobis_result = self._mahalanobis_detection(features)
            validation_results['stage_results']['mahalanobis'] = mahalanobis_result
            
            if not mahalanobis_result['is_valid']:
                validation_results['is_valid'] = False
                validation_results['rejection_reasons'].append(mahalanobis_result['reason'])
                validation_results['confidence'] *= mahalanobis_result['confidence']
            
            # Stage 4: Medical Image Classification
            medical_result = self._medical_image_classification(image_bytes)
            validation_results['stage_results']['medical_classification'] = medical_result
            
            if not medical_result['is_medical']:
                validation_results['is_valid'] = False
                validation_results['rejection_reasons'].append(medical_result['reason'])
                validation_results['confidence'] *= medical_result['confidence']
            
            # Stage 5: Anatomical Verification (simplified)
            anatomical_result = self._anatomical_verification(image_bytes)
            validation_results['stage_results']['anatomical'] = anatomical_result
            
            if not anatomical_result['has_breast_region']:
                validation_results['is_valid'] = False
                validation_results['rejection_reasons'].append(anatomical_result['reason'])
                validation_results['confidence'] *= anatomical_result['confidence']
            
        except Exception as e:
            validation_results['is_valid'] = False
            validation_results['rejection_reasons'].append(f"Validation error: {str(e)}")
            validation_results['confidence'] = 0.0
        
        return validation_results
    
    def _basic_image_validation(self, image_bytes):
        """Basic image properties validation"""
        try:
            # Convert to PIL Image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Check image format and properties
            if img.format not in ['JPEG', 'PNG', 'TIFF', 'DICOM']:
                return {
                    'passed': False,
                    'reason': f"Unsupported image format: {img.format}",
                    'confidence': 0.1
                }
            
            # Check image size (more permissive range)
            width, height = img.size
            if width < 50 or height < 50 or width > 4000 or height > 4000:
                return {
                    'passed': False,
                    'reason': f"Invalid image dimensions: {width}x{height}",
                    'confidence': 0.3
                }
            
            # Check color properties (more permissive - allow RGBA with warning)
            if img.mode == 'RGBA':
                # Convert RGBA to RGB for processing
                img = img.convert('RGB')
            
            # Basic histogram analysis for medical image characteristics
            img_array = np.array(img)
            if len(img_array.shape) == 3:  # RGB
                # Check for typical medical image color distribution (more permissive)
                mean_intensity = np.mean(img_array)
                if mean_intensity > 240 or mean_intensity < 15:
                    return {
                        'passed': False,
                        'reason': "Extreme intensity distribution",
                        'confidence': 0.3
                    }
            
            return {
                'passed': True,
                'reason': "Basic validation passed",
                'confidence': 0.9
            }
            
        except Exception as e:
            return {
                'passed': False,
                'reason': f"Image processing error: {str(e)}",
                'confidence': 0.0
            }
    
    def _ood_detection(self, features):
        """Out-of-Distribution detection using Maximum Softmax Probability"""
        try:
            # Simulate softmax probabilities (in real implementation, this comes from model)
            # For demo, we'll create mock probabilities
            feature_vector = np.array(list(features.values()))
            
            # Normalize features
            feature_vector = (feature_vector - np.mean(feature_vector)) / (np.std(feature_vector) + 1e-8)
            
            # Mock softmax probabilities (in real implementation, get from model)
            # Higher values indicate more "cancer-like" features
            cancer_prob = min(0.95, max(0.05, np.mean(feature_vector) / 30))
            normal_prob = 1 - cancer_prob
            uncertain_prob = 0.05  # Small uncertainty probability
            
            max_prob = max(cancer_prob, normal_prob)
            
            is_in_distribution = max_prob >= self.ood_threshold
            
            return {
                'is_in_distribution': is_in_distribution,
                'max_probability': max_prob,
                'probabilities': {
                    'malignant': cancer_prob,
                    'benign': normal_prob,
                    'uncertain': uncertain_prob
                },
                'reason': f"Max probability {max_prob:.3f} below threshold {self.ood_threshold}" if not is_in_distribution else "In distribution",
                'confidence': min(max_prob / self.ood_threshold, 1.0) if is_in_distribution else max_prob / self.ood_threshold
            }
            
        except Exception as e:
            return {
                'is_in_distribution': False,
                'reason': f"OOD detection error: {str(e)}",
                'confidence': 0.0
            }
    
    def _mahalanobis_detection(self, features):
        """Feature-based detection using Mahalanobis distance"""
        try:
            feature_vector = np.array(list(features.values()))
            
            if self.feature_mean is None or self.feature_cov is None:
                return {
                    'is_valid': True,
                    'distance': 0,
                    'reason': "Mahalanobis model not initialized",
                    'confidence': 0.5
                }
            
            # Calculate Mahalanobis distance
            try:
                inv_cov = np.linalg.inv(self.feature_cov)
                distance = mahalanobis(feature_vector, self.feature_mean, inv_cov)
            except:
                distance = np.linalg.norm(feature_vector - self.feature_mean)
            
            is_valid = distance <= self.mahalanobis_threshold
            
            return {
                'is_valid': is_valid,
                'distance': distance,
                'threshold': self.mahalanobis_threshold,
                'reason': f"Mahalanobis distance {distance:.2f} exceeds threshold {self.mahalanobis_threshold}" if not is_valid else "Within expected feature distribution",
                'confidence': max(0.1, 1.0 - (distance / (self.mahalanobis_threshold * 2)))
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'reason': f"Mahalanobis detection error: {str(e)}",
                'confidence': 0.0
            }
    
    def _medical_image_classification(self, image_bytes):
        """Binary classifier to distinguish medical vs non-medical images"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(img)
            
            # Simple heuristic-based medical image detection
            # In real implementation, this would be a trained CNN classifier
            
            # Feature 1: Aspect ratio analysis
            width, height = img.size
            aspect_ratio = width / height
            
            # Feature 2: Texture complexity
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Calculate texture features
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Feature 3: Edge density
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
            
            # Feature 4: Intensity distribution
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_normalized = hist.flatten() / hist.sum()
            intensity_entropy = -np.sum(hist_normalized * np.log2(hist_normalized + 1e-8))
            
            # Simple scoring function (trained classifier would be better)
            medical_score = 0.0
            
            # Medical images typically have:
            # - Reasonable aspect ratios (0.3 to 3.0) - more permissive
            if 0.3 <= aspect_ratio <= 3.0:
                medical_score += 0.25
            
            # - Moderate texture complexity (reduced threshold)
            if laplacian_var > 5:
                medical_score += 0.25
            
            # - Reasonable edge density (wider range)
            if 0.02 <= edge_density <= 0.4:
                medical_score += 0.25
            
            # - Moderate entropy (reduced threshold)
            if intensity_entropy > 2.0:
                medical_score += 0.25
            
            is_medical = medical_score >= self.medical_classifier_threshold
            
            return {
                'is_medical': is_medical,
                'medical_score': medical_score,
                'features': {
                    'aspect_ratio': aspect_ratio,
                    'texture_variance': laplacian_var,
                    'edge_density': edge_density,
                    'intensity_entropy': intensity_entropy
                },
                'reason': f"Medical image score {medical_score:.2f} below threshold {self.medical_classifier_threshold}" if not is_medical else "Classified as medical image",
                'confidence': medical_score
            }
            
        except Exception as e:
            return {
                'is_medical': False,
                'reason': f"Medical classification error: {str(e)}",
                'confidence': 0.0
            }
    
    def _anatomical_verification(self, image_bytes):
        """Anatomical verification to detect breast region"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(img)
            
            # Convert to grayscale for processing
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Simple anatomical detection heuristics
            # In real implementation, this would use a trained U-Net segmentation model
            
            # Feature 1: Circular/elliptical structure detection
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, 100, 50, 150)
            
            # Feature 2: Tissue-like texture patterns
            # Use Gabor filters to detect tissue patterns
            def gabor_kernel(size, theta, sigma, gamma, psi):
                # Simplified Gabor filter
                kernel = np.zeros((size, size))
                for x in range(size):
                    for y in range(size):
                        dx = x - size // 2
                        dy = y - size // 2
                        g = np.exp(-(dx**2 + gamma**2 * dy**2) / (2 * sigma**2))
                        kernel[x, y] = g * np.cos(2 * np.pi * dx / size + psi)
                return kernel
            
            # Apply multiple Gabor filters
            tissue_response = 0
            for theta in [0, 45, 90, 135]:
                kernel = gabor_kernel(15, theta, 3, 0.5, 0)
                filtered = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
                tissue_response += np.std(filtered)
            
            # Feature 3: Density distribution
            # Medical breast images typically have specific density patterns
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            density_score = np.sum(hist[50:200]) / np.sum(hist)  # Mid-range density
            
            # Combine features for anatomical confidence
            anatomical_score = 0.0
            
            # Circle detection (breast masses often appear circular)
            if circles is not None and len(circles) > 0:
                anatomical_score += 0.3
            
            # Tissue-like patterns
            if tissue_response / 4 > 20:
                anatomical_score += 0.3
            
            # Appropriate density distribution
            if 0.3 <= density_score <= 0.7:
                anatomical_score += 0.4
            
            has_breast_region = anatomical_score >= 0.5
            
            return {
                'has_breast_region': has_breast_region,
                'anatomical_score': anatomical_score,
                'features': {
                    'circles_detected': len(circles) if circles is not None else 0,
                    'tissue_response': tissue_response / 4,
                    'density_score': density_score
                },
                'reason': f"Anatomical score {anatomical_score:.2f} below threshold 0.5" if not has_breast_region else "Breast region detected",
                'confidence': anatomical_score
            }
            
        except Exception as e:
            return {
                'has_breast_region': False,
                'reason': f"Anatomical verification error: {str(e)}",
                'confidence': 0.0
            }

# Global validator instance
medical_validator = MedicalImageValidator()

def validate_medical_image(image_bytes, features):
    """
    Main validation function to be called from image_processor
    """
    return medical_validator.validate_image_pipeline(image_bytes, features)
