import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'remotehub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PayHero settings
    PAYHERO_BASE_URL = os.environ.get('PAYHERO_BASE_URL', 'https://payhero.co.ke')
    PAYHERO_API_USERNAME = os.environ.get('PAYHERO_API_USERNAME')
    PAYHERO_API_PASSWORD = os.environ.get('PAYHERO_API_PASSWORD')
    PAYHERO_CHECKOUT_URL = os.environ.get('PAYHERO_CHECKOUT_URL')
    PAYHERO_CALLBACK_URL = os.environ.get('PAYHERO_CALLBACK_URL')