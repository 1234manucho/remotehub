import requests
import uuid
import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, ProxyPlan, ProxyPurchase, Payment
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
    
    # Get phone number from query parameter
    phone_number = request.args.get('phone')
    if not phone_number:
        flash('Phone number is required to initiate payment. Please provide your M-PESA phone number.', 'warning')
        return redirect(url_for('proxy.marketplace'))

    # 1. Create pending payment
    payment = Payment(
        user_id=current_user.id,
        plan_id=plan.id,
        amount=plan.price,
        currency='KES',
        status='pending',
        transaction_id=str(uuid.uuid4())
    )
    db.session.add(payment)
    db.session.commit()

    # 2. Prepare PayHero M-PESA STK Push request (following PayHero API v2 spec)
    checkout_data = {
        'amount': int(plan.price),  # Amount in KES (cents if needed, check docs)
        'phone_number': phone_number,
        'channel_id': int(Config.PAYHERO_CHANNEL_ID),
        'provider': 'm-pesa',
        'external_reference': payment.transaction_id,
        'customer_name': current_user.full_name or current_user.username,
        'callback_url': Config.PAYHERO_CALLBACK_URL,
    }

    checkout_url = Config.PAYHERO_CHECKOUT_URL
    auth = (Config.PAYHERO_API_USERNAME, Config.PAYHERO_API_PASSWORD)

    try:
        logger.info(f"Posting to PayHero URL: {checkout_url}")
        logger.info(f"Request payload: {checkout_data}")
        logger.info(f"Using auth username: {Config.PAYHERO_API_USERNAME[:5]}...")
        
        response = requests.post(
            checkout_url,
            json=checkout_data,
            auth=auth,
            timeout=30
        )
        logger.info(f"PayHero response status: {response.status_code}")
        logger.info(f"PayHero response headers: {response.headers}")
        logger.info(f"PayHero response body: {response.text}")

        # Check if response is JSON
        if 'application/json' not in response.headers.get('Content-Type', ''):
            payment.status = 'failed'
            db.session.commit()
            logger.error(f"PayHero returned non-JSON. Full body:\n{response.text}")
            flash('Payment service returned an unexpected response. Please try again later.', 'danger')
            return redirect(url_for('proxy.marketplace'))

        response_data = response.json()

        # PayHero M-PESA STK Push returns 201 Created on success
        if response.status_code == 201 and response_data.get('success') == True:
            logger.info(f"STK Push initiated successfully. Reference: {response_data.get('reference')}")
            flash('M-PESA prompt sent to your phone. Please enter your PIN to complete payment.', 'success')
            return redirect(url_for('proxy.marketplace'))
        else:
            payment.status = 'failed'
            db.session.commit()
            logger.error(f"PayHero error response: {response_data}")
            flash('Payment initiation failed. Please try again.', 'danger')
            return redirect(url_for('proxy.marketplace'))

    except requests.exceptions.JSONDecodeError:
        payment.status = 'failed'
        db.session.commit()
        logger.exception("PayHero returned invalid JSON")
        flash('Payment service error. Please try again shortly.', 'danger')
        return redirect(url_for('proxy.marketplace'))
    except requests.RequestException as e:
        payment.status = 'failed'
        db.session.commit()
        logger.exception("PayHero request failed")
        flash('Payment service temporarily unavailable. Please try later.', 'danger')
        return redirect(url_for('proxy.marketplace'))


@proxy_bp.route('/callback', methods=['POST'])
def payhero_callback():
    data = request.get_json() if request.is_json else request.form
    logger.info(f"Callback received: {data}")

    transaction_id = data.get('reference')
    status = data.get('status')
    payhero_ref = data.get('transaction_id')

    if not transaction_id or not status:
        return 'Invalid callback', 400

    payment = Payment.query.filter_by(transaction_id=transaction_id).first()
    if not payment:
        return 'Payment not found', 404

    if status.lower() == 'completed':
        payment.status = 'completed'
        payment.completed_at = datetime.now(timezone.utc)
        payment.payhero_reference = payhero_ref

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

        db.session.commit()
        return 'OK', 200
    else:
        payment.status = 'failed'
        db.session.commit()
        return 'Payment failed', 200