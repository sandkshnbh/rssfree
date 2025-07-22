// Global variables
let currentFeedData = null;

// DOM Elements
const rssForm = document.getElementById('rss-form');
const socialUrlInput = document.getElementById('social-url');
const loadingModal = document.getElementById('loading-modal');
const resultsSection = document.getElementById('results');
const feedsContainer = document.getElementById('feeds-container');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadExistingFeeds();
    setupEventListeners();
});

// Initialize application
function initializeApp() {
    // Add smooth scrolling for navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    // Add scroll effect to header
    window.addEventListener('scroll', function() {
        const header = document.querySelector('.header');
        if (window.scrollY > 100) {
            header.style.background = 'rgba(255, 255, 255, 0.98)';
            header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.background = 'rgba(255, 255, 255, 0.95)';
            header.style.boxShadow = 'none';
        }
    });

    // Add animation to feature cards
    observeElements('.feature-card', 'fade-in');
    observeElements('.step', 'slide-up');
}

// Setup event listeners
function setupEventListeners() {
    // RSS form submission
    rssForm.addEventListener('submit', handleFormSubmission);
    
    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
}

// Handle form submission
async function handleFormSubmission(e) {
    e.preventDefault();
    
    const url = socialUrlInput.value.trim();
    if (!url) {
        showNotification('يرجى إدخال رابط صحيح', 'error');
        return;
    }
    
    if (!isValidUrl(url)) {
        showNotification('يرجى إدخال رابط صحيح', 'error');
        return;
    }
    
    try {
        showLoadingModal();
        const feedData = await createRSSFeed(url);
        hideLoadingModal();
        
        if (feedData.error) {
            showNotification(feedData.error, 'error');
        } else {
            currentFeedData = feedData;
            showResults(feedData);
            loadExistingFeeds(); // Refresh feeds list
            showNotification('تم إنشاء خلاصة RSS بنجاح!', 'success');
        }
    } catch (error) {
        hideLoadingModal();
        showNotification('حدث خطأ أثناء إنشاء الخلاصة. يرجى المحاولة مرة أخرى.', 'error');
        console.error('Error creating RSS feed:', error);
    }
}

// Create RSS feed via API
async function createRSSFeed(url) {
    const response = await fetch('/api/create-feed', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: url,
            max_posts: 10
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// Load existing feeds
async function loadExistingFeeds() {
    try {
        const response = await fetch('/api/feeds');
        if (response.ok) {
            const feeds = await response.json();
            displayFeeds(feeds);
        }
    } catch (error) {
        console.error('Error loading feeds:', error);
    }
}

// Display feeds in the grid
function displayFeeds(feeds) {
    if (!feeds || feeds.length === 0) {
        feedsContainer.innerHTML = `
            <div class="no-feeds">
                <i class="fas fa-rss fa-3x" style="color: var(--text-light); margin-bottom: 1rem;"></i>
                <p>لا توجد خلاصات مُنشأة بعد</p>
                <p style="font-size: 0.9rem; color: var(--text-light);">ابدأ بإنشاء أول خلاصة RSS لك</p>
            </div>
        `;
        return;
    }
    
    feedsContainer.innerHTML = feeds.map(feed => `
        <div class="feed-item" data-feed-id="${feed.id}">
            <h4>${feed.title}</h4>
            <p>${feed.description}</p>
            <div class="feed-meta">
                <span><i class="fas fa-globe"></i> ${feed.platform}</span>
                <span><i class="fas fa-file-alt"></i> ${feed.post_count} منشور</span>
            </div>
            <div class="feed-meta">
                <span><i class="fas fa-clock"></i> ${formatDate(feed.last_updated)}</span>
                <span class="feed-status ${feed.status}">${getStatusText(feed.status)}</span>
            </div>
            <div class="feed-actions">
                <button class="btn-copy" onclick="copyFeedUrl('${feed.rss_url}')">
                    <i class="fas fa-copy"></i> نسخ
                </button>
                <button class="btn-secondary" onclick="previewFeedById('${feed.id}')">
                    <i class="fas fa-eye"></i> معاينة
                </button>
                <button class="btn-secondary" onclick="downloadFeedById('${feed.id}')">
                    <i class="fas fa-download"></i> تحميل
                </button>
                <button class="btn-secondary error" onclick="deleteFeed('${feed.id}')">
                    <i class="fas fa-trash"></i> حذف
                </button>
            </div>
        </div>
    `).join('');
}

// Show results section
function showResults(feedData) {
    document.getElementById('feed-title').textContent = feedData.title;
    document.getElementById('feed-description').textContent = feedData.description;
    document.getElementById('post-count').textContent = feedData.post_count;
    document.getElementById('last-updated').textContent = formatDate(feedData.last_updated);
    document.getElementById('rss-url').value = window.location.origin + feedData.rss_url;
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    resultsSection.classList.add('fade-in');
}

// Copy RSS URL to clipboard
function copyRSSUrl() {
    const rssUrlInput = document.getElementById('rss-url');
    rssUrlInput.select();
    document.execCommand('copy');
    showNotification('تم نسخ رابط RSS بنجاح!', 'success');
}

// Copy feed URL to clipboard
function copyFeedUrl(feedUrl) {
    const fullUrl = window.location.origin + feedUrl;
    navigator.clipboard.writeText(fullUrl).then(() => {
        showNotification('تم نسخ رابط RSS بنجاح!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = fullUrl;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('تم نسخ رابط RSS بنجاح!', 'success');
    });
}

// Download RSS file
function downloadRSS() {
    if (currentFeedData && currentFeedData.rss_url) {
        const link = document.createElement('a');
        link.href = currentFeedData.rss_url;
        link.download = `feed_${currentFeedData.id}.xml`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showNotification('بدأ تحميل ملف RSS', 'success');
    }
}

// Download feed by ID
function downloadFeedById(feedId) {
    const link = document.createElement('a');
    link.href = `/feeds/${feedId}.xml`;
    link.download = `feed_${feedId}.xml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showNotification('بدأ تحميل ملف RSS', 'success');
}

// Preview feed
function previewFeed() {
    if (currentFeedData && currentFeedData.rss_url) {
        window.open(currentFeedData.rss_url, '_blank');
    }
}

// Preview feed by ID
function previewFeedById(feedId) {
    window.open(`/feeds/${feedId}.xml`, '_blank');
}

// Delete feed
async function deleteFeed(feedId) {
    if (!confirm('هل أنت متأكد من حذف هذه الخلاصة؟')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/feeds/${feedId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('تم حذف الخلاصة بنجاح', 'success');
            loadExistingFeeds(); // Refresh feeds list
        } else {
            showNotification('فشل في حذف الخلاصة', 'error');
        }
    } catch (error) {
        showNotification('حدث خطأ أثناء حذف الخلاصة', 'error');
        console.error('Error deleting feed:', error);
    }
}

// Create another feed
function createAnother() {
    resultsSection.style.display = 'none';
    socialUrlInput.value = '';
    socialUrlInput.focus();
    document.getElementById('home').scrollIntoView({ behavior: 'smooth' });
}

// Show loading modal
function showLoadingModal() {
    loadingModal.classList.add('show');
}

// Hide loading modal
function hideLoadingModal() {
    loadingModal.classList.remove('show');
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 3000;
        animation: slideInRight 0.3s ease-out;
        max-width: 400px;
        direction: rtl;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Get notification icon
function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

// Get notification color
function getNotificationColor(type) {
    switch (type) {
        case 'success': return '#10b981';
        case 'error': return '#ef4444';
        case 'warning': return '#f59e0b';
        default: return '#3b82f6';
    }
}

// Validate URL
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'اليوم';
    } else if (diffDays === 2) {
        return 'أمس';
    } else if (diffDays <= 7) {
        return `منذ ${diffDays} أيام`;
    } else {
        return date.toLocaleDateString('ar-SA');
    }
}

// Get status text
function getStatusText(status) {
    switch (status) {
        case 'active': return 'نشط';
        case 'inactive': return 'غير نشط';
        case 'error': return 'خطأ';
        default: return status;
    }
}

// Observe elements for animations
function observeElements(selector, animationClass) {
    const elements = document.querySelectorAll(selector);
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add(animationClass);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0.25rem;
        margin-right: auto;
        opacity: 0.8;
        transition: opacity 0.2s;
    }
    
    .notification-close:hover {
        opacity: 1;
    }
    
    .no-feeds {
        grid-column: 1 / -1;
        text-align: center;
        padding: 3rem;
        color: var(--text-secondary);
    }
    
    .feed-status {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .feed-status.active {
        background: #dcfce7;
        color: #166534;
    }
    
    .feed-status.inactive {
        background: #fef3c7;
        color: #92400e;
    }
    
    .feed-status.error {
        background: #fecaca;
        color: #991b1b;
    }
    
    @media (max-width: 768px) {
        .nav-menu.active {
            display: flex;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            flex-direction: column;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-top: 1px solid var(--border-color);
        }
        
        .notification {
            right: 10px !important;
            left: 10px !important;
            max-width: none !important;
        }
    }
`;
document.head.appendChild(style);

