from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Notification

notif_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notif_bp.route('/')
@login_required
def list_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id) \
                .order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('notifications.html', notifications=notifs, unread_count=unread_count)

@notif_bp.route('/read/<int:notif_id>')
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('notifications.list_notifications'))
    notif.is_read = True
    db.session.commit()
    return redirect(url_for('notifications.list_notifications'))
@notif_bp.route('/dismiss/<int:notif_id>')
@login_required
def dismiss(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('notifications.list_notifications'))
    db.session.delete(notif)
    db.session.commit()
    flash('Notification dismissed.', 'success')
    return redirect(url_for('notifications.list_notifications'))
@notif_bp.route('/read-all')
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False) \
        .update({Notification.is_read: True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.list_notifications'))