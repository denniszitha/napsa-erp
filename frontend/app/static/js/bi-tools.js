/**
 * BI Tools Enhanced JavaScript Functionality
 */

// Global variables
let charts = {};
let updateInterval;
let isAutoRefresh = true;

// Initialize BI Tools Dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    startAutoRefresh();
});

/**
 * Initialize Dashboard Components
 */
function initializeDashboard() {
    // Initialize all charts
    initializeCharts();
    
    // Load initial data
    loadDashboardData();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup notification system
    setupNotifications();
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn')?.addEventListener('click', () => {
        refreshDashboard(true);
    });
    
    // Time range selector
    document.getElementById('timeRange')?.addEventListener('change', (e) => {
        loadDashboardData(e.target.value);
    });
    
    // Department filter
    document.getElementById('departmentFilter')?.addEventListener('change', (e) => {
        loadDashboardData(null, e.target.value);
    });
    
    // Export button
    document.getElementById('exportBtn')?.addEventListener('click', exportDashboard);
    
    // Auto-refresh toggle
    document.getElementById('autoRefreshToggle')?.addEventListener('change', (e) => {
        isAutoRefresh = e.target.checked;
        if (isAutoRefresh) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
}

/**
 * Initialize Charts
 */
function initializeCharts() {
    // Risk Trend Chart
    const trendCtx = document.getElementById('trendChart')?.getContext('2d');
    if (trendCtx) {
        charts.trend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Risk Trend',
                    data: [],
                    borderColor: '#6cbace',
                    backgroundColor: 'rgba(108, 186, 206, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#6cbace',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return `Risks: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
    
    // Category Distribution Chart
    const categoryCtx = document.getElementById('categoryChart')?.getContext('2d');
    if (categoryCtx) {
        charts.category = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#ef4444',
                        '#f97316',
                        '#eab308',
                        '#84cc16',
                        '#10b981',
                        '#06b6d4',
                        '#3b82f6',
                        '#8b5cf6'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true
                }
            }
        });
    }
}

/**
 * Load Dashboard Data
 */
async function loadDashboardData(timeRange = null, departmentId = null) {
    try {
        showLoading();
        
        const params = new URLSearchParams();
        params.append('time_range', timeRange || document.getElementById('timeRange')?.value || '30d');
        if (departmentId || document.getElementById('departmentFilter')?.value) {
            params.append('department_id', departmentId || document.getElementById('departmentFilter').value);
        }
        
        const response = await fetch(`/bi-tools/api/dashboard-data?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateDashboard(data);
            showNotification('Dashboard updated successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to load dashboard data');
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
        // Use mock data as fallback
        useMockData();
    } finally {
        hideLoading();
    }
}

/**
 * Update Dashboard with New Data
 */
function updateDashboard(data) {
    // Update metrics
    updateMetrics(data.summary);
    
    // Update charts
    if (data.risk_trends && charts.trend) {
        updateTrendChart(data.risk_trends);
    }
    
    if (data.category_distribution && charts.category) {
        updateCategoryChart(data.category_distribution);
    }
    
    // Update heatmap
    if (data.heatmap_data) {
        updateHeatmap(data.heatmap_data);
    }
    
    // Add animation to updated elements
    animateUpdates();
}

/**
 * Update Metric Cards
 */
function updateMetrics(summary) {
    const metrics = {
        'totalRisks': summary.total_risks || 0,
        'highRisks': summary.high_risks || 0,
        'completedAssessments': summary.completed_assessments || 0,
        'controlEffectiveness': (summary.control_effectiveness_ratio || 0).toFixed(1) + '%',
        'complianceScore': (summary.compliance_score || 0).toFixed(1) + '%',
        'riskVelocity': (summary.risk_velocity || 0).toFixed(1)
    };
    
    Object.keys(metrics).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            animateValue(element, element.textContent, metrics[key]);
        }
    });
}

/**
 * Animate Numeric Value Changes
 */
function animateValue(element, start, end) {
    const startNum = parseFloat(start) || 0;
    const endNum = parseFloat(end) || 0;
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const currentValue = startNum + (endNum - startNum) * easeOutQuart(progress);
        
        if (end.toString().includes('%')) {
            element.textContent = currentValue.toFixed(1) + '%';
        } else if (end.toString().includes('.')) {
            element.textContent = currentValue.toFixed(1);
        } else {
            element.textContent = Math.round(currentValue);
        }
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.classList.add('updating');
            setTimeout(() => element.classList.remove('updating'), 500);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Easing Function
 */
function easeOutQuart(t) {
    return 1 - Math.pow(1 - t, 4);
}

/**
 * Update Trend Chart
 */
function updateTrendChart(trendData) {
    if (!charts.trend) return;
    
    charts.trend.data.labels = trendData.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    charts.trend.data.datasets[0].data = trendData.map(item => item.count);
    charts.trend.update('active');
}

/**
 * Update Category Chart
 */
function updateCategoryChart(categoryData) {
    if (!charts.category) return;
    
    charts.category.data.labels = categoryData.map(item => item.category);
    charts.category.data.datasets[0].data = categoryData.map(item => item.count);
    charts.category.update('active');
}

/**
 * Update Risk Heatmap
 */
function updateHeatmap(heatmapData) {
    const container = document.getElementById('riskHeatmap');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Create 5x5 grid
    for (let impact = 5; impact >= 1; impact--) {
        for (let probability = 1; probability <= 5; probability++) {
            const risks = heatmapData.filter(risk => 
                risk.probability === probability && risk.impact === impact
            );
            
            const cell = document.createElement('div');
            const riskScore = probability * impact;
            const riskLevel = riskScore > 20 ? 5 : Math.ceil(riskScore / 5);
            
            cell.className = `heatmap-cell risk-${riskLevel}`;
            cell.textContent = risks.length;
            cell.title = `Probability: ${probability}, Impact: ${impact}\n${risks.length} risks`;
            
            if (risks.length > 0) {
                cell.addEventListener('click', () => showRiskDetails(risks));
            }
            
            container.appendChild(cell);
        }
    }
}

/**
 * Show Risk Details Modal
 */
function showRiskDetails(risks) {
    const modal = document.createElement('div');
    modal.className = 'bi-modal';
    
    const content = `
        <div class="bi-modal-content">
            <div class="bi-modal-header">
                <h3>Risk Details</h3>
                <button onclick="this.closest('.bi-modal').remove()" class="bi-modal-close">&times;</button>
            </div>
            <div class="bi-modal-body">
                <ul class="risk-list">
                    ${risks.map(risk => `
                        <li>
                            <strong>${risk.title}</strong>
                            <span class="risk-category">${risk.category}</span>
                            <span class="risk-department">${risk.department}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;
    
    modal.innerHTML = content;
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

/**
 * Refresh Dashboard
 */
async function refreshDashboard(manual = false) {
    const refreshBtn = document.getElementById('refreshBtn');
    if (!refreshBtn) return;
    
    const originalContent = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<span class="loading-spinner"></span> Refreshing...';
    refreshBtn.disabled = true;
    
    try {
        await loadDashboardData();
        
        if (manual) {
            showNotification('Dashboard refreshed successfully', 'success');
        }
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        showNotification('Failed to refresh dashboard', 'error');
    } finally {
        refreshBtn.innerHTML = originalContent;
        refreshBtn.disabled = false;
    }
}

/**
 * Auto Refresh Functionality
 */
function startAutoRefresh() {
    // Refresh every 30 seconds
    updateInterval = setInterval(() => {
        if (isAutoRefresh) {
            refreshDashboard(false);
        }
    }, 30000);
}

function stopAutoRefresh() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

/**
 * Export Dashboard Data
 */
async function exportDashboard() {
    try {
        const exportBtn = document.getElementById('exportBtn');
        if (!exportBtn) return;
        
        exportBtn.disabled = true;
        exportBtn.innerHTML = '<span class="loading-spinner"></span> Exporting...';
        
        const exportData = {
            data_type: 'dashboard',
            format: 'excel',
            filters: {
                time_range: document.getElementById('timeRange')?.value || '30d',
                department_id: document.getElementById('departmentFilter')?.value || null
            }
        };
        
        const response = await fetch('/bi-tools/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(exportData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`Export generated: ${data.filename}`, 'success');
            // In production, trigger download
            // window.location.href = data.download_url;
        } else {
            throw new Error(data.error || 'Export failed');
        }
    } catch (error) {
        console.error('Export error:', error);
        showNotification('Export failed', 'error');
    } finally {
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.disabled = false;
            exportBtn.innerHTML = '<i class="fas fa-download"></i> Export';
        }
    }
}

/**
 * Show/Hide Loading State
 */
function showLoading() {
    document.body.classList.add('loading');
}

function hideLoading() {
    document.body.classList.remove('loading');
}

/**
 * Animate Updates
 */
function animateUpdates() {
    document.querySelectorAll('.metric-card').forEach((card, index) => {
        card.style.animation = 'none';
        setTimeout(() => {
            card.style.animation = `fadeInUp 0.6s ease-out forwards`;
            card.style.animationDelay = `${index * 0.1}s`;
        }, 10);
    });
}

/**
 * Initialize Tooltips
 */
function initializeTooltips() {
    // Add tooltips to elements with title attribute
    document.querySelectorAll('[title]').forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'bi-tooltip';
    tooltip.textContent = e.target.title;
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    
    e.target.dataset.originalTitle = e.target.title;
    e.target.title = '';
}

function hideTooltip(e) {
    const tooltip = document.querySelector('.bi-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
    
    if (e.target.dataset.originalTitle) {
        e.target.title = e.target.dataset.originalTitle;
        delete e.target.dataset.originalTitle;
    }
}

/**
 * Notification System
 */
function setupNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notificationContainer')) {
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';
    
    notification.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 5000);
}

/**
 * Use Mock Data (Fallback)
 */
function useMockData() {
    const mockData = {
        summary: {
            total_risks: 234,
            high_risks: 45,
            completed_assessments: 189,
            control_effectiveness_ratio: 78.5,
            compliance_score: 85.3,
            risk_velocity: 2.4
        },
        risk_trends: Array.from({length: 30}, (_, i) => ({
            date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
            count: Math.floor(Math.random() * 20) + 5
        })),
        category_distribution: [
            {category: 'Operational', count: 45},
            {category: 'Financial', count: 32},
            {category: 'Compliance', count: 28},
            {category: 'Strategic', count: 24},
            {category: 'Technology', count: 38},
            {category: 'Reputational', count: 18}
        ],
        heatmap_data: Array.from({length: 25}, () => ({
            probability: Math.floor(Math.random() * 5) + 1,
            impact: Math.floor(Math.random() * 5) + 1,
            title: `Risk ${Math.floor(Math.random() * 1000)}`,
            category: ['Operational', 'Financial', 'Compliance'][Math.floor(Math.random() * 3)],
            department: ['IT', 'Finance', 'HR', 'Operations'][Math.floor(Math.random() * 4)]
        }))
    };
    
    updateDashboard(mockData);
}

// Export functions for external use
window.BITools = {
    refreshDashboard,
    loadDashboardData,
    showNotification,
    exportDashboard
};