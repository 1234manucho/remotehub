from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Withdrawal
from datetime import datetime, timezone

withdraw_bp = Blueprint('withdraw', __name__, url_prefix='/withdraw')

@withdraw_bp.route('/request', methods=['POST'])
@login_required
def request_withdrawal():
    amount = request.form.get('amount', '').strip()
    wallet = request.form.get('wallet', '').strip()
    method = request.form.get('method', 'trc20')

    if not amount or not wallet:
        flash('Please fill in all fields.', 'danger')
        return redirect(url_for('dashboard.overview'))

    try:
        amount = float(amount)
    except ValueError:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('dashboard.overview'))

    if amount <= 0:
        flash('Amount must be greater than zero.', 'danger')
        return redirect(url_for('dashboard.overview'))

    withdrawal = Withdrawal(
        user_id=current_user.id,
        amount=amount,
        payment_method=method,
        phone_number=wallet,   # we store wallet address in phone_number for simplicity
        status='pending'
    )
    db.session.add(withdrawal)
    db.session.commit()

    flash('Withdrawal request submitted! Admin will review it shortly.', 'success')
    return redirect(url_for('dashboard.overview'))


# ==================== ADMIN APPROVE / REJECT ====================
@withdraw_bp.route('/admin/approve/<int:withdrawal_id>')
@login_required
def admin_approve(withdrawal_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    if withdrawal.status != 'pending':
        flash('This withdrawal has already been processed.', 'info')
        return redirect(url_for('admin.dashboard'))

    withdrawal.status = 'approved'
    withdrawal.processed_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f'Withdrawal #{withdrawal.id} approved.', 'success')
    return redirect(url_for('admin.dashboard'))

@withdraw_bp.route('/admin/reject/<int:withdrawal_id>')
@login_required
def admin_reject(withdrawal_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    if withdrawal.status != 'pending':
        flash('This withdrawal has already been processed.', 'info')
        return redirect(url_for('admin.dashboard'))

    withdrawal.status = 'rejected'
    withdrawal.processed_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f'Withdrawal #{withdrawal.id} rejected.', 'info')
    return redirect(url_for('admin.dashboard'))