import uuid
import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, ProxyPlan, ProxyPurchase, Payment, Conversation
from datetime import datetime, timezone, timedelta
from config import Config

proxy_bp = Blueprint('proxy', __name__)
logger = logging.getLogger(__name__)


def allocate_proxy_for_user(plan, user_id):
    """Allocate a real proxy (placeholder for now)."""
    logger.warning("Using placeholder proxy allocation – replace with real provider.")
    return f"10.0.{plan.id}.{user_id % 255}", "US"


@proxy_bp.route('/marketplace')
@login_required
def marketplace():
    plans = ProxyPlan.query.filter_by(is_active=True).order_by(ProxyPlan.price).all()
    return render_template('proxy_marketplace.html', proxy_plans=plans)


@proxy_bp.route('/purchase/<int:plan_id>')
@login_required
def purchase(plan_id):
    plan = ProxyPlan.query.get_or_404(plan_id)

    # 1. Create a pending payment
    payment = Payment(
        user_id=current_user.id,
        plan_id=plan.id,
        amount=plan.price,
        currency='USDT',
        status='pending',
        transaction_id=str(uuid.uuid4()),
    )
    # Link to conversation if present
    conv_id = request.args.get('conv_id')
    if conv_id:
        payment.conversation_id = int(conv_id)

    db.session.add(payment)
    db.session.commit()

    # 2. Show crypto payment instructions
    return render_template('crypto_payment.html',
                           payment=payment,
                           plan=plan,
                           wallet=Config.TRC20_WALLET,
                           contract=Config.TRC20_CONTRACT)


# ==================== ADMIN APPROVES CRYPTO PAYMENT ====================
@proxy_bp.route('/admin/approve/<int:payment_id>')
@login_required
def admin_approve(payment_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    payment = Payment.query.get_or_404(payment_id)
    if payment.status != 'pending':
        flash('This payment has already been processed.', 'info')
        return redirect(url_for('admin.dashboard'))

    # Mark payment completed
    payment.status = 'completed'
    payment.completed_at = datetime.now(timezone.utc)

    # Allocate and activate the proxy
    plan = ProxyPlan.query.get(payment.plan_id)
    if plan:
        proxy_ip, country = allocate_proxy_for_user(plan, payment.user_id)
        proxy_purchase = ProxyPurchase(
            user_id=payment.user_id,
            plan_id=plan.id,
            proxy_ip=proxy_ip,
            country=country,
            purchased_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.session.add(proxy_purchase)
        db.session.flush()
        payment.proxy_purchase_id = proxy_purchase.id

        # If this payment came from a conversation, link the purchase
        if payment.conversation_id:
            conv = Conversation.query.get(payment.conversation_id)
            if conv:
                conv.proxy_purchase_id = proxy_purchase.id

    db.session.commit()
    flash(f'Payment #{payment.id} approved! Proxy activated.', 'success')
    return redirect(url_for('admin.dashboard'))


@proxy_bp.route('/admin/reject/<int:payment_id>')
@login_required
def admin_reject(payment_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    payment = Payment.query.get_or_404(payment_id)
    if payment.status != 'pending':
        flash('This payment has already been processed.', 'info')
        return redirect(url_for('admin.dashboard'))

    payment.status = 'failed'
    db.session.commit()
    flash(f'Payment #{payment.id} rejected.', 'info')
    return redirect(url_for('admin.dashboard'))


# ==================== STATUS CHECK (AJAX endpoint) ====================
@proxy_bp.route('/status/<int:payment_id>')
@login_required
def payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    if payment.user_id != current_user.id and not current_user.is_admin:
        return {'error': 'Access denied'}, 403
    return {
        'status': payment.status,
        'transaction_id': payment.transaction_id
    }