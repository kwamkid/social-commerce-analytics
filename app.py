from flask import Flask
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import os

from config import config
from models import db
from routes.main import main_bp
from routes.api import api_bp
from services.tiktok_collector import TikTokCollector
from models.models import Keyword


def create_app(config_name=None):
    """Factory function สำหรับสร้าง Flask app"""
    app = Flask(__name__)

    # Load configuration
    config_name = config_name or os.environ.get('FLASK_CONFIG', 'development')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize database
    with app.app_context():
        db.create_all()

    return app


def background_data_collection():
    """Background task สำหรับเก็บข้อมูลอัตโนมัติ"""
    with app.app_context():
        try:
            collector = TikTokCollector()

            # ดึง keywords ที่ active
            keywords = Keyword.query.filter_by(is_active=True).all()

            if not keywords:
                print("No active keywords found")
                return

            total_collected = 0
            for keyword in keywords:
                print(f"Collecting data for keyword: {keyword.keyword}")
                collected = collector.collect_for_keyword(keyword.keyword)
                total_collected += collected

                # อัพเดท keyword statistics
                keyword.last_collection_time = db.session.utcnow()
                keyword.total_posts_found += collected

            db.session.commit()
            print(f"Background collection completed. Total posts collected: {total_collected}")

        except Exception as e:
            print(f"Background collection error: {e}")
            db.session.rollback()


# Create app instance
app = create_app()

# Setup background scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Add background job for data collection
scheduler.add_job(
    func=background_data_collection,
    trigger=IntervalTrigger(seconds=app.config.get('DATA_COLLECTION_INTERVAL', 3600)),
    id='data_collection_job',
    name='Collect TikTok data',
    replace_existing=True
)

# Ensure scheduler shuts down cleanly
atexit.register(lambda: scheduler.shutdown())


@app.before_first_request
def create_tables():
    """สร้างตารางฐานข้อมูลเมื่อเริ่มแอป"""
    db.create_all()


@app.context_processor
def inject_global_vars():
    """Inject global variables สำหรับ templates"""
    return {
        'app_name': 'TikTok Social Listening',
        'version': '1.0.0'
    }


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    from models.models import Keyword

    db.create_all()

    # เพิ่ม sample keywords
    sample_keywords = [
        {'keyword': 'อาหารไทย', 'category': 'food', 'priority': 5},
        {'keyword': 'แฟชั่น', 'category': 'fashion', 'priority': 4},
        {'keyword': 'เทคโนโลยี', 'category': 'tech', 'priority': 3},
        {'keyword': 'ท่องเที่ยว', 'category': 'travel', 'priority': 4},
        {'keyword': 'ออกกำลังกาย', 'category': 'fitness', 'priority': 3}
    ]

    for kw_data in sample_keywords:
        existing = Keyword.query.filter_by(keyword=kw_data['keyword']).first()
        if not existing:
            keyword = Keyword(**kw_data)
            db.session.add(keyword)

    db.session.commit()
    print("Database initialized with sample data!")


@app.cli.command()
def collect_data():
    """Manual command สำหรับเก็บข้อมูล"""
    collector = TikTokCollector()
    keywords = Keyword.query.filter_by(is_active=True).all()

    if not keywords:
        print("No active keywords found!")
        return

    total_collected = 0
    for keyword in keywords:
        print(f"Collecting data for: {keyword.keyword}")
        collected = collector.collect_for_keyword(keyword.keyword)
        total_collected += collected
        print(f"Collected {collected} posts")

    print(f"Total posts collected: {total_collected}")


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )