import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'

    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'social_commerce_analytics'

    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {'charset': 'utf8mb4'}
    }

    # TikTok API Configuration
    TIKTOK_ACCESS_TOKEN = os.environ.get('TIKTOK_ACCESS_TOKEN') or 'your-tiktok-access-token'
    TIKTOK_CLIENT_KEY = os.environ.get('TIKTOK_CLIENT_KEY') or 'your-client-key'
    TIKTOK_CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET') or 'your-client-secret'

    # Data Collection Settings
    DATA_COLLECTION_INTERVAL = int(os.environ.get('DATA_COLLECTION_INTERVAL') or 3600)  # seconds
    MAX_POSTS_PER_KEYWORD = int(os.environ.get('MAX_POSTS_PER_KEYWORD') or 100)

    # Analytics Settings
    TRENDING_THRESHOLD = int(os.environ.get('TRENDING_THRESHOLD') or 1000)  # minimum likes for trending
    DAYS_FOR_TRENDING = int(os.environ.get('DAYS_FOR_TRENDING') or 7)

    # Shopee Scraping Settings
    SHOPEE_SCRAPE_INTERVAL = int(os.environ.get('SHOPEE_SCRAPE_INTERVAL') or 7200)  # 2 hours
    SHOPEE_MAX_PAGES = int(os.environ.get('SHOPEE_MAX_PAGES') or 5)
    SHOPEE_DELAY_MIN = int(os.environ.get('SHOPEE_DELAY_MIN') or 2)
    SHOPEE_DELAY_MAX = int(os.environ.get('SHOPEE_DELAY_MAX') or 5)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}