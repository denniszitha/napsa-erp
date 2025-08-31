from flask import Blueprint, render_template

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/')
def index():
    return render_template('audit/index.html')
