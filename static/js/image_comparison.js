/**
 * Image Comparison System
 * Side-by-side comparison of original and processed images
 */

let originalImage = null;
let processedImage = null;
let comparisonMode = 'split'; // 'split', 'overlay', 'slider'

function initializeComparison() {
    const img = document.getElementById('prev-img');
    if (!img) return;
    
    // Store original image for comparison
    originalImage = img.src;
    
    // Add comparison controls
    addComparisonControls();
    
    // Initialize split view by default
    setComparisonMode('split');
}

function addComparisonControls() {
    const container = document.querySelector('.image-viewer');
    if (!container) return;
    
    const controls = document.createElement('div');
    controls.className = 'comparison-controls';
    controls.innerHTML = `
        <div class="comparison-mode">
            <strong>Comparison Mode:</strong>
            <button type="button" class="btn btn-sm ${comparisonMode === 'split' ? 'btn-primary' : 'btn-outline'}" onclick="setComparisonMode('split')">
                <i class="fa-solid fa-columns"></i> Split View
            </button>
            <button type="button" class="btn btn-sm ${comparisonMode === 'overlay' ? 'btn-primary' : 'btn-outline'}" onclick="setComparisonMode('overlay')">
                <i class="fa-solid fa-layer-group"></i> Overlay
            </button>
            <button type="button" class="btn btn-sm ${comparisonMode === 'slider' ? 'btn-primary' : 'btn-outline'}" onclick="setComparisonMode('slider')">
                <i class="fa-solid fa-sliders-h"></i> Slider
            </button>
        </div>
        <div class="comparison-adjustments">
            <strong>Adjustments:</strong>
            <div class="adjustment-row">
                <label>Opacity:</label>
                <input type="range" id="overlay-opacity" min="0" max="100" value="50" oninput="updateOverlayOpacity()"/>
                <span id="opacity-value">50%</span>
            </div>
            <div class="adjustment-row">
                <label>Blend Mode:</label>
                <select id="blend-mode" onchange="updateBlendMode()" class="form-control form-control-sm">
                    <option value="normal">Normal</option>
                    <option value="multiply">Multiply</option>
                    <option value="screen">Screen</option>
                    <option value="overlay">Overlay</option>
                </select>
            </div>
            <div class="adjustment-row">
                <button type="button" class="btn btn-sm btn-info" onclick="syncFeatures()">
                    <i class="fa-solid fa-sync"></i> Sync Features
                </button>
                <button type="button" class="btn btn-sm btn-success" onclick="exportComparison()">
                    <i class="fa-solid fa-download"></i> Export Comparison
                </button>
            </div>
        </div>
    `;
    
    container.appendChild(controls);
}

function setComparisonMode(mode) {
    comparisonMode = mode;
    
    // Update button states
    document.querySelectorAll('.comparison-controls button').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline');
    });
    
    // Activate selected mode button
    const activeBtn = document.querySelector(`.comparison-controls button[onclick="setComparisonMode('${mode}')"]`);
    if (activeBtn) {
        activeBtn.classList.remove('btn-outline');
        activeBtn.classList.add('btn-primary');
    }
    
    // Apply comparison mode
    switch(mode) {
        case 'split':
            createSplitView();
            break;
        case 'overlay':
            createOverlayView();
            break;
        case 'slider':
            createSliderView();
            break;
    }
}

function createSplitView() {
    const container = document.querySelector('.image-viewer');
    if (!container || !originalImage) return;
    
    // Clear existing comparison views
    clearComparisonViews();
    
    // Create split container
    const splitContainer = document.createElement('div');
    splitContainer.className = 'split-view-container';
    splitContainer.innerHTML = `
        <div class="split-view left">
            <div class="comparison-label">Original Image</div>
            <img src="${originalImage}" class="comparison-img"/>
        </div>
        <div class="split-view right">
            <div class="comparison-label">Processed Image</div>
            <img src="${originalImage}" class="comparison-img"/>
            <div class="comparison-overlay">
                <!-- Feature differences will be highlighted here -->
            </div>
        </div>
    `;
    
    // Replace original image with split view
    const originalImg = document.getElementById('prev-img');
    if (originalImg) {
        originalImg.style.display = 'none';
        originalImg.parentNode.insertBefore(splitContainer, originalImg);
    }
    
    // Add feature difference highlighting
    highlightFeatureDifferences();
}

function createOverlayView() {
    const container = document.querySelector('.image-viewer');
    if (!container || !originalImage) return;
    
    // Clear existing comparison views
    clearComparisonViews();
    
    // Create overlay container
    const overlayContainer = document.createElement('div');
    overlayContainer.className = 'overlay-view-container';
    overlayContainer.innerHTML = `
        <div class="overlay-base">
            <img src="${originalImage}" class="comparison-img base-image"/>
        </div>
        <div class="overlay-top">
            <img src="${originalImage}" class="comparison-img overlay-image"/>
            <div class="overlay-differences">
                <!-- AI-detected differences highlighted -->
            </div>
        </div>
        <div class="overlay-controls">
            <button type="button" class="btn btn-xs" onclick="toggleOverlayLayer('base')">
                <i class="fa-solid fa-eye"></i> Base
            </button>
            <button type="button" class="btn btn-xs" onclick="toggleOverlayLayer('top')">
                <i class="fa-solid fa-layer-group"></i> Processed
            </button>
        </div>
    `;
    
    // Replace original image with overlay view
    const originalImg = document.getElementById('prev-img');
    if (originalImg) {
        originalImg.style.display = 'none';
        originalImg.parentNode.insertBefore(overlayContainer, originalImg);
    }
}

function createSliderView() {
    const container = document.querySelector('.image-viewer');
    if (!container || !originalImage) return;
    
    // Clear existing comparison views
    clearComparisonViews();
    
    // Create slider container
    const sliderContainer = document.createElement('div');
    sliderContainer.className = 'slider-view-container';
    sliderContainer.innerHTML = `
        <div class="slider-base">
            <img src="${originalImage}" class="comparison-img"/>
        </div>
        <div class="slider-handle">
            <input type="range" id="comparison-slider" min="0" max="100" value="50" oninput="updateSliderView()"/>
            <div class="slider-label">50%</div>
        </div>
        <div class="slider-overlay">
            <img src="${originalImage}" class="comparison-img"/>
            <div class="slider-differences">
                <!-- Real-time difference display -->
            </div>
        </div>
    `;
    
    // Replace original image with slider view
    const originalImg = document.getElementById('prev-img');
    if (originalImg) {
        originalImg.style.display = 'none';
        originalImg.parentNode.insertBefore(sliderContainer, originalImg);
    }
}

function clearComparisonViews() {
    // Remove any existing comparison views
    const existingViews = document.querySelectorAll('.split-view-container, .overlay-view-container, .slider-view-container');
    existingViews.forEach(view => view.remove());
    
    // Show original image
    const originalImg = document.getElementById('prev-img');
    if (originalImg) {
        originalImg.style.display = 'block';
    }
}

function updateOverlayOpacity() {
    const opacity = document.getElementById('overlay-opacity').value;
    const overlayImage = document.querySelector('.overlay-image');
    if (overlayImage) {
        overlayImage.style.opacity = opacity / 100;
    }
    
    // Update opacity value display
    document.getElementById('opacity-value').textContent = `${opacity}%`;
}

function updateBlendMode() {
    const blendMode = document.getElementById('blend-mode').value;
    const overlayImage = document.querySelector('.overlay-image');
    if (overlayImage) {
        overlayImage.style.mixBlendMode = blendMode;
    }
}

function updateSliderView() {
    const sliderValue = document.getElementById('comparison-slider').value;
    const sliderOverlay = document.querySelector('.slider-overlay');
    if (sliderOverlay) {
        sliderOverlay.style.clipPath = `inset(0 0 ${100 - sliderValue}% 0)`;
    }
    
    // Update slider label
    document.querySelector('.slider-label').textContent = `${sliderValue}%`;
}

function toggleOverlayLayer(layer) {
    const baseImage = document.querySelector('.base-image');
    const overlayImage = document.querySelector('.overlay-image');
    
    if (layer === 'base') {
        baseImage.style.opacity = '1';
        overlayImage.style.opacity = '0.3';
    } else {
        baseImage.style.opacity = '0.3';
        overlayImage.style.opacity = '1';
    }
}

function highlightFeatureDifferences() {
    // Compare features between original and processed
    const originalFeatures = getStoredFeatures('original');
    const processedFeatures = getStoredFeatures('processed');
    
    if (!originalFeatures || !processedFeatures) return;
    
    // Highlight significant differences
    const differences = analyzeFeatureDifferences(originalFeatures, processedFeatures);
    
    // Add difference indicators to comparison view
    const differenceContainer = document.querySelector('.comparison-overlay, .slider-differences');
    if (differenceContainer) {
        differenceContainer.innerHTML = differences.map(diff => `
            <div class="feature-difference ${diff.severity}">
                <div class="diff-feature">${diff.feature}</div>
                <div class="diff-value">${diff.original} → ${diff.processed}</div>
                <div class="diff-change">${diff.change}</div>
            </div>
        `).join('');
    }
}

function analyzeFeatureDifferences(original, processed) {
    const differences = [];
    
    // Compare key features
    const keyFeatures = ['radius_mean', 'texture_mean', 'area_mean', 'concavity_mean', 'symmetry_mean'];
    
    keyFeatures.forEach(feature => {
        const origVal = original[feature];
        const procVal = processed[feature];
        
        if (origVal && procVal) {
            const change = Math.abs(procVal - origVal);
            const percentChange = (change / origVal) * 100;
            
            let severity = 'minor';
            if (percentChange > 20) severity = 'major';
            else if (percentChange > 10) severity = 'moderate';
            
            differences.push({
                feature,
                original: origVal.toFixed(3),
                processed: procVal.toFixed(3),
                change: `${change > 0 ? '+' : ''}${change.toFixed(3)} (${percentChange.toFixed(1)}%)`,
                severity
            });
        }
    });
    
    return differences;
}

function syncFeatures() {
    // Sync features between original and processed views
    const originalFeatures = getStoredFeatures('original');
    const processedFeatures = getStoredFeatures('processed');
    
    if (originalFeatures && processedFeatures) {
        // Update processed features to match original
        Object.keys(originalFeatures).forEach(feature => {
            const input = document.querySelector(`input[name="${feature}"]`);
            if (input && originalFeatures[feature]) {
                input.value = originalFeatures[feature];
                input.dispatchEvent(new Event('input'));
            }
        });
        
        flash('Features synchronized with original values', 'success');
    }
}

function getStoredFeatures(type) {
    // Get features from current form or storage
    const features = {};
    const inputs = document.querySelectorAll('input[type="number"]');
    
    inputs.forEach(input => {
        if (input.name && input.value) {
            features[input.name] = parseFloat(input.value);
        }
    });
    
    return features;
}

function exportComparison() {
    const comparisonData = {
        timestamp: new Date().toISOString(),
        comparisonMode: comparisonMode,
        originalFeatures: getStoredFeatures('original'),
        processedFeatures: getStoredFeatures('processed'),
        differences: analyzeFeatureDifferences(
            getStoredFeatures('original'),
            getStoredFeatures('processed')
        ),
        annotations: annotations || []
    };
    
    // Download comparison data
    downloadJSON(comparisonData, `image-comparison-${Date.now()}.json`);
}

// Initialize comparison when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add comparison button to existing toolbar
    setTimeout(initializeComparison, 1000);
});
