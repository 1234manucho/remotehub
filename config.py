import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'remotehub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # TRC20 Crypto Payment Settings
    TRC20_WALLET = os.environ.get('TRC20_WALLET', 'TV3niXZ93z7vN98wBBkpgTFb7cpz8hcq3Y')
    TRC20_CONTRACT = os.environ.get('TRC20_CONTRACT', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')