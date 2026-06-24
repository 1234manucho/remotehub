import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from datetime import datetime, timezone
from config import Config
from models import db, User, Notification
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.job_routes import job_bp
from routes.proxy_routes import proxy_bp
from routes.dashboard_routes import dashboard_bp
from routes.admin_routes import admin_bp
from routes.profile_routes import profile_bp
from routes.chat_routes import chat_bp
from routes.notifications_routes import notif_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Fix Render's 'postgres://' → 'postgresql://'
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    # Upload folder for chat attachments
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(job_bp, url_prefix='/jobs')
    app.register_blueprint(proxy_bp, url_prefix='/proxy')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(notif_bp, url_prefix='/notifications')

    # Custom filter: clean slugs for category URLs
    @app.template_filter('slugify')
    def slugify(text):
        slug = text.lower().replace(' & ', ' and ').replace(' ', '-')
        while '--' in slug:
            slug = slug.replace('--', '-')
        return slug

    # Context processor for current year in footer
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}

    # Context processor for unread notification count
    @app.context_processor
    def inject_unread_notifications():
        count = 0
        if current_user.is_authenticated:
            count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {'unread_notifications_count': count}

    with app.app_context():
        db.create_all()

    return app

# Create the app instance at module level for Gunicorn
app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app.run(debug=True)