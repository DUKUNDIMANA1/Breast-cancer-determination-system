/**
 * Collaborative Review System
 * Enables multiple doctors to review and discuss cases
 */

let activeReviewers = [];
let reviewComments = [];
let currentUser = null;

// Initialize collaborative review
function initializeCollaborativeReview() {
    currentUser = getCurrentUser();
    loadActiveReviewers();
    loadReviewComments();
    setupRealtimeCollaboration();
}

// Reviewer management
function addReviewer(userId) {
    if (!activeReviewers.includes(userId)) {
        activeReviewers.push(userId);
        
        // Notify added reviewer
        notifyReviewer(userId, 'added');
        
        // Update UI
        updateReviewerUI();
        saveReviewers();
    }
}

function removeReviewer(userId) {
    const index = activeReviewers.indexOf(userId);
    if (index > -1) {
        activeReviewers.splice(index, 1);
        
        // Notify removed reviewer
        notifyReviewer(userId, 'removed');
        
        // Update UI
        updateReviewerUI();
        saveReviewers();
    }
}

function updateReviewerUI() {
    const reviewerList = document.getElementById('active-reviewers');
    if (!reviewerList) return;
    
    reviewerList.innerHTML = activeReviewers.map(reviewerId => {
        const reviewer = getUserInfo(reviewerId);
        return `
            <div class="reviewer-item" data-user-id="${reviewerId}">
                <div class="reviewer-avatar">
                    <img src="${reviewer.avatar || '/static/images/default-avatar.png'}" alt="${reviewer.name}"/>
                </div>
                <div class="reviewer-info">
                    <div class="reviewer-name">${reviewer.name}</div>
                    <div class="reviewer-role">${reviewer.role}</div>
                    <div class="reviewer-status ${reviewer.online ? 'online' : 'offline'}">
                        ${reviewer.online ? '🟢 Online' : '⚫ Offline'}
                    </div>
                </div>
                <div class="reviewer-actions">
                    <button type="button" class="btn btn-xs btn-outline" onclick="messageReviewer('${reviewerId}')">
                        <i class="fa-solid fa-message"></i>
                    </button>
                    <button type="button" class="btn btn-xs btn-outline" onclick="callReviewer('${reviewerId}')">
                        <i class="fa-solid fa-phone"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Review comments system
function addReviewComment(comment) {
    const reviewComment = {
        id: Date.now(),
        author: currentUser,
        content: comment,
        timestamp: new Date().toISOString(),
        type: 'comment',
        replies: []
    };
    
    reviewComments.push(reviewComment);
    saveReviewComments();
    updateCommentsUI();
    
    // Notify other reviewers
    notifyNewComment(reviewComment);
}

function addReply(commentId, reply) {
    const parentComment = reviewComments.find(c => c.id === commentId);
    if (parentComment) {
        const replyData = {
            id: Date.now(),
            author: currentUser,
            content: reply,
            timestamp: new Date().toISOString(),
            type: 'reply',
            parentId: commentId
        };
        
        parentComment.replies.push(replyData);
        saveReviewComments();
        updateCommentsUI();
        
        // Notify parent comment author
        notifyReply(parentComment, replyData);
    }
}

function updateCommentsUI() {
    const commentsContainer = document.getElementById('review-comments');
    if (!commentsContainer) return;
    
    commentsContainer.innerHTML = reviewComments.map(comment => renderComment(comment)).join('');
}

function renderComment(comment) {
    const author = getUserInfo(comment.author);
    const isOwnComment = comment.author === currentUser;
    
    return `
        <div class="review-comment ${isOwnComment ? 'own-comment' : ''}" data-comment-id="${comment.id}">
            <div class="comment-header">
                <div class="comment-author">
                    <img src="${author.avatar || '/static/images/default-avatar.png'}" alt="${author.name}" class="author-avatar"/>
                    <div class="author-info">
                        <div class="author-name">${author.name}</div>
                        <div class="author-role">${author.role}</div>
                        <div class="comment-time">${formatCommentTime(comment.timestamp)}</div>
                    </div>
                </div>
                <div class="comment-actions">
                    ${isOwnComment ? `
                        <button type="button" class="btn btn-xs btn-outline" onclick="editComment('${comment.id}')">
                            <i class="fa-solid fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-xs btn-danger" onclick="deleteComment('${comment.id}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    ` : `
                        <button type="button" class="btn btn-xs btn-outline" onclick="replyToComment('${comment.id}')">
                            <i class="fa-solid fa-reply"></i> Reply
                        </button>
                    `}
                </div>
            </div>
            <div class="comment-content">
                ${comment.content}
            </div>
            ${comment.replies.length > 0 ? renderReplies(comment.replies) : ''}
        </div>
    `;
}

function renderReplies(replies) {
    return replies.map(reply => `
        <div class="comment-reply" data-comment-id="${reply.id}">
            <div class="reply-header">
                <div class="reply-author">${getUserInfo(reply.author).name}</div>
                <div class="reply-time">${formatCommentTime(reply.timestamp)}</div>
            </div>
            <div class="reply-content">${reply.content}</div>
        </div>
    `).join('');
}

// Real-time collaboration
function setupRealtimeCollaboration() {
    // In real implementation, this would use WebSockets or Server-Sent Events
    // For now, simulate with periodic updates
    
    setInterval(() => {
        checkForNewComments();
        checkReviewerStatus();
    }, 5000); // Check every 5 seconds
}

function checkForNewComments() {
    // Simulate checking for new comments
    // In real implementation, this would fetch from server
}

function checkReviewerStatus() {
    // Update online/offline status of reviewers
    activeReviewers.forEach(reviewerId => {
        const reviewer = document.querySelector(`[data-user-id="${reviewerId}"]`);
        if (reviewer) {
            const statusElement = reviewer.querySelector('.reviewer-status');
            const isOnline = Math.random() > 0.7; // Simulate online status
            
            if (statusElement) {
                statusElement.className = `reviewer-status ${isOnline ? 'online' : 'offline'}`;
                statusElement.textContent = isOnline ? '🟢 Online' : '⚫ Offline';
            }
        }
    });
}

// Notification system
function notifyNewComment(comment) {
    // Notify all active reviewers except the author
    activeReviewers.forEach(reviewerId => {
        if (reviewerId !== comment.author) {
            sendNotification(reviewerId, {
                type: 'new_comment',
                data: comment
            });
        }
    });
}

function notifyReply(parentComment, reply) {
    // Notify the parent comment author
    sendNotification(parentComment.author, {
        type: 'reply',
        data: {
            parentComment,
            reply
        }
    });
}

function notifyReviewer(reviewerId, action) {
    sendNotification(reviewerId, {
        type: 'reviewer_update',
        data: { action }
    });
}

function sendNotification(userId, notification) {
    // In real implementation, this would send via WebSocket or push notification
    console.log(`Notification sent to ${userId}:`, notification);
    
    // Show browser notification if page is visible
    if (Notification.permission === 'granted' && !document.hidden) {
        new Notification(`BreastCare AI - ${notification.type}`, {
            body: getNotificationMessage(notification),
            icon: '/static/images/logo.png'
        });
    }
}

function getNotificationMessage(notification) {
    switch(notification.type) {
        case 'new_comment':
            return `New comment from ${getUserInfo(notification.data.author).name}`;
        case 'reply':
            return `${getUserInfo(notification.data.reply.author).name} replied to your comment`;
        case 'reviewer_update':
            return `You were ${notification.data.action} from the review`;
        default:
            return 'New notification';
    }
}

// Utility functions
function getCurrentUser() {
    return sessionStorage.getItem('currentUser') || 'Unknown User';
}

function getUserInfo(userId) {
    // In real implementation, this would fetch from server
    const users = {
        'doctor1': { name: 'Dr. Smith', role: 'Radiologist', avatar: '/static/images/doctor1.jpg' },
        'doctor2': { name: 'Dr. Johnson', role: 'Pathologist', avatar: '/static/images/doctor2.jpg' },
        'lab_tech': { name: 'Lab Tech', role: 'Lab Technician', avatar: '/static/images/lab-tech.jpg' }
    };
    
    return users[userId] || { name: 'Unknown User', role: 'Unknown', avatar: '/static/images/default-avatar.png' };
}

function formatCommentTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // Less than 1 minute
        return 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
        return `${Math.floor(diff / 60000)} minutes ago`;
    } else if (diff < 86400000) { // Less than 1 day
        return `${Math.floor(diff / 3600000)} hours ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Data persistence
function saveReviewers() {
    localStorage.setItem('activeReviewers', JSON.stringify(activeReviewers));
}

function loadActiveReviewers() {
    const saved = localStorage.getItem('activeReviewers');
    if (saved) {
        activeReviewers = JSON.parse(saved);
    }
}

function saveReviewComments() {
    localStorage.setItem('reviewComments', JSON.stringify(reviewComments));
}

function loadReviewComments() {
    const saved = localStorage.getItem('reviewComments');
    if (saved) {
        reviewComments = JSON.parse(saved);
    }
}

// Comment editing
function editComment(commentId) {
    const comment = reviewComments.find(c => c.id === commentId);
    if (comment && comment.author === currentUser) {
        const content = prompt('Edit your comment:', comment.content);
        if (content !== null && content !== comment.content) {
            comment.content = content;
            comment.edited = true;
            comment.editedAt = new Date().toISOString();
            saveReviewComments();
            updateCommentsUI();
        }
    }
}

function deleteComment(commentId) {
    const index = reviewComments.findIndex(c => c.id === commentId);
    if (index > -1) {
        const comment = reviewComments[index];
        if (comment.author === currentUser) {
            if (confirm('Are you sure you want to delete this comment?')) {
                reviewComments.splice(index, 1);
                saveReviewComments();
                updateCommentsUI();
            }
        }
    }
}

function replyToComment(commentId) {
    const reply = prompt('Reply to comment:');
    if (reply !== null && reply.trim()) {
        addReply(commentId, reply.trim());
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCollaborativeReview();
    
    // Request notification permission
    if ('Notification' in window) {
        Notification.requestPermission();
    }
});
