import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Conversation, Message, SubscriptionPlan, UserSubscription, Notification, Job, User
from datetime import datetime, timezone, timedelta

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_active_subscription(user_id):
    """Return the user's active chat subscription or None."""
    now = datetime.now(timezone.utc)
    return UserSubscription.query.filter(
        UserSubscription.user_id == user_id,
        UserSubscription.is_active == True,
        UserSubscription.end_date > now
    ).first()

def free_message_count(conversation_id):
    """Count messages sent by the user (not admin) in a conversation."""
    return Message.query.filter_by(conversation_id=conversation_id).count()

def create_notification(user_id, message, notif_type='chat'):
    """Helper to create a notification for a user."""
    notif = Notification(user_id=user_id, message=message, type=notif_type)
    db.session.add(notif)
    db.session.commit()


# ---------- Conversation List ----------
@chat_bp.route('/')
@login_required
def list_conversations():
    convos = Conversation.query.filter(
        (Conversation.user_id == current_user.id) | (Conversation.admin_id == current_user.id)
    ).order_by(Conversation.updated_at.desc()).all()
    # Precompute message counts for each conversation
    for conv in convos:
        conv._msg_count = Message.query.filter_by(conversation_id=conv.id).count()
    return render_template('chat/conversations.html', conversations=convos)


# ---------- Start a Conversation ----------
@chat_bp.route('/start/<int:job_id>', methods=['POST'])
@login_required
def start_conversation(job_id):
    job = Job.query.get_or_404(job_id)
    # Check if user already has a conversation for this job
    existing = Conversation.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        return redirect(url_for('chat.view_conversation', conv_id=existing.id))

    # Create new conversation (admin_id could be the job poster / admin for now use any admin)
    admin = User.query.filter_by(is_admin=True).first()
    conv = Conversation(user_id=current_user.id, admin_id=admin.id if admin else None, job_id=job_id)
    db.session.add(conv)
    db.session.commit()
    return redirect(url_for('chat.view_conversation', conv_id=conv.id))


# ---------- View Conversation & Send Message ----------
@chat_bp.route('/<int:conv_id>', methods=['GET', 'POST'])
@login_required
def view_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    # Ensure user is participant
    if conv.user_id != current_user.id and conv.admin_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('chat.list_conversations'))

    if request.method == 'POST':
        # Check message limit for non-admin users
        if not current_user.is_admin and conv.admin_id != current_user.id:
            # Only the job applicant (not admin) is subject to limit
            msg_count = free_message_count(conv.id)
            if msg_count >= 5:
                sub = get_active_subscription(current_user.id)
                if not sub:
                    flash('You have reached the free message limit. Please subscribe to continue.', 'warning')
                    return redirect(url_for('chat.subscribe'))

        content = request.form.get('message', '').strip()
        if not content and 'attachment' not in request.files:
            flash('Message cannot be empty.', 'danger')
            return redirect(url_for('chat.view_conversation', conv_id=conv.id))

        # Handle file upload
        attachment_path = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                attachment_path = f'uploads/{filename}'

        # Determine receiver
        receiver_id = conv.admin_id if current_user.id == conv.user_id else conv.user_id

        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content if content else '',
            attachment=attachment_path
        )
        db.session.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Notify the other party
        create_notification(receiver_id, f'New message from {current_user.username} in conversation #{conv.id}', 'chat')

        flash('Message sent.', 'success')
        return redirect(url_for('chat.view_conversation', conv_id=conv.id))

    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.timestamp).all()
    # Mark unread messages as read for this user
    unread = [m for m in messages if m.receiver_id == current_user.id and not m.is_read]
    for m in unread:
        m.is_read = True
    db.session.commit()

    return render_template('chat/conversation.html', conversation=conv, messages=messages)


# ---------- Subscription Page ----------
@chat_bp.route('/subscribe')
@login_required
def subscribe():
    plan = SubscriptionPlan.query.filter_by(is_active=True).first()
    if not plan:
        flash('No subscription plans available.', 'danger')
        return redirect(url_for('chat.list_conversations'))
    # Check if user already has active subscription
    active_sub = get_active_subscription(current_user.id)
    return render_template('chat/subscribe.html', plan=plan, active_subscription=active_sub)


@chat_bp.route('/subscribe/checkout/<int:plan_id>')
@login_required
def checkout_subscription(plan_id):
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    # Here you would integrate PayHero again to charge $20.
    # For now, simulate activation
    active_sub = get_active_subscription(current_user.id)
    if active_sub:
        flash('You already have an active subscription.', 'info')
        return redirect(url_for('chat.subscribe'))

    # Create a UserSubscription immediately (simulate successful payment)
    sub = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
        is_active=True
    )
    db.session.add(sub)
    db.session.commit()

    create_notification(current_user.id, 'Your chat subscription has been activated!', 'subscription')
    flash('Subscription activated! You can now chat freely.', 'success')
    return redirect(url_for('chat.list_conversations'))