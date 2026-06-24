from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Job, ProxyPlan, Payment, Conversation
from datetime import datetime, timezone

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(func):
    """Decorator to ensure only admins can access these routes."""
    from functools import wraps
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.home'))
        return func(*args, **kwargs)
    return wrapper

# ==================== DASHBOARD ====================
@admin_bp.route('/')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_proxy_plans = ProxyPlan.query.count()
    total_payments = Payment.query.filter_by(status='completed').count()
    total_conversations = Conversation.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.posted_date.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_jobs=total_jobs,
                           total_proxy_plans=total_proxy_plans,
                           total_payments=total_payments,
                           total_conversations=total_conversations,
                           recent_users=recent_users,
                           recent_jobs=recent_jobs)

# ==================== MANAGE JOBS ====================
@admin_bp.route('/jobs')
@admin_required
def manage_jobs():
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    return render_template('admin/jobs.html', jobs=jobs)

@admin_bp.route('/jobs/toggle/<int:job_id>')
@admin_required
def toggle_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.is_active = not job.is_active
    db.session.commit()
    flash(f'Job "{job.title}" status updated.', 'success')
    return redirect(url_for('admin.manage_jobs'))

@admin_bp.route('/jobs/delete/<int:job_id>')
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash(f'Job "{job.title}" deleted.', 'success')
    return redirect(url_for('admin.manage_jobs'))

# ==================== MANAGE USERS ====================
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/toggle-admin/<int:user_id>')
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'danger')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'User "{user.username}" admin status updated.', 'success')
    return redirect(url_for('admin.manage_users'))

# ==================== MANAGE PROXY PLANS ====================
@admin_bp.route('/proxy-plans')
@admin_required
def manage_proxy_plans():
    plans = ProxyPlan.query.all()
    return render_template('admin/proxy_plans.html', plans=plans)

@admin_bp.route('/proxy-plans/toggle/<int:plan_id>')
@admin_required
def toggle_proxy_plan(plan_id):
    plan = ProxyPlan.query.get_or_404(plan_id)
    plan.is_active = not plan.is_active
    db.session.commit()
    flash(f'Plan "{plan.name}" status updated.', 'success')
    return redirect(url_for('admin.manage_proxy_plans'))

# ==================== CONVERSATIONS ====================
@admin_bp.route('/conversations')
@admin_required
def manage_conversations():
    convos = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    return render_template('admin/conversations.html', conversations=convos)