from flask import Blueprint, render_template

training_bp = Blueprint('training', __name__)

@training_bp.route('/')
def index():
    return render_template('training/index.html')
