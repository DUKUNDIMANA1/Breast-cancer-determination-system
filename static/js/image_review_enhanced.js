/**
 * Enhanced Image Review System
 * Provides zoom, pan, annotation, and validation features
 */

let zoomLevel = 1;
let isDragging = false;
let startX, startY;
let scrollLeft, scrollTop;
let currentAnnotation = null;
let annotations = [];
let isFullscreen = false;

// Feature validation ranges
const featureRanges = {
    'radius_mean': { min: 5, max: 30, unit: 'mm' },
    'texture_mean': { min: 0.05, max: 0.3, unit: '' },
    'perimeter_mean': { min: 50, max: 200, unit: 'mm' },
    'area_mean': { min: 200, max: 2500, unit: 'mm²' },
    'smoothness_mean': { min: 0, max: 0.2, unit: '' },
    'compactness_mean': { min: 0, max: 0.1, unit: '' },
    'concavity_mean': { min: 0, max: 0.4, unit: '' },
    'concave points_mean': { min: 0, max: 0.2, unit: '' },
    'symmetry_mean': { min: 0.1, max: 0.3, unit: '' },
    'fractal_dimension_mean': { min: 0.05, max: 0.1, unit: '' },
    'radius_se': { min: 0.1, max: 2, unit: 'mm' },
    'texture_se': { min: 0.01, max: 0.08, unit: '' },
    'perimeter_se': { min: 5, max: 25, unit: 'mm' },
    'area_se': { min: 20, max: 500, unit: 'mm²' },
    'smoothness_se': { min: 0.001, max: 0.03, unit: '' },
    'compactness_se': { min: 0.001, max: 0.03, unit: '' },
    'concavity_se': { min: 0.001, max: 0.05, unit: '' },
    'concave points_se': { min: 0.001, max: 0.03, unit: '' },
    'symmetry_se': { min: 0.002, max: 0.04, unit: '' },
    'fractal_dimension_se': { min: 0.002, max: 0.02, unit: '' },
    'radius_worst': { min: 7, max: 40, unit: 'mm' },
    'texture_worst': { min: 0.1, max: 0.5, unit: '' },
    'perimeter_worst': { min: 60, max: 250, unit: 'mm' },
    'area_worst': { min: 300, max: 3000, unit: 'mm²' },
    'smoothness_worst': { min: 0, max: 0.3, unit: '' },
    'compactness_worst': { min: 0, max: 0.2, unit: '' },
    'concavity_worst': { min: 0, max: 0.6, unit: '' },
    'concave points_worst': { min: 0, max: 0.3, unit: '' },
    'symmetry_worst': { min: 0.15, max: 0.5, unit: '' },
    'fractal_dimension_worst': { min: 0.06, max: 0.15, unit: '' }
};

// Initialize image viewer
function initializeImageViewer() {
    const img = document.getElementById('prev-img');
    if (!img) return;

    // Add drag functionality
    img.addEventListener('mousedown', startDrag);
    img.addEventListener('mouseleave', endDrag);
    img.addEventListener('mouseup', endDrag);
    img.addEventListener('mousemove', drag);
    
    // Add wheel zoom
    img.addEventListener('wheel', handleWheel);
    
    // Initialize validation
    validateAllFeatures();
}

// Zoom functions
function zoomIn() {
    zoomLevel = Math.min(zoomLevel * 1.2, 5);
    applyZoom();
}

function zoomOut() {
    zoomLevel = Math.max(zoomLevel / 1.2, 0.5);
    applyZoom();
}

function resetZoom() {
    zoomLevel = 1;
    applyZoom();
    centerImage();
}

function applyZoom() {
    const img = document.getElementById('prev-img');
    img.style.transform = `scale(${zoomLevel})`;
}

function centerImage() {
    const img = document.getElementById('prev-img');
    const container = img.parentElement;
    container.scrollTop = (img.offsetHeight * zoomLevel - container.offsetHeight) / 2;
    container.scrollLeft = (img.offsetWidth * zoomLevel - container.offsetWidth) / 2;
}

// Pan functionality
function startDrag(e) {
    isDragging = true;
    const img = document.getElementById('prev-img');
    const container = img.parentElement;
    
    startX = e.pageX - container.offsetLeft;
    startY = e.pageY - container.offsetTop;
    scrollLeft = container.scrollLeft;
    scrollTop = container.scrollTop;
    
    img.style.cursor = 'grabbing';
}

function drag(e) {
    if (!isDragging) return;
    e.preventDefault();
    
    const img = document.getElementById('prev-img');
    const container = img.parentElement;
    const x = e.pageX - container.offsetLeft;
    const y = e.pageY - container.offsetTop;
    const walkX = (x - startX) * 1.5;
    const walkY = (y - startY) * 1.5;
    
    container.scrollLeft = scrollLeft - walkX;
    container.scrollTop = scrollTop - walkY;
}

function endDrag() {
    isDragging = false;
    const img = document.getElementById('prev-img');
    img.style.cursor = 'grab';
}

function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -1 : 1;
    if (delta < 0) {
        zoomIn();
    } else {
        zoomOut();
    }
}

// Fullscreen functionality
function toggleFullscreen() {
    const img = document.getElementById('prev-img');
    const container = img.parentElement;
    
    if (!isFullscreen) {
        if (container.requestFullscreen) {
            container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) {
            container.msRequestFullscreen();
        }
        isFullscreen = true;
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        isFullscreen = false;
    }
}

// Annotation functions
function enableAnnotation(type) {
    currentAnnotation = type;
    const img = document.getElementById('prev-img');
    img.style.cursor = 'crosshair';
    
    // Remove existing annotation listeners
    img.removeEventListener('click', handlePointAnnotation);
    img.removeEventListener('click', handleCircleAnnotation);
    img.removeEventListener('click', handleArrowAnnotation);
    
    // Add appropriate annotation listener
    switch(type) {
        case 'point':
            img.addEventListener('click', handlePointAnnotation);
            break;
        case 'circle':
            img.addEventListener('click', handleCircleAnnotation);
            break;
        case 'arrow':
            img.addEventListener('click', handleArrowAnnotation);
            break;
    }
}

function handlePointAnnotation(e) {
    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    addAnnotation('point', { x, y });
}

function handleCircleAnnotation(e) {
    // Simplified circle annotation - just mark center
    handlePointAnnotation(e);
}

function handleArrowAnnotation(e) {
    // Simplified arrow annotation - just mark point
    handlePointAnnotation(e);
}

function addAnnotation(type, data) {
    const annotation = {
        id: Date.now(),
        type,
        data,
        timestamp: new Date().toISOString(),
        author: getCurrentUser()
    };
    
    annotations.push(annotation);
    renderAnnotation(annotation);
    saveAnnotations();
}

function renderAnnotation(annotation) {
    const img = document.getElementById('prev-img');
    const rect = img.getBoundingClientRect();
    
    const element = document.createElement('div');
    element.className = 'annotation-marker';
    element.style.position = 'absolute';
    element.style.left = `${annotation.data.x}px`;
    element.style.top = `${annotation.data.y}px`;
    element.style.zIndex = '1000';
    
    switch(annotation.type) {
        case 'point':
            element.innerHTML = `<i class="fa-solid fa-map-pin" style="color: var(--danger-color); font-size: 16px;"></i>`;
            break;
        case 'circle':
            element.innerHTML = `<i class="fa-solid fa-circle" style="color: var(--warning-color); font-size: 12px;"></i>`;
            break;
        case 'arrow':
            element.innerHTML = `<i class="fa-solid fa-arrow-right" style="color: var(--info-color); font-size: 14px;"></i>`;
            break;
    }
    
    img.parentElement.appendChild(element);
}

function clearAnnotations() {
    const img = document.getElementById('prev-img');
    const container = img.parentElement;
    
    // Remove all annotation elements
    const annotationElements = container.querySelectorAll('.annotation-marker');
    annotationElements.forEach(el => el.remove());
    
    // Clear annotations array
    annotations = [];
    saveAnnotations();
    
    // Reset cursor
    img.style.cursor = 'grab';
    currentAnnotation = null;
}

function saveAnnotations() {
    // Save annotations to localStorage or send to server
    localStorage.setItem('imageAnnotations', JSON.stringify(annotations));
}

function loadAnnotations() {
    const saved = localStorage.getItem('imageAnnotations');
    if (saved) {
        annotations = JSON.parse(saved);
        annotations.forEach(annotation => renderAnnotation(annotation));
    }
}

// Feature validation
function validateFeature(featureName, value) {
    const range = featureRanges[featureName];
    if (!range) return { valid: true, status: 'unknown' };
    
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return { valid: false, status: 'invalid' };
    
    let status = 'valid';
    let message = '';
    
    if (numValue < range.min) {
        status = 'low';
        message = `Below minimum (${range.min}${range.unit})`;
    } else if (numValue > range.max) {
        status = 'high';
        message = `Above maximum (${range.max}${range.unit})`;
    }
    
    return { valid: status === 'valid', status, message, value: numValue, range };
}

function validateAllFeatures() {
    const inputs = document.querySelectorAll('input[type="number"]');
    
    inputs.forEach(input => {
        const featureName = input.name;
        const value = input.value;
        
        if (featureName && value) {
            const validation = validateFeature(featureName, value);
            
            // Remove existing validation classes
            input.classList.remove('feature-valid', 'feature-invalid', 'feature-warning');
            
            // Add appropriate validation class
            if (!validation.valid) {
                input.classList.add('feature-invalid');
            } else if (validation.status !== 'valid') {
                input.classList.add('feature-warning');
            } else {
                input.classList.add('feature-valid');
            }
            
            // Add tooltip with validation info
            if (validation.message) {
                input.title = validation.message;
            } else {
                input.title = `Valid range: ${validation.range.min}-${validation.range.max}${validation.range.unit}`;
            }
        }
    });
}

// AI assistance for feature verification
function getAIAssistance(featureName) {
    // Simulate AI verification
    const input = document.querySelector(`input[name="${featureName}"]`);
    if (!input) return;
    
    const value = parseFloat(input.value);
    if (isNaN(value)) return;
    
    // Show AI suggestion
    const suggestion = analyzeFeatureWithAI(featureName, value);
    if (suggestion) {
        showAISuggestion(featureName, suggestion);
    }
}

function analyzeFeatureWithAI(featureName, value) {
    // Simulated AI analysis - in real implementation, this would call an AI service
    const range = featureRanges[featureName];
    if (!range) return null;
    
    const deviation = Math.abs(value - ((range.min + range.max) / 2)) / ((range.max - range.min) / 2);
    
    if (deviation > 0.8) {
        return {
            confidence: 'low',
            suggestion: 'This value seems unusual. Please verify the measurement.',
            action: 'review'
        };
    } else if (deviation > 0.5) {
        return {
            confidence: 'medium',
            suggestion: 'This value is outside typical range but may be valid for this case.',
            action: 'verify'
        };
    } else {
        return {
            confidence: 'high',
            suggestion: 'This value appears normal.',
            action: 'accept'
        };
    }
}

function showAISuggestion(featureName, suggestion) {
    // Create or update AI suggestion tooltip
    let tooltip = document.getElementById(`ai-suggestion-${featureName}`);
    
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = `ai-suggestion-${featureName}`;
        tooltip.className = 'ai-suggestion';
        tooltip.innerHTML = `
            <div class="ai-confidence-${suggestion.confidence}">
                <i class="fa-solid fa-robot"></i> AI: ${suggestion.suggestion}
            </div>
        `;
        
        const input = document.querySelector(`input[name="${featureName}"]`);
        input.parentNode.appendChild(tooltip);
    }
}

// Utility functions
function getCurrentUser() {
    // Get current user from session or localStorage
    return sessionStorage.getItem('currentUser') || 'Unknown User';
}

function exportAnnotatedImage() {
    // Create export with annotations overlay
    const img = document.getElementById('prev-img');
    
    // In real implementation, this would use canvas to overlay annotations
    const exportData = {
        imageUrl: img.src,
        annotations: annotations,
        timestamp: new Date().toISOString(),
        features: extractCurrentFeatures()
    };
    
    // Download as JSON or send to server
    downloadJSON(exportData, `image-review-${Date.now()}.json`);
}

function extractCurrentFeatures() {
    const features = {};
    const inputs = document.querySelectorAll('input[type="number"]');
    
    inputs.forEach(input => {
        if (input.name && input.value) {
            features[input.name] = parseFloat(input.value);
        }
    });
    
    return features;
}

function downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// Toggle collaborative review panel
function toggleCollaborativeReview() {
    const panel = document.getElementById('collaborative-panel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
}

// Generate PDF report
function generatePDFReport() {
    const reportData = {
        patientInfo: {
            name: document.querySelector('.info-value.fw-700')?.textContent || 'Unknown',
            id: document.querySelector('.info-value code')?.textContent || 'Unknown',
            testType: document.querySelector('.info-value')?.textContent || 'Unknown'
        },
        features: extractCurrentFeatures(),
        annotations: annotations,
        reviewComments: reviewComments,
        doctorReview: document.querySelector('textarea[name="doctor_review_comment"]')?.value || '',
        labNotes: document.querySelector('textarea[name="lab_notes"]')?.value || '',
        timestamp: new Date().toISOString(),
        generatedBy: getCurrentUser()
    };
    
    // In real implementation, this would use a PDF library like jsPDF
    // For now, create a formatted text report that can be saved as PDF
    createTextReport(reportData);
}

function createTextReport(data) {
    const reportContent = `
BREASTCARE AI DIAGNOSTIC REPORT
===============================================

PATIENT INFORMATION
-----------------
Name: ${data.patientInfo.name}
ID: ${data.patientInfo.id}
Test Type: ${data.patientInfo.testType}
Report Generated: ${new Date().toLocaleString()}
Generated By: ${data.generatedBy}

FEATUREURE ANALYSIS
-----------------
${formatFeaturesForReport(data.features)}

DOCTOR REVIEW
-------------
${data.doctorReview || 'No doctor review provided'}

LAB NOTES
----------
${data.labNotes || 'No lab notes provided'}

ANNOTATIONS
-----------
${data.annotations.length > 0 ? data.annotations.map(ann => `- ${ann.type} at (${ann.data.x}, ${ann.data.y}): ${ann.timestamp}`).join('\n') : 'No annotations'}

REVIEW COMMENTS
--------------
${data.reviewComments.length > 0 ? data.reviewComments.map(comment => `${comment.author} (${formatCommentTime(comment.timestamp)}): ${comment.content}`).join('\n\n') : 'No review comments'}

===============================================
End of Report
    `;
    
    // Create downloadable text file
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnostic-report-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    flash('Diagnostic report generated and downloaded', 'success');
}

function formatFeaturesForReport(features) {
    const sections = {
        'Mean Features': ['radius_mean', 'texture_mean', 'perimeter_mean', 'area_mean', 'smoothness_mean', 'compactness_mean', 'concavity_mean', 'concave points_mean', 'symmetry_mean', 'fractal_dimension_mean'],
        'Standard Error Features': ['radius_se', 'texture_se', 'perimeter_se', 'area_se', 'smoothness_se', 'compactness_se', 'concavity_se', 'concave points_se', 'symmetry_se', 'fractal_dimension_se'],
        'Worst Features': ['radius_worst', 'texture_worst', 'perimeter_worst', 'area_worst', 'smoothness_worst', 'compactness_worst', 'concavity_worst', 'concave points_worst', 'symmetry_worst', 'fractal_dimension_worst']
    };
    
    let report = '';
    
    Object.entries(sections).forEach(([sectionName, featureList]) => {
        report += `\n${sectionName}:\n`;
        featureList.forEach(feature => {
            const value = features[feature];
            const range = featureRanges[feature];
            const validation = validateFeature(feature, value);
            
            report += `  ${feature}: ${value ? value.toFixed(6) : 'N/A'}`;
            if (range) {
                report += ` (Range: ${range.min}-${range.max}${range.unit})`;
            }
            if (!validation.valid) {
                report += ` ⚠️ ${validation.message}`;
            }
            report += '\n';
        });
        report += '\n';
    });
    
    return report;
}

// Add quality assessment button to image controls
function addQualityAssessmentButton() {
    const controls = document.querySelector('.image-controls');
    if (!controls) return;
    
    const qualityBtn = document.createElement('button');
    qualityBtn.className = 'btn btn-sm btn-warning';
    qualityBtn.innerHTML = '<i class="fa-solid fa-chart-line"></i> Quality';
    qualityBtn.onclick = initializeQualityAssessment;
    controls.appendChild(qualityBtn);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeImageViewer();
    loadAnnotations();
    addQualityAssessmentButton();
    
    // Add validation listeners
    const inputs = document.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        input.addEventListener('input', validateAllFeatures);
        input.addEventListener('change', validateAllFeatures);
    });
});
