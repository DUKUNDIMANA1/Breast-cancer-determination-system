/**
 * Audit Trail System
 * Tracks all image review actions for compliance and quality control
 */

let auditEvents = [];
let currentUser = null;

// Audit event types
const AUDIT_EVENTS = {
    IMAGE_UPLOAD: 'image_upload',
    FEATURE_EXTRACTION: 'feature_extraction',
    ANNOTATION_ADDED: 'annotation_added',
    ANNOTATION_REMOVED: 'annotation_removed',
    FEATURE_VALIDATION: 'feature_validation',
    REVIEW_STARTED: 'review_started',
    REVIEW_COMPLETED: 'review_completed',
    APPROVAL_SUBMITTED: 'approval_submitted',
    REJECTION_SUBMITTED: 'rejection_submitted',
    CHANGES_REQUESTED: 'changes_requested',
    AI_ASSISTANCE: 'ai_assistance',
    COMPARISON_USED: 'comparison_used',
    QUALITY_ASSESSMENT: 'quality_assessment',
    REPORT_GENERATED: 'report_generated',
    COMMENT_ADDED: 'comment_added',
    COMMENT_EDITED: 'comment_edited',
    COMMENT_DELETED: 'comment_deleted',
    USER_LOGIN: 'user_login',
    USER_LOGOUT: 'user_logout'
};

function initializeAuditTrail() {
    currentUser = getCurrentUser();
    loadAuditEvents();
    
    // Log user session start
    logAuditEvent(AUDIT_EVENTS.USER_LOGIN, {
        timestamp: new Date().toISOString(),
        sessionId: generateSessionId()
    });
    
    // Setup page unload tracking
    window.addEventListener('beforeunload', () => {
        logAuditEvent(AUDIT_EVENTS.USER_LOGOUT, {
            timestamp: new Date().toISOString(),
            sessionId: generateSessionId()
        });
    });
}

function logAuditEvent(eventType, eventData = {}) {
    const auditEvent = {
        id: generateEventId(),
        type: eventType,
        userId: currentUser,
        timestamp: new Date().toISOString(),
        sessionId: getSessionId(),
        userAgent: navigator.userAgent,
        page: window.location.pathname,
        ...eventData
    };
    
    auditEvents.push(auditEvent);
    
    // Keep only last 1000 events
    if (auditEvents.length > 1000) {
        auditEvents = auditEvents.slice(-1000);
    }
    
    saveAuditEvents();
    
    // In production, this would send to server
    sendAuditToServer(auditEvent);
}

function logImageUpload(imageData) {
    logAuditEvent(AUDIT_EVENTS.IMAGE_UPLOAD, {
        imageName: imageData.name,
        imageSize: imageData.size,
        imageType: imageData.type,
        uploadDuration: imageData.uploadDuration,
        success: imageData.success
    });
}

function logFeatureExtraction(features, source) {
    logAuditEvent(AUDIT_EVENTS.FEATURE_EXTRACTION, {
        featureCount: Object.keys(features).length,
        source: source, // 'manual', 'ai_extracted', 'api'
        features: Object.keys(features),
        extractionDuration: features.extractionDuration
    });
}

function logAnnotationAdded(annotation) {
    logAuditEvent(AUDIT_EVENTS.ANNOTATION_ADDED, {
        annotationType: annotation.type,
        coordinates: annotation.data,
        annotationId: annotation.id,
        timestamp: annotation.timestamp
    });
}

function logAnnotationRemoved(annotationId) {
    logAuditEvent(AUDIT_EVENTS.ANNOTATION_REMOVED, {
        annotationId: annotationId,
        removedAt: new Date().toISOString()
    });
}

function logFeatureValidation(features, validationResults) {
    logAuditEvent(AUDIT_EVENTS.FEATURE_VALIDATION, {
        featureCount: Object.keys(features).length,
        validFeatures: validationResults.valid,
        invalidFeatures: validationResults.invalid,
        warnings: validationResults.warnings
    });
}

function logReviewStarted(requestId) {
    logAuditEvent(AUDIT_EVENTS.REVIEW_STARTED, {
        requestId: requestId,
        reviewType: 'doctor_review'
    });
}

function logReviewCompleted(requestId, action, comments) {
    logAuditEvent(AUDIT_EVENTS.REVIEW_COMPLETED, {
        requestId: requestId,
        action: action, // 'approve', 'reject', 'request_changes'
        comments: comments,
        reviewDuration: calculateReviewDuration()
    });
}

function logApprovalSubmitted(requestId, features) {
    logAuditEvent(AUDIT_EVENTS.APPROVAL_SUBMITTED, {
        requestId: requestId,
        approvedFeatures: Object.keys(features),
        featureCount: Object.keys(features).length
    });
}

function logRejectionSubmitted(requestId, reason) {
    logAuditEvent(AUDIT_EVENTS.REJECTION_SUBMITTED, {
        requestId: requestId,
        rejectionReason: reason
    });
}

function logChangesRequested(requestId, requestedChanges) {
    logAuditEvent(AUDIT_EVENTS.CHANGES_REQUESTED, {
        requestId: requestId,
        requestedChanges: requestedChanges
    });
}

function logAIAssistance(featureName, suggestion) {
    logAuditEvent(AUDIT_EVENTS.AI_ASSISTANCE, {
        featureName: featureName,
        aiSuggestion: suggestion,
        confidence: suggestion.confidence
    });
}

function logComparisonUsed(mode, features) {
    logAuditEvent(AUDIT_EVENTS.COMPARISON_USED, {
        comparisonMode: mode,
        featuresCompared: Object.keys(features)
    });
}

function logQualityAssessment(qualityScore, metrics) {
    logAuditEvent(AUDIT_EVENTS.QUALITY_ASSESSMENT, {
        qualityScore: qualityScore,
        metrics: Object.keys(metrics),
        grade: getQualityGrade(qualityScore)
    });
}

function logReportGenerated(reportType, reportData) {
    logAuditEvent(AUDIT_EVENTS.REPORT_GENERATED, {
        reportType: reportType, // 'pdf', 'json', 'text'
        reportSize: JSON.stringify(reportData).length,
        includesAnnotations: reportData.annotations ? reportData.annotations.length > 0 : false
    });
}

function logCommentAdded(commentId, commentData) {
    logAuditEvent(AUDIT_EVENTS.COMMENT_ADDED, {
        commentId: commentId,
        commentLength: commentData.content.length,
        isReply: commentData.isReply || false,
        parentId: commentData.parentId || null
    });
}

function logCommentEdited(commentId, originalContent, newContent) {
    logAuditEvent(AUDIT_EVENTS.COMMENT_EDITED, {
        commentId: commentId,
        originalLength: originalContent.length,
        newLength: newContent.length,
        changesDetected: originalContent !== newContent
    });
}

function logCommentDeleted(commentId, commentContent) {
    logAuditEvent(AUDIT_EVENTS.COMMENT_DELETED, {
        commentId: commentId,
        commentLength: commentContent ? commentContent.length : 0
    });
}

// Utility functions
function generateEventId() {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateSessionId() {
    return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function getSessionId() {
    return sessionStorage.getItem('sessionId') || generateSessionId();
}

function getCurrentUser() {
    return sessionStorage.getItem('currentUser') || 'anonymous';
}

function calculateReviewDuration() {
    // This would track review start time
    const startTime = sessionStorage.getItem('reviewStartTime');
    if (startTime) {
        return Date.now() - parseInt(startTime);
    }
    return 0;
}

function getQualityGrade(score) {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Good';
    if (score >= 70) return 'Fair';
    if (score >= 60) return 'Poor';
    return 'Very Poor';
}

function saveAuditEvents() {
    try {
        localStorage.setItem('auditTrail', JSON.stringify(auditEvents));
    } catch (error) {
        console.error('Failed to save audit events:', error);
    }
}

function loadAuditEvents() {
    try {
        const saved = localStorage.getItem('auditTrail');
        if (saved) {
            auditEvents = JSON.parse(saved);
        }
    } catch (error) {
        console.error('Failed to load audit events:', error);
        auditEvents = [];
    }
}

function sendAuditToServer(auditEvent) {
    // In production, this would send to server via API
    // For now, just log to console
    console.log('Audit Event:', auditEvent);
    
    // Simulate server response
    setTimeout(() => {
        console.log('Audit event logged successfully');
    }, 100);
}

function getAuditEvents() {
    return auditEvents;
}

function getAuditEventsByType(eventType) {
    return auditEvents.filter(event => event.type === eventType);
}

function getAuditEventsByUser(userId) {
    return auditEvents.filter(event => event.userId === userId);
}

function getAuditEventsByDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    return auditEvents.filter(event => {
        const eventDate = new Date(event.timestamp);
        return eventDate >= start && eventDate <= end;
    });
}

function exportAuditTrail() {
    const auditData = {
        exportedAt: new Date().toISOString(),
        exportedBy: currentUser,
        eventCount: auditEvents.length,
        events: auditEvents
    };
    
    downloadJSON(auditData, `audit-trail-${Date.now()}.json`);
}

function clearAuditTrail() {
    if (confirm('Are you sure you want to clear the audit trail? This cannot be undone.')) {
        auditEvents = [];
        saveAuditEvents();
        
        // Log the clear action
        logAuditEvent('AUDIT_TRAIL_CLEARED', {
            clearedBy: currentUser,
            clearedAt: new Date().toISOString()
        });
    }
}

function generateAuditReport() {
    const report = {
        summary: generateAuditSummary(),
        events: auditEvents,
        statistics: generateAuditStatistics()
    };
    
    downloadJSON(report, `audit-report-${Date.now()}.json`);
}

function generateAuditSummary() {
    const summary = {
        totalEvents: auditEvents.length,
        eventTypes: {},
        userActivity: {},
        timeRange: {
            first: auditEvents.length > 0 ? auditEvents[0].timestamp : null,
            last: auditEvents.length > 0 ? auditEvents[auditEvents.length - 1].timestamp : null
        }
    };
    
    // Count event types
    auditEvents.forEach(event => {
        summary.eventTypes[event.type] = (summary.eventTypes[event.type] || 0) + 1;
    });
    
    // Count user activity
    auditEvents.forEach(event => {
        summary.userActivity[event.userId] = (summary.userActivity[event.userId] || 0) + 1;
    });
    
    return summary;
}

function generateAuditStatistics() {
    const stats = {
        dailyActivity: {},
        hourlyActivity: {},
        eventTypeDistribution: {},
        userEngagement: {}
    };
    
    auditEvents.forEach(event => {
        const date = new Date(event.timestamp);
        const day = date.toDateString();
        const hour = date.getHours();
        
        // Daily activity
        stats.dailyActivity[day] = (stats.dailyActivity[day] || 0) + 1;
        
        // Hourly activity
        stats.hourlyActivity[hour] = (stats.hourlyActivity[hour] || 0) + 1;
        
        // Event type distribution
        stats.eventTypeDistribution[event.type] = (stats.eventTypeDistribution[event.type] || 0) + 1;
        
        // User engagement
        stats.userEngagement[event.userId] = (stats.userEngagement[event.userId] || 0) + 1;
    });
    
    return stats;
}

// Initialize audit trail on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeAuditTrail();
    
    // Add audit controls to page
    setTimeout(() => {
        addAuditControls();
    }, 2000);
});

function addAuditControls() {
    const controls = document.createElement('div');
    controls.className = 'audit-controls';
    controls.innerHTML = `
        <div class="audit-header">
            <h4><i class="fa-solid fa-history"></i> Audit Trail</h4>
            <div class="audit-actions">
                <button type="button" class="btn btn-sm btn-info" onclick="generateAuditReport()">
                    <i class="fa-solid fa-download"></i> Export Report
                </button>
                <button type="button" class="btn btn-sm btn-warning" onclick="clearAuditTrail()">
                    <i class="fa-solid fa-trash"></i> Clear Trail
                </button>
            </div>
        </div>
        <div class="audit-summary">
            <div class="summary-item">
                <span class="summary-label">Total Events:</span>
                <span class="summary-value">${auditEvents.length}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Session:</span>
                <span class="summary-value">${getSessionId().substr(0, 8)}...</span>
            </div>
        </div>
    `;
    
    // Add to page
    const container = document.querySelector('.page-header');
    if (container) {
        container.appendChild(controls);
    }
}
