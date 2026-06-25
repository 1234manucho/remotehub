from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()

# ---------- EXISTING TABLES (UNCHANGED) ----------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150))
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)
    avatar = db.Column(db.String(256))
    resume_path = db.Column(db.String(256))
    portfolio_url = db.Column(db.String(256))
    github_url = db.Column(db.String(256))
    linkedin_url = db.Column(db.String(256))
    website = db.Column(db.String(256))
    languages = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_admin = db.Column(db.Boolean, default=False)

    applications = db.relationship('JobApplication', backref='user', lazy='dynamic')
    saved_jobs = db.relationship('SavedJob', backref='user', lazy='dynamic')
    proxy_purchases = db.relationship('ProxyPurchase', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    subscriptions = db.relationship('UserSubscription', backref='user', lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    logo = db.Column(db.String(256))
    description = db.Column(db.Text)
    website = db.Column(db.String(256))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    jobs = db.relationship('Job', backref='company', lazy='dynamic')


class JobCategory(db.Model):
    __tablename__ = 'job_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    jobs = db.relationship('Job', backref='category', lazy='dynamic')


class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('job_categories.id'))
    parent_category = db.Column(db.String(100))
    employment_type = db.Column(db.String(50))
    salary = db.Column(db.String(100))
    experience_level = db.Column(db.String(100))
    location = db.Column(db.String(100))
    timezone = db.Column(db.String(100))
    description = db.Column(db.Text)
    responsibilities = db.Column(db.Text)
    qualifications = db.Column(db.Text)
    skills_required = db.Column(db.Text)
    posted_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    application_deadline = db.Column(db.DateTime)
    proxy_required = db.Column(db.Boolean, default=False)
    proxy_country = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    benefits = db.Column(db.Text)
    contract_type = db.Column(db.String(50))

    applications = db.relationship('JobApplication', backref='job', lazy='dynamic')
    saved_by = db.relationship('SavedJob', backref='job', lazy='dynamic')


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    cover_letter = db.Column(db.Text)


class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ProxyPlan(db.Model):
    __tablename__ = 'proxy_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(50))
    features = db.Column(db.Text)
    popular = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    purchases = db.relationship('ProxyPurchase', backref='plan', lazy='dynamic')


class ProxyPurchase(db.Model):
    __tablename__ = 'proxy_purchases'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('proxy_plans.id'), nullable=False)
    proxy_ip = db.Column(db.String(100))
    country = db.Column(db.String(100))
    purchased_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('proxy_plans.id'))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(50), default='pending')
    transaction_id = db.Column(db.String(100), unique=True)
    payhero_reference = db.Column(db.String(100), unique=True, nullable=True)
    proxy_purchase_id = db.Column(db.Integer, db.ForeignKey('proxy_purchases.id'))
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='payments')
    plan = db.relationship('ProxyPlan', backref='payments')


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ===================== CHAT & SUBSCRIPTION =====================

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True)
    assigned_proxy_plan_id = db.Column(db.Integer, db.ForeignKey('proxy_plans.id'), nullable=True)
    proxy_purchase_id = db.Column(db.Integer, db.ForeignKey('proxy_purchases.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id])
    admin = db.relationship('User', foreign_keys=[admin_id])
    job = db.relationship('Job')
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', order_by='Message.timestamp')
    assigned_plan = db.relationship('ProxyPlan', foreign_keys=[assigned_proxy_plan_id])


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False)


class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, default=30)
    message_limit = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    subscriptions = db.relationship('UserSubscription', backref='plan', lazy='dynamic')


class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    auto_renew = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ===================== NEW: WITHDRAWALS =====================

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(50))
    phone_number = db.Column(db.String(15))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime)