from flask import Blueprint, render_template

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/')
def index():
    return render_template('metrics/index.html')
