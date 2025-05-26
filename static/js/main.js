/**
 * TikTok Social Listening - Main JavaScript File
 * Contains common functions and utilities used across the application
 */

// Global configuration
const APP_CONFIG = {
    API_BASE_URL: '/api',
    REFRESH_INTERVAL: 300000, // 5 minutes
    CHART_COLORS: {
        primary: '#667eea',
        secondary: '#764ba2',
        success: '#25d366',
        danger: '#ff0050',
        warning: '#ffa726',
        info: '#25f4ee'
    }
};

// Utility Functions
const Utils = {
    /**
     * Format number with commas
     */
    formatNumber: function(num) {
        if (num === null || num === undefined) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Format large numbers (K, M, B)
     */
    formatLargeNumber: function(num) {
        if (num === null || num === undefined) return '0';
        if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'B';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    },

    /**
     * Get relative time (e.g., "2 hours ago")
     */
    getRelativeTime: function(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} วันที่แล้ว`;
        if (hours > 0) return `${hours} ชั่วโมงที่แล้ว`;
        if (minutes > 0) return `${minutes} นาทีที่แล้ว`;
        return 'เมื่อสักครู่';
    },

    /**
     * Debounce function to limit API calls
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Copy text to clipboard
     */
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve();
        }
    }
};

// Alert System
const AlertSystem = {
    /**
     * Show alert message
     */
    show: function(type, message, duration = 5000) {
        const alertId = 'alert-' + Date.now();
        const alertDiv = document.createElement('div');
        alertDiv.id = alertId;
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '90px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(alertDiv);

        // Auto-dismiss
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                alert.remove();
            }
        }, duration);

        return alertId;
    },

    success: function(message, duration) {
        return this.show('success', message, duration);
    },

    error: function(message, duration) {
        return this.show('danger', message, duration);
    },

    warning: function(message, duration) {
        return this.show('warning', message, duration);
    },

    info: function(message, duration) {
        return this.show('info', message, duration);
    }
};

// API Client
const ApiClient = {
    /**
     * Make API request
     */
    request: async function(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const config = { ...defaultOptions, ...options };
        const url = APP_CONFIG.API_BASE_URL + endpoint;

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    // Dashboard APIs
    getDashboardStats: function() {
        return this.request('/dashboard-stats');
    },

    collectDataNow: function() {
        return this.request('/collect-now', { method: 'POST' });
    },

    // Keywords APIs
    toggleKeyword: function(keywordId) {
        return this.request(`/keywords/${keywordId}/toggle`, { method: 'POST' });
    },

    // Content APIs
    searchPosts: function(params) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/posts/search?${queryString}`);
    },

    generateContentIdeas: function(limit = 10) {
        return this.request('/content-ideas/generate', {
            method: 'POST',
            body: JSON.stringify({ limit })
        });
    },

    // Analytics APIs
    getKeywordAnalytics: function(keyword) {
        return this.request(`/keyword/${encodeURIComponent(keyword)}/analytics`);
    },

    getTrendingHashtags: function(days = 7, limit = 20) {
        return this.request(`/trending-hashtags?days=${days}&limit=${limit}`);
    }
};

// Loading Management
const LoadingManager = {
    modal: null,

    show: function(message = 'กำลังประมวลผล...') {
        if (!this.modal) {
            this.modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        }

        const modalBody = document.querySelector('#loadingModal .modal-body p');
        if (modalBody) {
            modalBody.textContent = message;
        }

        this.modal.show();
    },

    hide: function() {
        if (this.modal) {
            this.modal.hide();
        }
    }
};

// Chart Helper
const ChartHelper = {
    /**
     * Create line chart
     */
    createLineChart: function(ctx, data, options = {}) {
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            }
        };

        return new Chart(ctx, {
            type: 'line',
            data: data,
            options: { ...defaultOptions, ...options }
        });
    },

    /**
     * Create doughnut chart
     */
    createDoughnutChart: function(ctx, data, options = {}) {
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        };

        return new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: { ...defaultOptions, ...options }
        });
    }
};

// Form Validation
const FormValidator = {
    /**
     * Validate keyword form
     */
    validateKeyword: function(keyword) {
        const errors = [];

        if (!keyword || keyword.trim().length < 2) {
            errors.push('Keyword ต้องมีอย่างน้อย 2 ตัวอักษร');
        }

        if (keyword && keyword.length > 50) {
            errors.push('Keyword ต้องไม่เกิน 50 ตัวอักษร');
        }

        // Check for special characters that might cause issues
        if (keyword && /[<>\"'&]/.test(keyword)) {
            errors.push('Keyword ประกอบด้วยอักขระที่ไม่อนุญาต');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    },

    /**
     * Show validation errors
     */
    showErrors: function(errors, formElement) {
        // Clear previous errors
        const existingErrors = formElement.querySelectorAll('.invalid-feedback');
        existingErrors.forEach(error => error.remove());

        // Add new errors
        errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback d-block';
            errorDiv.textContent = error;
            formElement.appendChild(errorDiv);
        });
    }
};

// Auto-refresh System
const AutoRefresh = {
    intervals: new Map(),

    /**
     * Start auto-refresh for dashboard stats
     */
    startDashboardRefresh: function(callback, interval = APP_CONFIG.REFRESH_INTERVAL) {
        this.stop('dashboard');

        const intervalId = setInterval(async () => {
            try {
                const stats = await ApiClient.getDashboardStats();
                if (callback && typeof callback === 'function') {
                    callback(stats);
                }
            } catch (error) {
                console.error('Auto-refresh failed:', error);
            }
        }, interval);

        this.intervals.set('dashboard', intervalId);
    },

    /**
     * Stop auto-refresh
     */
    stop: function(name) {
        if (this.intervals.has(name)) {
            clearInterval(this.intervals.get(name));
            this.intervals.delete(name);
        }
    },

    /**
     * Stop all auto-refresh
     */
    stopAll: function() {
        this.intervals.forEach((intervalId, name) => {
            clearInterval(intervalId);
        });
        this.intervals.clear();
    }
};

// Theme Management
const ThemeManager = {
    /**
     * Get current theme
     */
    getCurrentTheme: function() {
        return localStorage.getItem('theme') ||
               (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    },

    /**
     * Set theme
     */
    setTheme: function(theme) {
        localStorage.setItem('theme', theme);
        document.documentElement.setAttribute('data-theme', theme);

        // Update chart colors if needed
        if (window.Chart) {
            Chart.defaults.color = theme === 'dark' ? '#ffffff' : '#333333';
        }
    },

    /**
     * Initialize theme
     */
    init: function() {
        const theme = this.getCurrentTheme();
        this.setTheme(theme);
    }
};

// Hashtag Helper
const HashtagHelper = {
    /**
     * Extract hashtags from text
     */
    extract: function(text) {
        const hashtagRegex = /#[\w\u0E00-\u0E7F]+/g;
        return text.match(hashtagRegex) || [];
    },

    /**
     * Make hashtags clickable
     */
    makeClickable: function(text, baseUrl = '/trending') {
        const hashtagRegex = /#([\w\u0E00-\u0E7F]+)/g;
        return text.replace(hashtagRegex, (match, hashtag) => {
            return `<a href="${baseUrl}?hashtag=${encodeURIComponent(hashtag)}" class="hashtag">${match}</a>`;
        });
    }
};

// Data Export Helper
const ExportHelper = {
    /**
     * Export data to CSV
     */
    toCSV: function(data, filename = 'export.csv') {
        const csv = this.arrayToCSV(data);
        this.downloadFile(csv, filename, 'text/csv');
    },

    /**
     * Convert array to CSV
     */
    arrayToCSV: function(data) {
        if (!data || data.length === 0) return '';

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row =>
                headers.map(header => {
                    const value = row[header];
                    // Escape commas and quotes
                    if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value;
                }).join(',')
            )
        ].join('\n');

        return csvContent;
    },

    /**
     * Download file
     */
    downloadFile: function(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }
};

// Search Helper
const SearchHelper = {
    /**
     * Debounced search function
     */
    debouncedSearch: Utils.debounce(function(query, callback) {
        if (query.length < 2) {
            callback([]);
            return;
        }

        ApiClient.searchPosts({
            keyword: query,
            limit: 10
        }).then(response => {
            callback(response.data || []);
        }).catch(error => {
            console.error('Search failed:', error);
            callback([]);
        });
    }, 300),

    /**
     * Initialize search functionality
     */
    initSearchBox: function(inputElement, resultsElement, onSelect) {
        inputElement.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            this.debouncedSearch(query, (results) => {
                this.renderSearchResults(results, resultsElement, onSelect);
            });
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!inputElement.contains(e.target) && !resultsElement.contains(e.target)) {
                resultsElement.style.display = 'none';
            }
        });
    },

    /**
     * Render search results
     */
    renderSearchResults: function(results, container, onSelect) {
        container.innerHTML = '';

        if (results.length === 0) {
            container.style.display = 'none';
            return;
        }

        results.forEach(item => {
            const div = document.createElement('div');
            div.className = 'search-result-item p-2 border-bottom cursor-pointer';
            div.innerHTML = `
                <div class="fw-semibold">${item.username}</div>
                <div class="text-muted small">${item.description.substring(0, 100)}...</div>
            `;

            div.addEventListener('click', () => {
                onSelect(item);
                container.style.display = 'none';
            });

            container.appendChild(div);
        });

        container.style.display = 'block';
    }
};

// Performance Monitor
const PerformanceMonitor = {
    metrics: {},

    /**
     * Start timing
     */
    start: function(name) {
        this.metrics[name] = { start: performance.now() };
    },

    /**
     * End timing
     */
    end: function(name) {
        if (this.metrics[name]) {
            this.metrics[name].duration = performance.now() - this.metrics[name].start;
            return this.metrics[name].duration;
        }
        return null;
    },

    /**
     * Log performance metrics
     */
    log: function() {
        console.table(this.metrics);
    }
};

// Notification System
const NotificationSystem = {
    permission: null,

    /**
     * Request notification permission
     */
    requestPermission: async function() {
        if ('Notification' in window) {
            this.permission = await Notification.requestPermission();
            return this.permission === 'granted';
        }
        return false;
    },

    /**
     * Show notification
     */
    show: function(title, options = {}) {
        if (this.permission === 'granted') {
            const notification = new Notification(title, {
                icon: '/static/images/logo.png',
                badge: '/static/images/badge.png',
                ...options
            });

            // Auto-close after 5 seconds
            setTimeout(() => notification.close(), 5000);

            return notification;
        }
        return null;
    },

    /**
     * Show data collection complete notification
     */
    showDataCollectionComplete: function(postsCount) {
        this.show('Data Collection Complete', {
            body: `เก็บข้อมูลใหม่ได้ ${postsCount} posts`,
            icon: '/static/images/success-icon.png'
        });
    }
};

// App Initialization
const App = {
    /**
     * Initialize application
     */
    init: function() {
        console.log('🚀 TikTok Social Listening App Starting...');

        // Initialize theme
        ThemeManager.init();

        // Request notification permission
        NotificationSystem.requestPermission();

        // Initialize global event listeners
        this.initGlobalEventListeners();

        // Initialize tooltips
        this.initTooltips();

        // Start performance monitoring
        PerformanceMonitor.start('app-init');

        console.log('✅ App initialized successfully');
        PerformanceMonitor.end('app-init');
    },

    /**
     * Initialize global event listeners
     */
    initGlobalEventListeners: function() {
        // Handle all ajax forms
        document.addEventListener('submit', this.handleFormSubmit);

        // Handle escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.show');
                modals.forEach(modal => {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) modalInstance.hide();
                });
            }
        });

        // Handle page visibility change for auto-refresh
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                AutoRefresh.stopAll();
            } else {
                // Restart auto-refresh when page becomes visible
                if (window.location.pathname === '/') {
                    this.startDashboardAutoRefresh();
                }
            }
        });
    },

    /**
     * Handle form submission
     */
    handleFormSubmit: function(e) {
        const form = e.target;

        // Skip if form has data-no-ajax attribute
        if (form.hasAttribute('data-no-ajax')) return;

        // Validate forms with validation class
        if (form.classList.contains('needs-validation')) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                form.classList.add('was-validated');
                return;
            }
        }

        // Show loading state for submit buttons
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
            submitBtn.disabled = true;

            // Reset after 10 seconds as fallback
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 10000);
        }
    },

    /**
     * Initialize tooltips
     */
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    /**
     * Start dashboard auto-refresh
     */
    startDashboardAutoRefresh: function() {
        AutoRefresh.startDashboardRefresh((stats) => {
            if (stats.success) {
                this.updateDashboardStats(stats.data);
            }
        });
    },

    /**
     * Update dashboard statistics
     */
    updateDashboardStats: function(data) {
        // Update stats cards
        const elements = {
            totalPosts: document.querySelector('.stats-card .stats-number'),
            totalKeywords: document.querySelectorAll('.stats-card .stats-number')[1],
            totalEngagement: document.querySelectorAll('.stats-card .stats-number')[2],
            trendingPosts: document.querySelectorAll('.stats-card .stats-number')[3]
        };

        if (elements.totalPosts) elements.totalPosts.textContent = Utils.formatNumber(data.total_posts);
        if (elements.totalKeywords) elements.totalKeywords.textContent = data.total_keywords;
        if (elements.totalEngagement) elements.totalEngagement.textContent = Utils.formatLargeNumber(data.total_engagement);
        if (elements.trendingPosts) elements.trendingPosts.textContent = data.trending_posts;
    }
};

// Page-specific modules
const PageModules = {
    /**
     * Keywords page functionality
     */
    keywords: {
        init: function() {
            console.log('🔑 Initializing Keywords page');

            // Initialize form validation
            const form = document.getElementById('addKeywordForm');
            if (form) {
                form.addEventListener('submit', this.handleAddKeyword);
            }

            // Initialize search functionality
            const searchInput = document.getElementById('keywordSearch');
            const searchResults = document.getElementById('searchResults');
            if (searchInput && searchResults) {
                SearchHelper.initSearchBox(searchInput, searchResults, this.selectKeyword);
            }
        },

        handleAddKeyword: function(e) {
            const keyword = document.getElementById('keyword').value.trim();
            const validation = FormValidator.validateKeyword(keyword);

            if (!validation.isValid) {
                e.preventDefault();
                FormValidator.showErrors(validation.errors, e.target);
                return false;
            }
        },

        selectKeyword: function(keyword) {
            window.location.href = `/keywords/${keyword.id}/analytics`;
        }
    },

    /**
     * Dashboard page functionality
     */
    dashboard: {
        init: function() {
            console.log('📊 Initializing Dashboard page');

            // Start auto-refresh
            App.startDashboardAutoRefresh();

            // Initialize charts if Chart.js is available
            if (typeof Chart !== 'undefined') {
                this.initCharts();
            }
        },

        initCharts: function() {
            // Engagement chart
            const engagementCtx = document.getElementById('engagementChart');
            if (engagementCtx && window.engagementData) {
                ChartHelper.createLineChart(engagementCtx, {
                    labels: window.engagementData.labels,
                    datasets: [{
                        label: 'Total Engagement',
                        data: window.engagementData.data,
                        borderColor: APP_CONFIG.CHART_COLORS.primary,
                        backgroundColor: APP_CONFIG.CHART_COLORS.primary + '20',
                        tension: 0.4,
                        fill: true
                    }]
                });
            }

            // Keywords chart
            const keywordsCtx = document.getElementById('keywordsChart');
            if (keywordsCtx && window.keywordData) {
                ChartHelper.createDoughnutChart(keywordsCtx, {
                    labels: window.keywordData.labels,
                    datasets: [{
                        data: window.keywordData.data,
                        backgroundColor: [
                            APP_CONFIG.CHART_COLORS.danger,
                            APP_CONFIG.CHART_COLORS.info,
                            APP_CONFIG.CHART_COLORS.primary,
                            APP_CONFIG.CHART_COLORS.warning,
                            APP_CONFIG.CHART_COLORS.success
                        ]
                    }]
                });
            }
        }
    }
};

// Global functions (for backward compatibility)
window.showAlert = AlertSystem.show;
window.copyToClipboard = Utils.copyToClipboard;
window.formatNumber = Utils.formatNumber;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize main app
    App.init();

    // Initialize page-specific modules based on current page
    const currentPage = document.body.getAttribute('data-page');
    if (currentPage && PageModules[currentPage]) {
        PageModules[currentPage].init();
    }
});

// Cleanup when page is unloaded
window.addEventListener('beforeunload', function() {
    AutoRefresh.stopAll();
});

// Export for use in other scripts
window.TikTokApp = {
    Utils,
    AlertSystem,
    ApiClient,
    LoadingManager,
    ChartHelper,
    FormValidator,
    AutoRefresh,
    ThemeManager,
    HashtagHelper,
    ExportHelper,
    SearchHelper,
    PerformanceMonitor,
    NotificationSystem,
    App,
    PageModules
};