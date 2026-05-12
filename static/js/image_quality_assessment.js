/**
 * Image Quality Assessment System
 * Evaluates image quality and provides scoring
 */

let qualityMetrics = null;
let qualityScore = 0;
let assessmentHistory = [];

// Quality assessment criteria
const qualityCriteria = {
    resolution: { min: 800, max: 4000, weight: 0.2 },
    contrast: { min: 0.1, max: 1.0, weight: 0.15 },
    sharpness: { min: 0.1, max: 1.0, weight: 0.15 },
    noise: { min: 0, max: 0.3, weight: 0.1 },
    brightness: { min: 0.3, max: 0.7, weight: 0.1 },
    saturation: { min: 0.2, max: 0.8, weight: 0.1 },
    focus: { min: 0.5, max: 1.0, weight: 0.2 }
};

function initializeQualityAssessment() {
    const img = document.getElementById('prev-img');
    if (!img) return;
    
    // Wait for image to load
    if (img.complete) {
        performQualityAssessment(img);
    } else {
        img.addEventListener('load', () => performQualityAssessment(img));
    }
}

function performQualityAssessment(img) {
    // Create canvas for image analysis
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    
    try {
        ctx.drawImage(img, 0, 0);
        
        // Get image data
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Calculate quality metrics
        qualityMetrics = {
            resolution: calculateResolution(img),
            contrast: calculateContrast(data),
            sharpness: calculateSharpness(data),
            noise: calculateNoise(data),
            brightness: calculateBrightness(data),
            saturation: calculateSaturation(data),
            focus: calculateFocus(data),
            timestamp: new Date().toISOString()
        };
        
        // Calculate overall score
        qualityScore = calculateOverallScore(qualityMetrics);
        
        // Display results
        displayQualityResults();
        
        // Save assessment history
        saveAssessmentHistory();
        
    } catch (error) {
        console.error('Quality assessment failed:', error);
        flash('Image quality assessment failed', 'danger');
    }
}

function calculateResolution(img) {
    const width = img.naturalWidth;
    const height = img.naturalHeight;
    const megapixels = (width * height) / 1000000;
    
    // Score based on resolution requirements
    let score = 0;
    if (width >= qualityCriteria.resolution.min && height >= qualityCriteria.resolution.min) {
        score = 1.0;
    } else {
        score = (width * height) / (qualityCriteria.resolution.max * qualityCriteria.resolution.max);
    }
    
    return {
        width,
        height,
        megapixels,
        score: Math.min(score, 1.0)
    };
}

function calculateContrast(imageData) {
    const data = imageData.data;
    let sum = 0;
    let sumSq = 0;
    const pixelCount = data.length / 4;
    
    // Calculate RMS contrast
    for (let i = 0; i < data.length; i += 4) {
        const gray = (data[i] + data[i+1] + data[i+2]) / 3;
        sum += gray;
        sumSq += gray * gray;
    }
    
    const mean = sum / pixelCount;
    const rms = Math.sqrt(sumSq / pixelCount);
    const contrast = rms / mean;
    
    // Normalize to 0-1 range
    const normalizedContrast = Math.min(contrast / 0.5, 1.0);
    
    return {
        value: contrast,
        normalized: normalizedContrast,
        score: Math.max(0, Math.min(1.0, (normalizedContrast - qualityCriteria.contrast.min) / (qualityCriteria.contrast.max - qualityCriteria.contrast.min)))
    };
}

function calculateSharpness(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Simplified sharpness calculation using edge detection
    let edges = 0;
    let totalPixels = 0;
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = (y * width + x) * 4;
            
            // Calculate gradient magnitude
            const gx = Math.abs(data[idx] - data[idx + 4]);
            const gy = Math.abs(data[idx] - data[idx + width * 4]);
            const gradient = Math.sqrt(gx * gx + gy * gy);
            
            if (gradient > 30) edges++;
            totalPixels++;
        }
    }
    
    const edgeRatio = edges / totalPixels;
    const sharpness = Math.min(edgeRatio * 10, 1.0);
    
    return {
        edgeCount: edges,
        edgeRatio,
        score: Math.max(0, Math.min(1.0, (sharpness - qualityCriteria.sharpness.min) / (qualityCriteria.sharpness.max - qualityCriteria.sharpness.min)))
    };
}

function calculateNoise(imageData) {
    const data = imageData.data;
    let noise = 0;
    const sampleSize = 1000;
    
    // Sample pixels and calculate local variance
    for (let i = 0; i < sampleSize; i++) {
        const idx = Math.floor(Math.random() * (data.length / 4)) * 4;
        const pixel = [data[idx], data[idx+1], data[idx+2]];
        
        // Calculate local variance as noise indicator
        const mean = pixel.reduce((a, b) => a + b, 0) / 3;
        const variance = pixel.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / 3;
        noise += Math.sqrt(variance);
    }
    
    const avgNoise = noise / sampleSize;
    const normalizedNoise = Math.min(avgNoise / 50, 1.0);
    
    return {
        averageNoise: avgNoise,
        normalized: normalizedNoise,
        score: Math.max(0, Math.min(1.0, 1.0 - (normalizedNoise - qualityCriteria.noise.min) / (qualityCriteria.noise.max - qualityCriteria.noise.min)))
    };
}

function calculateBrightness(imageData) {
    const data = imageData.data;
    let totalBrightness = 0;
    const pixelCount = data.length / 4;
    
    for (let i = 0; i < data.length; i += 4) {
        // Calculate perceived brightness
        const r = data[i];
        const g = data[i+1];
        const b = data[i+2];
        const brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        totalBrightness += brightness;
    }
    
    const avgBrightness = totalBrightness / pixelCount;
    const normalizedBrightness = Math.max(0, Math.min(1.0, avgBrightness));
    
    return {
        average: avgBrightness,
        normalized: normalizedBrightness,
        score: Math.max(0, Math.min(1.0, 1.0 - Math.abs(normalizedBrightness - 0.5) / 0.2))
    };
}

function calculateSaturation(imageData) {
    const data = imageData.data;
    let totalSaturation = 0;
    const pixelCount = data.length / 4;
    
    for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i+1];
        const b = data[i+2];
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const saturation = max === 0 ? 0 : (max - min) / max;
        totalSaturation += saturation;
    }
    
    const avgSaturation = totalSaturation / pixelCount;
    const normalizedSaturation = Math.min(avgSaturation, 1.0);
    
    return {
        average: avgSaturation,
        normalized: normalizedSaturation,
        score: Math.max(0, Math.min(1.0, (normalizedSaturation - qualityCriteria.saturation.min) / (qualityCriteria.saturation.max - qualityCriteria.saturation.min)))
    };
}

function calculateFocus(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Simplified focus calculation using frequency analysis
    let highFreq = 0;
    let lowFreq = 0;
    
    for (let y = 0; y < height; y += 2) {
        for (let x = 0; x < width; x += 2) {
            const idx = (y * width + x) * 4;
            const brightness = (data[idx] + data[idx+1] + data[idx+2]) / 3;
            
            // Simple high-pass filter approximation
            if (x > 0 && y > 0) {
                const prevIdx = ((y-1) * width + (x-1)) * 4;
                const prevBrightness = (data[prevIdx] + data[prevIdx+1] + data[prevIdx+2]) / 3;
                const diff = Math.abs(brightness - prevBrightness);
                
                if (diff > 20) highFreq++;
                else lowFreq++;
            }
        }
    }
    
    const focusRatio = highFreq / (highFreq + lowFreq);
    const normalizedFocus = Math.min(focusRatio * 2, 1.0);
    
    return {
        highFreq,
        lowFreq,
        focusRatio,
        score: Math.max(0, Math.min(1.0, (normalizedFocus - qualityCriteria.focus.min) / (qualityCriteria.focus.max - qualityCriteria.focus.min)))
    };
}

function calculateOverallScore(metrics) {
    let totalScore = 0;
    
    Object.entries(qualityCriteria).forEach(([criterion, config]) => {
        const metric = metrics[criterion];
        if (metric && metric.score !== undefined) {
            totalScore += metric.score * config.weight;
        }
    });
    
    return Math.round(totalScore * 100);
}

function displayQualityResults() {
    const resultsContainer = document.getElementById('quality-results');
    if (!resultsContainer) {
        createQualityResultsContainer();
        return;
    }
    
    const grade = getQualityGrade(qualityScore);
    const gradeColor = getGradeColor(grade);
    
    resultsContainer.innerHTML = `
        <div class="quality-assessment">
            <div class="quality-header">
                <h4>Image Quality Assessment</h4>
                <div class="quality-score" style="color: ${gradeColor}">
                    <div class="score-value">${qualityScore}/100</div>
                    <div class="score-grade">${grade}</div>
                </div>
            </div>
            <div class="quality-metrics">
                ${Object.entries(qualityMetrics).map(([metric, data]) => `
                    <div class="metric-item">
                        <div class="metric-name">${formatMetricName(metric)}</div>
                        <div class="metric-value">
                            <div class="metric-score">${Math.round(data.score * 100)}%</div>
                            <div class="metric-details">${formatMetricDetails(metric, data)}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="quality-recommendations">
                <h5>Recommendations</h5>
                <ul>
                    ${generateRecommendations(grade)}
                </ul>
            </div>
        </div>
    `;
    
    // Add to image viewer
    const imageViewer = document.querySelector('.image-viewer');
    if (imageViewer) {
        imageViewer.appendChild(resultsContainer);
    }
}

function createQualityResultsContainer() {
    const imageViewer = document.querySelector('.image-viewer');
    if (!imageViewer) return;
    
    const container = document.createElement('div');
    container.id = 'quality-results';
    container.className = 'quality-assessment-container';
    imageViewer.appendChild(container);
}

function formatMetricName(metric) {
    return metric.charAt(0).toUpperCase() + metric.slice(1).replace(/([A-Z])/g, ' $1');
}

function formatMetricDetails(metric, data) {
    switch(metric) {
        case 'resolution':
            return `${data.width}×${data.height} (${data.megapixels.toFixed(2)}MP)`;
        case 'contrast':
            return `Contrast: ${data.value.toFixed(2)}`;
        case 'sharpness':
            return `Edge ratio: ${data.edgeRatio.toFixed(3)}`;
        case 'noise':
            return `Noise level: ${data.averageNoise.toFixed(2)}`;
        case 'brightness':
            return `Brightness: ${(data.normalized * 100).toFixed(1)}%`;
        case 'saturation':
            return `Saturation: ${(data.normalized * 100).toFixed(1)}%`;
        case 'focus':
            return `Focus quality: ${(data.normalized * 100).toFixed(1)}%`;
        default:
            return '';
    }
}

function getQualityGrade(score) {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Good';
    if (score >= 70) return 'Fair';
    if (score >= 60) return 'Poor';
    return 'Very Poor';
}

function getGradeColor(grade) {
    const colors = {
        'Excellent': '#28a745',
        'Good': '#17a2b8',
        'Fair': '#ffc107',
        'Poor': '#fd7e14',
        'Very Poor': '#dc3545'
    };
    return colors[grade] || '#6c757d';
}

function generateRecommendations(grade) {
    const recommendations = {
        'Excellent': [
            'Image quality is excellent for analysis',
            'All quality metrics are within optimal ranges',
            'Proceed with confidence in the analysis results'
        ],
        'Good': [
            'Image quality is good for most analyses',
            'Consider minor adjustments if possible',
            'Results should be reliable'
        ],
        'Fair': [
            'Image quality may affect analysis accuracy',
            'Consider re-scanning if possible',
            'Be cautious with borderline features'
        ],
        'Poor': [
            'Image quality may significantly impact results',
            'Strongly recommend re-acquiring image',
            'Consider manual feature entry as backup'
        ],
        'Very Poor': [
            'Image quality is insufficient for reliable analysis',
            'Do not rely on automated feature extraction',
            'Manual feature entry recommended'
        ]
    };
    
    return (recommendations[grade] || []).map(rec => `<li>${rec}</li>`).join('');
}

function saveAssessmentHistory() {
    const assessment = {
        timestamp: qualityMetrics.timestamp,
        score: qualityScore,
        metrics: qualityMetrics,
        grade: getQualityGrade(qualityScore)
    };
    
    assessmentHistory.push(assessment);
    
    // Keep only last 10 assessments
    if (assessmentHistory.length > 10) {
        assessmentHistory = assessmentHistory.slice(-10);
    }
    
    localStorage.setItem('qualityAssessmentHistory', JSON.stringify(assessmentHistory));
}

function loadAssessmentHistory() {
    const saved = localStorage.getItem('qualityAssessmentHistory');
    if (saved) {
        assessmentHistory = JSON.parse(saved);
    }
}

function getAssessmentHistory() {
    return assessmentHistory;
}

function exportQualityReport() {
    const report = {
        currentAssessment: {
            timestamp: qualityMetrics.timestamp,
            score: qualityScore,
            metrics: qualityMetrics,
            grade: getQualityGrade(qualityScore)
        },
        history: assessmentHistory,
        criteria: qualityCriteria
    };
    
    downloadJSON(report, `quality-assessment-${Date.now()}.json`);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAssessmentHistory();
    
    // Add quality assessment button to controls
    setTimeout(() => {
        const controls = document.querySelector('.image-controls');
        if (controls) {
            const qualityBtn = document.createElement('button');
            qualityBtn.className = 'btn btn-sm btn-info';
            qualityBtn.innerHTML = '<i class="fa-solid fa-chart-line"></i> Quality';
            qualityBtn.onclick = initializeQualityAssessment;
            controls.appendChild(qualityBtn);
        }
    }, 1000);
});
