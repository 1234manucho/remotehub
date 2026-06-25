from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import JobApplication, SavedJob, ProxyPurchase, Notification, Message

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def overview():
    # Stats
    applications_count = JobApplication.query.filter_by(user_id=current_user.id).count()
    saved_count = SavedJob.query.filter_by(user_id=current_user.id).count()
    proxies_count = ProxyPurchase.query.filter_by(user_id=current_user.id).count()

    # Recent activity (notifications + messages)
    notifications = Notification.query.filter_by(user_id=current_user.id) \
                        .order_by(Notification.created_at.desc()).limit(5).all()
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).limit(5).all()

    # Combine into an activity feed sorted by time
    activity = []
    for n in notifications:
        activity.append({
            'type': 'notification',
            'text': n.message,
            'time': n.created_at
        })
    for m in messages:
        other = m.sender.username if m.sender_id != current_user.id else m.receiver.username
        activity.append({
            'type': 'message',
            'text': f'Message from {other}: {m.content[:60]}{"..." if len(m.content) > 60 else ""}',
            'time': m.timestamp
        })
    # Sort by time descending, take first 5
    activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = activity[:5]

    return render_template('dashboard.html',
                           applications=applications_count,
                           saved_jobs=saved_count,
                           proxies=proxies_count,
                           applications_list=JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.applied_at.desc()).limit(5).all(),
                           saved_jobs_list=SavedJob.query.filter_by(user_id=current_user.id).all(),
                           user_proxies=ProxyPurchase.query.filter_by(user_id=current_user.id).all(),
                           recent_activity=recent_activity)