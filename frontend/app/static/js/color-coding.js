/**
 * NAPSA ERM - Color Coding Utility Functions
 * Provides dynamic color coding throughout the application
 */

class ColorCoding {
    constructor() {
        this.riskColors = {
            1: { class: 'risk-low', color: '#10b981', label: 'Low' },
            2: { class: 'risk-low', color: '#10b981', label: 'Low' },
            3: { class: 'risk-low', color: '#10b981', label: 'Low' },
            4: { class: 'risk-low', color: '#10b981', label: 'Low' },
            5: { class: 'risk-medium', color: '#f59e0b', label: 'Medium' },
            6: { class: 'risk-medium', color: '#f59e0b', label: 'Medium' },
            7: { class: 'risk-medium', color: '#f59e0b', label: 'Medium' },
            8: { class: 'risk-medium', color: '#f59e0b', label: 'Medium' },
            9: { class: 'risk-medium', color: '#f59e0b', label: 'Medium' },
            10: { class: 'risk-high', color: '#fd7e14', label: 'High' },
            11: { class: 'risk-high', color: '#fd7e14', label: 'High' },
            12: { class: 'risk-high', color: '#fd7e14', label: 'High' },
            13: { class: 'risk-high', color: '#fd7e14', label: 'High' },
            14: { class: 'risk-high', color: '#fd7e14', label: 'High' },
            15: { class: 'risk-very-high', color: '#ef4444', label: 'Very High' },
            16: { class: 'risk-very-high', color: '#ef4444', label: 'Very High' },
            17: { class: 'risk-very-high', color: '#ef4444', label: 'Very High' },
            18: { class: 'risk-very-high', color: '#ef4444', label: 'Very High' },
            19: { class: 'risk-very-high', color: '#ef4444', label: 'Very High' },
            20: { class: 'risk-critical', color: '#6366f1', label: 'Critical' },
            21: { class: 'risk-critical', color: '#6366f1', label: 'Critical' },
            22: { class: 'risk-critical', color: '#6366f1', label: 'Critical' },
            23: { class: 'risk-critical', color: '#6366f1', label: 'Critical' },
            24: { class: 'risk-critical', color: '#6366f1', label: 'Critical' },
            25: { class: 'risk-critical', color: '#6366f1', label: 'Critical' }
        };

        this.statusColors = {
            'active': { class: 'status-active', color: '#10b981' },
            'inactive': { class: 'status-inactive', color: '#6b7280' },
            'pending': { class: 'status-pending', color: '#f59e0b' },
            'overdue': { class: 'status-overdue', color: '#ef4444' },
            'completed': { class: 'status-completed', color: '#059669' },
            'draft': { class: 'status-draft', color: '#94a3b8' },
            'under_review': { class: 'status-review', color: '#3b82f6' },
            'approved': { class: 'status-approved', color: '#10b981' },
            'rejected': { class: 'status-rejected', color: '#dc2626' }
        };

        this.departmentColors = {
            'finance': { class: 'dept-finance', color: '#1e40af' },
            'operations': { class: 'dept-operations', color: '#7c3aed' },
            'it': { class: 'dept-it', color: '#059669' },
            'hr': { class: 'dept-hr', color: '#dc2626' },
            'legal': { class: 'dept-legal', color: '#374151' },
            'compliance': { class: 'dept-compliance', color: '#0891b2' },
            'audit': { class: 'dept-audit', color: '#9333ea' },
            'credit': { class: 'dept-credit', color: '#ea580c' },
            'treasury': { class: 'dept-treasury', color: '#0d9488' }
        };

        this.priorityColors = {
            'critical': { class: 'priority-critical', color: '#7c2d12' },
            'high': { class: 'priority-high', color: '#dc2626' },
            'medium': { class: 'priority-medium', color: '#d97706' },
            'low': { class: 'priority-low', color: '#16a34a' },
            'info': { class: 'priority-info', color: '#0284c7' }
        };

        this.complianceColors = {
            'compliant': { class: 'compliance-compliant', color: '#059669' },
            'non_compliant': { class: 'compliance-non-compliant', color: '#dc2626' },
            'partially_compliant': { class: 'compliance-partial', color: '#d97706' },
            'pending': { class: 'compliance-pending', color: '#6b7280' },
            'not_applicable': { class: 'compliance-not-applicable', color: '#94a3b8' }
        };
    }

    /**
     * Get risk color information based on risk score
     * @param {number} score - Risk score (1-25)
     * @returns {object} Color information
     */
    getRiskColor(score) {
        return this.riskColors[score] || this.riskColors[1];
    }

    /**
     * Get status color information
     * @param {string} status - Status value
     * @returns {object} Color information
     */
    getStatusColor(status) {
        const normalizedStatus = status.toLowerCase().replace(/ /g, '_');
        return this.statusColors[normalizedStatus] || this.statusColors['draft'];
    }

    /**
     * Get department color information
     * @param {string} department - Department name
     * @returns {object} Color information
     */
    getDepartmentColor(department) {
        const normalizedDept = department.toLowerCase().replace(/ /g, '_');
        return this.departmentColors[normalizedDept] || { class: 'dept-finance', color: '#1e40af' };
    }

    /**
     * Get priority color information
     * @param {string} priority - Priority level
     * @returns {object} Color information
     */
    getPriorityColor(priority) {
        const normalizedPriority = priority.toLowerCase();
        return this.priorityColors[normalizedPriority] || this.priorityColors['medium'];
    }

    /**
     * Apply color coding to an element
     * @param {HTMLElement} element - DOM element
     * @param {string} type - Color type (risk, status, department, priority)
     * @param {string|number} value - Value to determine color
     */
    applyColor(element, type, value) {
        let colorInfo;
        
        switch(type) {
            case 'risk':
                colorInfo = this.getRiskColor(value);
                break;
            case 'status':
                colorInfo = this.getStatusColor(value);
                break;
            case 'department':
                colorInfo = this.getDepartmentColor(value);
                break;
            case 'priority':
                colorInfo = this.getPriorityColor(value);
                break;
            default:
                return;
        }

        if (colorInfo) {
            element.className = element.className.replace(/\b(risk|status|dept|priority)-\w+/g, '');
            element.classList.add(colorInfo.class);
            element.setAttribute('data-color-value', value);
            element.setAttribute('data-color-type', type);
        }
    }

    /**
     * Apply color coding to a badge element
     * @param {HTMLElement} badge - Badge element
     * @param {string} type - Color type
     * @param {string|number} value - Value
     * @param {string} text - Badge text (optional)
     */
    applyBadgeColor(badge, type, value, text = null) {
        this.applyColor(badge, type, value);
        badge.classList.add('badge');
        if (text) {
            badge.textContent = text;
        }
    }

    /**
     * Generate color-coded HTML badge
     * @param {string} type - Color type
     * @param {string|number} value - Value
     * @param {string} text - Badge text
     * @returns {string} HTML string
     */
    generateBadge(type, value, text = null) {
        const colorInfo = this.getColorInfo(type, value);
        const displayText = text || (typeof value === 'string' ? value.charAt(0).toUpperCase() + value.slice(1) : value);
        
        return `<span class="badge ${colorInfo.class}" data-color-type="${type}" data-color-value="${value}">${displayText}</span>`;
    }

    /**
     * Get color information for any type
     * @param {string} type - Color type
     * @param {string|number} value - Value
     * @returns {object} Color information
     */
    getColorInfo(type, value) {
        switch(type) {
            case 'risk':
                return this.getRiskColor(value);
            case 'status':
                return this.getStatusColor(value);
            case 'department':
                return this.getDepartmentColor(value);
            case 'priority':
                return this.getPriorityColor(value);
            case 'compliance':
                return this.getComplianceColor(value);
            default:
                return { class: 'badge-secondary', color: '#6b7280' };
        }
    }

    /**
     * Get compliance color information
     * @param {string} compliance - Compliance status
     * @returns {object} Color information
     */
    getComplianceColor(compliance) {
        const normalizedCompliance = compliance.toLowerCase().replace(/ /g, '_');
        return this.complianceColors[normalizedCompliance] || this.complianceColors['pending'];
    }

    /**
     * Apply color coding to DataTable cells
     * @param {DataTable} table - DataTables instance
     * @param {object} columnConfig - Column configuration
     */
    applyDataTableColors(table, columnConfig) {
        table.on('draw', () => {
            Object.keys(columnConfig).forEach(columnIndex => {
                const config = columnConfig[columnIndex];
                const cells = table.column(columnIndex).nodes();
                
                cells.each((cell, index) => {
                    const data = table.cell(cell).data();
                    let value = data;
                    
                    if (config.valueExtractor) {
                        value = config.valueExtractor(data);
                    }
                    
                    this.applyColor(cell, config.type, value);
                });
            });
        });
    }

    /**
     * Generate chart colors for ApexCharts
     * @param {string} type - Chart type (risk, status, department, etc.)
     * @param {Array} values - Array of values
     * @returns {Array} Array of colors
     */
    generateChartColors(type, values) {
        return values.map(value => {
            const colorInfo = this.getColorInfo(type, value);
            return colorInfo.color;
        });
    }

    /**
     * Apply risk matrix colors
     * @param {HTMLElement} matrixContainer - Matrix container element
     * @param {object} matrixConfig - Matrix configuration
     */
    applyMatrixColors(matrixContainer, matrixConfig) {
        const cells = matrixContainer.querySelectorAll('.matrix-cell[data-score]');
        
        cells.forEach(cell => {
            const score = parseInt(cell.getAttribute('data-score'));
            if (score) {
                const colorInfo = this.getRiskColor(score);
                cell.className = cell.className.replace(/\brisk-level-\w+/g, '');
                cell.classList.add(colorInfo.class.replace('risk-', 'risk-level-'));
                cell.setAttribute('title', `Risk Score: ${score} (${colorInfo.label})`);
            }
        });
    }

    /**
     * Create color legend for charts/tables
     * @param {string} type - Color type
     * @param {Array} values - Values to include in legend
     * @returns {HTMLElement} Legend element
     */
    createColorLegend(type, values) {
        const legend = document.createElement('div');
        legend.className = 'color-legend d-flex flex-wrap gap-2 mb-3';
        
        values.forEach(value => {
            const colorInfo = this.getColorInfo(type, value);
            const item = document.createElement('div');
            item.className = 'd-flex align-items-center gap-1';
            item.innerHTML = `
                <div class="color-swatch ${colorInfo.class}" style="width: 16px; height: 16px; border-radius: 3px;"></div>
                <small class="text-muted">${typeof value === 'string' ? value.charAt(0).toUpperCase() + value.slice(1) : value}</small>
            `;
            legend.appendChild(item);
        });
        
        return legend;
    }

    /**
     * Initialize color coding for the page
     * @param {object} config - Page-specific configuration
     */
    initializePageColors(config = {}) {
        // Apply automatic color coding to elements with data attributes
        const elements = document.querySelectorAll('[data-color-type][data-color-value]');
        elements.forEach(element => {
            const type = element.getAttribute('data-color-type');
            const value = element.getAttribute('data-color-value');
            this.applyColor(element, type, value);
        });

        // Apply badge colors
        const badges = document.querySelectorAll('.badge[data-color-type][data-color-value]');
        badges.forEach(badge => {
            const type = badge.getAttribute('data-color-type');
            const value = badge.getAttribute('data-color-value');
            this.applyBadgeColor(badge, type, value);
        });

        // Custom page configurations
        if (config.matrixContainer) {
            this.applyMatrixColors(config.matrixContainer, config.matrixConfig || {});
        }
    }

    /**
     * Update colors when data changes
     * @param {string} selector - CSS selector for elements to update
     * @param {string} type - Color type
     * @param {Function} valueExtractor - Function to extract value from element
     */
    updateDynamicColors(selector, type, valueExtractor) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            const value = valueExtractor(element);
            this.applyColor(element, type, value);
        });
    }
}

// Create global instance
window.ColorCoding = new ColorCoding();

// jQuery integration
if (typeof $ !== 'undefined') {
    $.fn.applyColors = function(type, valueExtractor) {
        return this.each(function() {
            const value = typeof valueExtractor === 'function' ? 
                valueExtractor($(this)) : 
                $(this).data('color-value');
            window.ColorCoding.applyColor(this, type, value);
        });
    };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    window.ColorCoding.initializePageColors();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ColorCoding;
}