from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def overview():
    stats = {
        'applications': 0,
        'saved_jobs': 0,
        'proxies': 0,
        'views': 0
    }
    return render_template('dashboard.html',
                           stats=stats,
                           saved_jobs=[],
                           applications=[],
                           user_proxies=[])