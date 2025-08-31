"""
Heat Map Routes for Risk Visualization
"""

from flask import Blueprint, render_template, jsonify, request
from app.utils.auth import login_required
import requests
from app.services.api_service import APIService

heatmap_bp = Blueprint('heatmap', __name__, url_prefix='/risks/heatmap')
api_service = APIService()

@heatmap_bp.route('/')
@login_required
def heat_map():
    """Display risk heat map visualization"""
    return render_template('risks/heatmap.html')

@heatmap_bp.route('/api/matrix')
@login_required
def get_matrix_data():
    """Proxy for heat map matrix data"""
    params = {
        'department_id': request.args.get('department_id'),
        'category_id': request.args.get('category_id'),
        'risk_type': request.args.get('risk_type', 'inherent')
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v}
    
    response = api_service.get('/heatmap/matrix', params=params)
    return jsonify(response)

@heatmap_bp.route('/api/trend')
@login_required
def get_trend_data():
    """Proxy for heat map trend data"""
    months = request.args.get('months', 6)
    response = api_service.get(f'/heatmap/trend?months={months}')
    return jsonify(response)

@heatmap_bp.route('/api/categories')
@login_required
def get_category_data():
    """Proxy for category heat map data"""
    response = api_service.get('/heatmap/category-matrix')
    return jsonify(response)

@heatmap_bp.route('/api/department-comparison')
@login_required
def get_department_comparison():
    """Proxy for department comparison data"""
    response = api_service.get('/heatmap/department-comparison')
    return jsonify(response)

@heatmap_bp.route('/export/pdf')
@login_required
def export_pdf():
    """Export heat map as PDF"""
    department_id = request.args.get('department_id')
    
    # Get PDF from backend
    response = api_service.get_raw(
        f'/reports/generate/heatmap/pdf?department_id={department_id}',
        stream=True
    )
    
    return response.content, 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename=risk_heatmap.pdf'
    }