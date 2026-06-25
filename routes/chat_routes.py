import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Conversation, Message, Notification, Job, User, ProxyPlan, ProxyPurchase
from datetime import datetime, timezone

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'xlsx', 'pptx'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_notification(user_id, message, notif_type='chat'):
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
    for conv in convos:
        conv._msg_count = Message.query.filter_by(conversation_id=conv.id).count()
        last_msg = Message.query.filter_by(conversation_id=conv.id).order_by(Message.timestamp.desc()).first()
        conv._last_msg = last_msg.content[:50] + '...' if last_msg and len(last_msg.content) > 50 else (last_msg.content if last_msg else '')
        conv._last_time = last_msg.timestamp.strftime('%H:%M') if last_msg else conv.updated_at.strftime('%H:%M')
    return render_template('chat/conversations.html', conversations=convos)


# ---------- Start a Conversation ----------
@chat_bp.route('/start/<int:job_id>', methods=['POST'])
@login_required
def start_conversation(job_id):
    job = Job.query.get_or_404(job_id)
    existing = Conversation.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        return redirect(url_for('chat.view_conversation', conv_id=existing.id))

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
    if conv.user_id != current_user.id and conv.admin_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('chat.list_conversations'))

    if request.method == 'POST':
        # Block message sending if proxy is assigned but not purchased
        if conv.assigned_proxy_plan_id and not conv.proxy_purchase_id:
            flash('You must purchase the assigned proxy before sending messages.', 'warning')
            return redirect(url_for('chat.view_conversation', conv_id=conv.id))

        content = request.form.get('message', '').strip()
        attachment_path = None

        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'chat')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                attachment_path = f'uploads/chat/{filename}'

        if not content and not attachment_path:
            return redirect(url_for('chat.view_conversation', conv_id=conv.id))

        receiver_id = conv.admin_id if current_user.id == conv.user_id else conv.user_id

        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            attachment=attachment_path
        )
        db.session.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        create_notification(receiver_id, f'New message from {current_user.username}', 'chat')
        flash('Message sent.', 'success')
        return redirect(url_for('chat.view_conversation', conv_id=conv.id))

    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.timestamp).all()
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.session.commit()

    # Proxy assignment data for template
    assigned_plan = ProxyPlan.query.get(conv.assigned_proxy_plan_id) if conv.assigned_proxy_plan_id else None
    proxy_purchased = conv.proxy_purchase_id is not None

    return render_template('chat/conversation.html',
                           conversation=conv,
                           messages=messages,
                           assigned_plan=assigned_plan,
                           proxy_purchased=proxy_purchased)