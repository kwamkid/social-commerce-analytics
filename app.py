from flask import Flask, render_template, request
from datetime import datetime
import os

# Import configuration
from config import config
from models import db


def create_app(config_name=None):
    """Factory function สำหรับสร้าง Flask app"""
    app = Flask(__name__)

    # Load configuration
    config_name = config_name or os.environ.get('FLASK_CONFIG', 'development')
    app.config.from_object(config[config_name])

    # Initialize database
    db.init_app(app)

    return app


# Create app instance
app = create_app()


@app.context_processor
def inject_global_vars():
    """Inject global variables สำหรับ templates"""
    return {
        'app_name': 'Social Commerce Analytics',
        'version': '2.0.0'
    }


@app.route('/')
def index():
    """Main index page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>Social Commerce Analytics</h1><p>System is running!</p><p>Template error: {e}</p>"


# TikTok routes (dummy for now)
@app.route('/main/dashboard')
def main_dashboard():
    """TikTok Dashboard"""
    try:
        return render_template('dashboard.html',
                               total_posts=0, total_keywords=0,
                               total_engagement=0, trending_posts=0,
                               trending_hashtags=[], recent_logs=[],
                               engagement_dates='[]', engagement_data='[]',
                               keyword_labels='[]', keyword_data='[]',
                               last_update='Just started')
    except Exception as e:
        return f"<h1>TikTok Dashboard</h1><p>Coming soon... Error: {e}</p>"


@app.route('/main/keywords')
def main_keywords():
    """TikTok Keywords"""
    return "<h1>TikTok Keywords</h1><p>Coming soon...</p>"


@app.route('/main/trending')
def main_trending():
    """TikTok Trending"""
    return "<h1>TikTok Trending</h1><p>Coming soon...</p>"


@app.route('/main/content_ideas')
def main_content_ideas():
    """TikTok Content Ideas"""
    return "<h1>TikTok Content Ideas</h1><p>Coming soon...</p>"


@app.route('/tiktok')
def tiktok_dashboard():
    """TikTok Dashboard"""
    return main_dashboard()


# Shopee routes
@app.route('/shopee')
def shopee_dashboard():
    """Shopee Dashboard"""
    try:
        from models.shopee_models import ShopeeProduct, ShopeeKeyword

        # ดึงข้อมูลจริงจาก database แบบ safe
        try:
            total_products = ShopeeProduct.query.count()
            total_keywords = ShopeeKeyword.query.filter_by(is_active=True).count()
        except Exception as e:
            print(f"Basic count error: {e}")
            total_products = 0
            total_keywords = 0

        # คำนวณยอดขายและรายได้รวม
        try:
            total_sales = db.session.query(db.func.sum(ShopeeProduct.sold_count)).scalar() or 0
            total_revenue = db.session.query(
                db.func.sum(ShopeeProduct.price * ShopeeProduct.sold_count)
            ).scalar() or 0
        except Exception as e:
            print(f"Sales calculation error: {e}")
            total_sales = 0
            total_revenue = 0

        # สินค้าขายดี (ขายมากกว่า 50 ชิ้น)
        try:
            bestsellers_count = ShopeeProduct.query.filter(ShopeeProduct.sold_count >= 50).count()
        except Exception as e:
            print(f"Bestsellers count error: {e}")
            bestsellers_count = 0

        # Top products
        try:
            top_products = ShopeeProduct.query.order_by(
                ShopeeProduct.sold_count.desc()
            ).limit(5).all()
        except Exception as e:
            print(f"Top products error: {e}")
            top_products = []

        # Keyword stats - แก้ไขให้ปลอดภัย
        try:
            keyword_stats = db.session.query(
                ShopeeProduct.search_keyword,
                db.func.count(ShopeeProduct.id).label('product_count'),
                db.func.sum(ShopeeProduct.sold_count).label('total_sales'),
                db.func.avg(ShopeeProduct.price).label('avg_price')
            ).group_by(ShopeeProduct.search_keyword).order_by(
                db.func.sum(ShopeeProduct.sold_count).desc()
            ).limit(10).all()
        except Exception as e:
            print(f"Keyword stats error: {e}")
            keyword_stats = []

        # Recent scrape logs
        try:
            from models.shopee_models import ScrapeLog
            recent_logs = ScrapeLog.query.order_by(
                ScrapeLog.start_time.desc()
            ).limit(10).all()
        except Exception as e:
            print(f"Recent logs error: {e}")
            recent_logs = []

        # Price ranges - แก้ไข syntax
        try:
            price_ranges = []
            price_under_100 = ShopeeProduct.query.filter(ShopeeProduct.price < 100).count()
            price_100_500 = ShopeeProduct.query.filter(
                ShopeeProduct.price >= 100, ShopeeProduct.price < 500
            ).count()
            price_500_1000 = ShopeeProduct.query.filter(
                ShopeeProduct.price >= 500, ShopeeProduct.price < 1000
            ).count()
            price_1000_5000 = ShopeeProduct.query.filter(
                ShopeeProduct.price >= 1000, ShopeeProduct.price < 5000
            ).count()
            price_over_5000 = ShopeeProduct.query.filter(ShopeeProduct.price >= 5000).count()

            price_ranges = [
                ('ต่ำกว่า 100 บาท', price_under_100),
                ('100-500 บาท', price_100_500),
                ('500-1,000 บาท', price_500_1000),
                ('1,000-5,000 บาท', price_1000_5000),
                ('มากกว่า 5,000 บาท', price_over_5000)
            ]
        except Exception as e:
            print(f"Price range error: {e}")
            price_ranges = []

        return render_template('shopee/dashboard.html',
                               total_products=total_products,
                               total_keywords=total_keywords,
                               total_sales=total_sales,
                               total_revenue=total_revenue,
                               bestsellers=bestsellers_count,
                               top_products=top_products,
                               keyword_stats=keyword_stats,
                               recent_logs=recent_logs,
                               price_ranges=price_ranges,
                               last_update=datetime.now().strftime('%d/%m/%Y %H:%M'))
    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Shopee Dashboard</h1><p>Error: {e}</p>"


@app.route('/shopee/bestsellers')
def shopee_bestsellers():
    """Shopee Bestsellers - ใช้ข้อมูลจริง"""
    try:
        from models.shopee_models import ShopeeProduct

        # ดึงสินค้าขายดีจากฐานข้อมูล
        bestsellers = ShopeeProduct.query.filter(
            ShopeeProduct.sold_count >= 10  # ขายอย่างน้อย 10 ชิ้น
        ).order_by(ShopeeProduct.sold_count.desc()).limit(50).all()

        if not bestsellers:
            # หากไม่มีข้อมูล ให้แสดงหน้า no_data
            return render_template('shopee/no_data.html',
                                   message="ยังไม่มีข้อมูลสินค้า",
                                   suggestion="เพิ่ม Keywords และทำการ Scrape ข้อมูลก่อน")

        # คำนวณสถิติ
        total_bestsellers = len(bestsellers)
        total_revenue = sum(p.price * p.sold_count for p in bestsellers)
        avg_price = sum(p.price for p in bestsellers) / len(bestsellers) if bestsellers else 0
        avg_sold = sum(p.sold_count for p in bestsellers) / len(bestsellers) if bestsellers else 0

        return render_template('shopee/bestsellers.html',
                               bestsellers=bestsellers,
                               total_bestsellers=total_bestsellers,
                               total_revenue=total_revenue,
                               avg_price=avg_price,
                               avg_sold=avg_sold)
    except Exception as e:
        print(f"Bestsellers error: {e}")
        return f"<h1>Shopee Bestsellers</h1><p>Error: {e}</p>"


@app.route('/shopee/keywords')
def shopee_keywords():
    """Shopee Keywords Management"""
    try:
        from models.shopee_models import ShopeeKeyword

        page = request.args.get('page', 1, type=int)
        per_page = 20

        keywords = ShopeeKeyword.query.order_by(
            ShopeeKeyword.created_time.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return render_template('shopee/keywords.html', keywords=keywords)
    except Exception as e:
        return f"<h1>Shopee Keywords</h1><p>Error: {e}</p>"


@app.route('/shopee/keywords/add', methods=['POST'])
def shopee_add_keyword():
    """เพิ่ม Keyword ใหม่สำหรับ Shopee"""
    try:
        from models.shopee_models import ShopeeKeyword

        keyword_text = request.form.get('keyword', '').strip()
        category = request.form.get('category', '').strip()
        max_pages = request.form.get('max_pages', 3, type=int)
        price_min = request.form.get('price_min', type=float)
        price_max = request.form.get('price_max', type=float)

        if not keyword_text:
            return "กรุณาใส่ keyword", 400

        # ตรวจสอบว่ามี keyword นี้แล้วหรือไม่
        existing = ShopeeKeyword.query.filter_by(keyword=keyword_text).first()
        if existing:
            return f'Keyword "{keyword_text}" มีอยู่แล้ว', 400

        # สร้าง keyword ใหม่
        new_keyword = ShopeeKeyword(
            keyword=keyword_text,
            category=category if category else None,
            max_pages=max_pages,
            price_min=price_min,
            price_max=price_max
        )

        db.session.add(new_keyword)
        db.session.commit()

        return f'เพิ่ม keyword "{keyword_text}" สำเร็จ!', 200

    except Exception as e:
        db.session.rollback()
        return f'เกิดข้อผิดพลาด: {str(e)}', 500


@app.route('/shopee/scrape/<int:keyword_id>', methods=['POST'])
def shopee_scrape_keyword(keyword_id):
    """Scrape ข้อมูลสำหรับ keyword เฉพาะ"""
    try:
        from models.shopee_models import ShopeeKeyword
        from services.shopee_scraper import ShopeeScraper

        keyword = ShopeeKeyword.query.get_or_404(keyword_id)

        scraper = ShopeeScraper()
        products_saved = scraper.scrape_keyword(keyword.keyword, keyword.max_pages)

        # อัพเดท keyword statistics
        keyword.total_products_found += products_saved
        keyword.last_scrape_time = datetime.utcnow()
        db.session.commit()

        return f'Scrape สำเร็จ! พบสินค้าใหม่ {products_saved} รายการ', 200

    except Exception as e:
        db.session.rollback()
        return f'เกิดข้อผิดพลาด: {str(e)}', 500


@app.route('/shopee/scrape-all', methods=['POST'])
def shopee_scrape_all():
    """Scrape ข้อมูลทุก keywords"""
    try:
        from models.shopee_models import ShopeeKeyword
        from services.shopee_scraper import ShopeeScraper

        keywords = ShopeeKeyword.query.filter_by(is_active=True).all()

        if not keywords:
            return 'ไม่มี active keywords', 400

        scraper = ShopeeScraper()
        total_products = 0

        for keyword in keywords:
            print(f"🔄 Scraping keyword: {keyword.keyword}")
            products_saved = scraper.scrape_keyword(keyword.keyword, keyword.max_pages)
            total_products += products_saved

            # อัพเดท keyword stats
            keyword.total_products_found += products_saved
            keyword.last_scrape_time = datetime.utcnow()

        db.session.commit()

        return f'Scrape สำเร็จ! รวม {total_products} สินค้าใหม่', 200

    except Exception as e:
        db.session.rollback()
        return f'เกิดข้อผิดพลาด: {str(e)}', 500


@app.route('/shopee/products')
def shopee_products():
    """Shopee Products"""
    return "<h1>Shopee Products</h1><p>Coming soon...</p>"


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return "Page not found", 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return "Internal server error", 500


@app.cli.command()
def init_db():
    """Initialize database with sample data"""
    print("Creating database tables...")

    # สร้างตารางทั้งหมด
    with app.app_context():
        db.create_all()
        print("Tables created successfully!")

        # Import models after app context is created
        from models.models import Keyword
        from models.shopee_models import ShopeeKeyword

        # เพิ่ม sample TikTok keywords
        tiktok_keywords = [
            {'keyword': 'อาหารไทย', 'category': 'food', 'priority': 5},
            {'keyword': 'แฟชั่น', 'category': 'fashion', 'priority': 4},
            {'keyword': 'เทคโนโลยี', 'category': 'tech', 'priority': 3},
        ]

        for kw_data in tiktok_keywords:
            existing = Keyword.query.filter_by(keyword=kw_data['keyword']).first()
            if not existing:
                keyword = Keyword(**kw_data)
                db.session.add(keyword)
                print(f"Added TikTok keyword: {kw_data['keyword']}")

        # เพิ่ม sample Shopee keywords
        shopee_keywords = [
            {'keyword': 'iPhone', 'category': 'electronics', 'max_pages': 3},
            {'keyword': 'เสื้อผ้า', 'category': 'fashion', 'max_pages': 3},
            {'keyword': 'หูฟัง', 'category': 'electronics', 'max_pages': 3},
            {'keyword': 'กระเป๋า', 'category': 'fashion', 'max_pages': 3},
        ]

        for kw_data in shopee_keywords:
            existing = ShopeeKeyword.query.filter_by(keyword=kw_data['keyword']).first()
            if not existing:
                keyword = ShopeeKeyword(**kw_data)
                db.session.add(keyword)
                print(f"Added Shopee keyword: {kw_data['keyword']}")

        try:
            db.session.commit()
            print("Database initialized with sample data!")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving sample data: {e}")


@app.cli.command()
def test_db():
    """Test database connection"""
    try:
        with app.app_context():
            # ทดสอบการเชื่อมต่อ
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                print("✅ Database connection successful!")

            # ดูตารางที่มี
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables in database: {tables}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("🔍 Checking connection details...")
        print(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")


@app.cli.command()
def scrape_shopee():
    """Manual command สำหรับ scrape ข้อมูล Shopee"""
    from models.shopee_models import ShopeeKeyword
    from services.shopee_scraper import ShopeeScraper

    scraper = ShopeeScraper()
    keywords = ShopeeKeyword.query.filter_by(is_active=True).all()

    if not keywords:
        print("No active Shopee keywords found!")
        return

    total_scraped = 0
    for keyword in keywords:
        print(f"Scraping Shopee data for: {keyword.keyword}")
        scraped = scraper.scrape_keyword(keyword.keyword, keyword.max_pages)
        total_scraped += scraped
        print(f"Scraped {scraped} products")

    print(f"Total Shopee products scraped: {total_scraped}")


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=True
    )