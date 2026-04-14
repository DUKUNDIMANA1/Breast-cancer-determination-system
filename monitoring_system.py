"""
Monitoring System for Breast Cancer Prediction System
Implements continuous monitoring and drift detection for model performance and data quality
"""

import numpy as np
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

class ModelMonitor:
    def __init__(self):
        self.prediction_history = deque(maxlen=1000)  # Last 1000 predictions
        self.validation_failures = deque(maxlen=100)  # Last 100 validation failures
        self.feature_statistics = defaultdict(list)
        self.confidence_scores = deque(maxlen=500)  # Last 500 confidence scores
        self.rejection_reasons = defaultdict(int)
        self.drift_threshold = 0.15  # Threshold for drift detection
        self.performance_window = 100  # Window for performance calculation
        
        # Initialize monitoring metrics
        self.start_time = datetime.now()
        self.total_predictions = 0
        self.total_rejections = 0
        self.total_validations = 0
        
    def log_prediction(self, features, validation_result, prediction_confidence=None):
        """Log prediction with validation results"""
        timestamp = datetime.now()
        
        # Update counters
        self.total_predictions += 1
        self.total_validations += 1
        
        # Log prediction details
        prediction_log = {
            'timestamp': timestamp.isoformat(),
            'validation_passed': validation_result['is_valid'],
            'validation_confidence': validation_result['confidence'],
            'rejection_reasons': validation_result['rejection_reasons'],
            'stage_results': validation_result.get('stage_results', {}),
            'prediction_confidence': prediction_confidence
        }
        
        self.prediction_history.append(prediction_log)
        
        # Update feature statistics
        if validation_result['is_valid']:
            for feature_name, feature_value in features.items():
                if isinstance(feature_value, (int, float)):
                    self.feature_statistics[feature_name].append(feature_value)
        
        # Update confidence scores
        if prediction_confidence is not None:
            self.confidence_scores.append(prediction_confidence)
        
        # Track rejection reasons
        if not validation_result['is_valid']:
            self.total_rejections += 1
            for reason in validation_result['rejection_reasons']:
                self.rejection_reasons[reason] += 1
        
        return prediction_log
    
    def detect_drift(self):
        """Detect data drift using multiple methods"""
        if len(self.prediction_history) < 50:
            return {
                'drift_detected': False,
                'reason': 'Insufficient data for drift detection',
                'metrics': {}
            }
        
        drift_metrics = {}
        drift_detected = False
        drift_reasons = []
        
        # Method 1: Validation failure rate drift
        recent_predictions = list(self.prediction_history)[-100:]  # Last 100 predictions
        recent_failures = [p for p in recent_predictions if not p['validation_passed']]
        failure_rate = len(recent_failures) / len(recent_predictions)
        
        if failure_rate > self.drift_threshold:
            drift_detected = True
            drift_reasons.append(f"High validation failure rate: {failure_rate:.3f}")
        
        drift_metrics['validation_failure_rate'] = failure_rate
        
        # Method 2: Confidence score drift
        if len(self.confidence_scores) >= 50:
            recent_confidence = list(self.confidence_scores)[-50:]
            old_confidence = list(self.confidence_scores)[-100:-50] if len(self.confidence_scores) >= 100 else []
            
            if old_confidence:
                confidence_change = np.mean(recent_confidence) - np.mean(old_confidence)
                if abs(confidence_change) > 0.1:
                    drift_detected = True
                    drift_reasons.append(f"Confidence score drift: {confidence_change:.3f}")
            
            drift_metrics['confidence_drift'] = confidence_change
        
        # Method 3: Feature distribution drift
        for feature_name, values in self.feature_statistics.items():
            if len(values) >= 30:  # Need sufficient samples
                recent_values = values[-30:]
                old_values = values[-60:-30] if len(values) >= 60 else []
                
                if old_values:
                    recent_mean = np.mean(recent_values)
                    old_mean = np.mean(old_values)
                    
                    # Calculate relative change
                    if old_mean != 0:
                        relative_change = abs(recent_mean - old_mean) / abs(old_mean)
                        if relative_change > 0.2:  # 20% change threshold
                            drift_detected = True
                            drift_reasons.append(f"Feature drift in {feature_name}: {relative_change:.3f}")
                    
                    drift_metrics[f'{feature_name}_drift'] = relative_change
        
        return {
            'drift_detected': drift_detected,
            'reasons': drift_reasons,
            'metrics': drift_metrics,
            'monitoring_period': str(datetime.now() - self.start_time),
            'total_predictions': self.total_predictions,
            'total_rejections': self.total_rejections,
            'rejection_rate': self.total_rejections / max(1, self.total_predictions)
        }
    
    def get_performance_metrics(self):
        """Get current performance metrics"""
        if len(self.prediction_history) == 0:
            return {
                'status': 'No data',
                'message': 'No predictions logged yet',
                'total_predictions': 0,
                'validation_passed_count': 0,
                'validation_failed_count': 0,
                'validation_pass_rate': 0.0,
                'average_validation_confidence': 0.0,
                'average_prediction_confidence': 0.0,
                'rejection_rate': 0.0,
                'rejection_reasons': {}
            }
        
        recent_predictions = list(self.prediction_history)[-self.performance_window:]
        
        # Calculate metrics
        validation_passed = [p for p in recent_predictions if p['validation_passed']]
        validation_failed = [p for p in recent_predictions if not p['validation_passed']]
        
        metrics = {
            'total_predictions': len(recent_predictions),
            'validation_passed_count': len(validation_passed),
            'validation_failed_count': len(validation_failed),
            'validation_pass_rate': len(validation_passed) / len(recent_predictions),
            'average_validation_confidence': np.mean([p['validation_confidence'] for p in recent_predictions]),
            'average_prediction_confidence': np.mean([p['prediction_confidence'] for p in recent_predictions if p['prediction_confidence'] is not None]),
            'monitoring_period': str(datetime.now() - self.start_time),
            'rejection_reasons': dict(self.rejection_reasons)
        }
        
        # Stage-specific metrics
        for stage in ['basic_validation', 'ood_detection', 'mahalanobis', 'medical_classification', 'anatomical']:
            stage_results = [p['stage_results'].get(stage, {}) for p in recent_predictions]
            stage_passed = [sr for sr in stage_results if sr.get('passed', True)]
            metrics[f'{stage}_pass_rate'] = len(stage_passed) / len(stage_results) if stage_results else 0
        
        return metrics
    
    def generate_alert(self, drift_result):
        """Generate alert for detected drift"""
        if drift_result['drift_detected']:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'severity': 'HIGH',
                'type': 'DATA_DRIFT_DETECTED',
                'message': 'Data drift detected in breast cancer prediction system',
                'details': drift_result,
                'recommendations': [
                    'Review recent validation failures',
                    'Check data source integrity',
                    'Consider model retraining',
                    'Verify image preprocessing pipeline'
                ]
            }
            return alert
        return None
    
    def export_monitoring_data(self, filename=None):
        """Export monitoring data for analysis"""
        if filename is None:
            filename = f"monitoring_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'monitoring_period': str(datetime.now() - self.start_time),
            'performance_metrics': self.get_performance_metrics(),
            'drift_analysis': self.detect_drift(),
            'prediction_history': [dict(p) for p in list(self.prediction_history)[-100:]],  # Last 100 predictions
            'feature_statistics': {k: list(v)[-50:] for k, v in self.feature_statistics.items()},  # Last 50 values per feature
            'rejection_reasons': dict(self.rejection_reasons)
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return filename
        except Exception as e:
            print(f"Error exporting monitoring data: {e}")
            return None

# Global monitor instance
model_monitor = ModelMonitor()

def log_prediction_event(features, validation_result, prediction_confidence=None):
    """Log prediction event to monitoring system"""
    return model_monitor.log_prediction(features, validation_result, prediction_confidence)

def check_system_drift():
    """Check for system drift"""
    return model_monitor.detect_drift()

def get_system_performance():
    """Get current system performance metrics"""
    return model_monitor.get_performance_metrics()

def generate_drift_alert():
    """Generate alert if drift is detected"""
    drift_result = model_monitor.detect_drift()
    return model_monitor.generate_alert(drift_result)

def export_monitoring_report():
    """Export monitoring report"""
    return model_monitor.export_monitoring_data()
