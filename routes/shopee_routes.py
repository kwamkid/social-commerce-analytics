from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json

from models.shopee_models import db, ShopeeProduct, ShopeeKeyword, ShopeeTrend, ScrapeLog
from services.shopee_scraper import ShopeeScraper

shopee_bp = Blueprint('shopee', __name__, url_prefix='/shopee')


@shopee_bp.route('/')
def dashboard():
    """หน้า Dashboard สำหรับ Shopee Analytics"""
    try:
        # ข้อมูลสถิติพื้นฐาน
        total_products = ShopeeProduct.query.count()
        total_keywords = ShopeeKeyword.query.filter_by(is_active=True).count()

        # ยอดขายรวม
        total_sales = db.session.query(
            func.sum(ShopeeProduct.sold_count)
        ).scalar() or 0

        # มูลค่าการขายโดยประมาณ
        total_revenue = db.session.query(
            func.sum(ShopeeProduct.price * ShopeeProduct.sold_count)
        ).scalar() or 0

        # สินค้าขายดี (ขายมากกว่า 100 ชิ้น)
        bestsellers = ShopeeProduct.query.filter(
            ShopeeProduct.sold_count >= 100
        ).count()

        # Top selling products (7 วันล่าสุด)
        since_date = datetime.utcnow() - timedelta(days=7)
        top_products = ShopeeProduct.query.filter(
            ShopeeProduct.scraped_time >= since_date
        ).order_by(
            desc(ShopeeProduct.sold_count)
        ).limit(10).all()

        # Keywords performance
        keyword_stats = db.session.query(
            ShopeeProduct.search_keyword,
            func.count(ShopeeProduct.id).label('product_count'),
            func.sum(ShopeeProduct.sold_count).label('total_sales'),
            func.avg(ShopeeProduct.price).label('avg_price')
        ).group_by(ShopeeProduct.search_keyword).order_by(desc('total_sales')).limit(10).all()

        # Recent scrape logs
        recent_logs = ScrapeLog.query.order_by(
            desc(ScrapeLog.start_time)
        ).limit(10).all()

        # Price range analysis
        price_ranges = db.session.query(
            func.case([
                (ShopeeProduct.price < 100, 'ต่ำกว่า 100 บาท'),
                (ShopeeProduct.price < 500, '100-500 บาท'),
                (ShopeeProduct.price < 1000, '500-1,000 บาท'),
                (ShopeeProduct.price < 5000, '1,000-5,000 บาท'),
            ], else_='มากกว่า 5,000 บาท').label('price_range'),
            func.count(ShopeeProduct.id).label('count')
        ).group_by('price_range').all()

        return render_template('shopee/dashboard.html',
                               total_products=total_products,
                               total_keywords=total_keywords,
                               total_sales=total_sales,
                               total_revenue=total_revenue,
                               bestsellers=bestsellers,
                               top_products=top_products,
                               keyword_stats=keyword_stats,
                               recent_logs=recent_logs,
                               price_ranges=price_ranges,
                               last_update=datetime.now().strftime('%d/%m/%Y %H:%M'))

    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}', 'error')
        return render_template('shopee/dashboard.html',
                               total_products=0, total_keywords=0,
                               total_sales=0, total_revenue=0, bestsellers=0,
                               top_products=[], keyword_stats=[], recent_logs=[])


@shopee_bp.route('/keywords')
def keywords():
    """หน้าจัดการ Keywords สำหรับ Shopee"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    keywords = ShopeeKeyword.query.order_by(desc(ShopeeKeyword.created_time)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('shopee/keywords.html', keywords=keywords)


@shopee_bp.route('/keywords/add', methods=['POST'])
def add_keyword():
    """เพิ่ม Keyword ใหม่สำหรับ Shopee"""
    try:
        keyword_text = request.form.get('keyword', '').strip()
        category = request.form.get('category', '').strip()
        max_pages = request.form.get('max_pages', 5, type=int)
        price_min = request.form.get('price_min', type=float)
        price_max = request.form.get('price_max', type=float)

        if not keyword_text:
            flash('กรุณาใส่ keyword', 'error')
            return redirect(url_for('shopee.keywords'))

        # ตรวจสอบว่ามี keyword นี้แล้วหรือไม่
        existing = ShopeeKeyword.query.filter_by(keyword=keyword_text).first()
        if existing:
            flash(f'Keyword "{keyword_text}" มีอยู่แล้ว', 'warning')
            return redirect(url_for('shopee.keywords'))

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

        flash(f'เพิ่ม keyword "{keyword_text}" สำเร็จ', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('shopee.keywords'))


@shopee_bp.route('/keywords/<int:keyword_id>/scrape', methods=['POST'])
def scrape_keyword(keyword_id):
    """Scrape ข้อมูลสำหรับ keyword เฉพาะ"""
    try:
        keyword = ShopeeKeyword.query.get_or_404(keyword_id)

        scraper = ShopeeScraper()
        products_saved = scraper.scrape_keyword(keyword.keyword, keyword.max_pages)

        # อัพเดท keyword statistics
        keyword.total_products_found += products_saved
        keyword.last_scrape_time = datetime.utcnow()
        db.session.commit()

        flash(f'Scrape สำเร็จ! พบสินค้าใหม่ {products_saved} รายการ', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('shopee.keywords'))


@shopee_bp.route('/products')
def products():
    """หน้าแสดงสินค้าทั้งหมด"""
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')
    sort_by = request.args.get('sort', 'sold_count')  # sold_count, price, rating
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    page = request.args.get('page', 1, type=int)
    per_page = 24

    # Base query
    query = ShopeeProduct.query

    # Filters
    if keyword:
        query = query.filter(ShopeeProduct.search_keyword.contains(keyword))

    if category:
        query = query.filter(ShopeeProduct.category == category)

    if min_price:
        query = query.filter(ShopeeProduct.price >= min_price)

    if max_price:
        query = query.filter(ShopeeProduct.price <= max_price)

    # Sorting
    if sort_by == 'price_low':
        query = query.order_by(ShopeeProduct.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(ShopeeProduct.price.desc())
    elif sort_by == 'rating':
        query = query.order_by(ShopeeProduct.rating.desc())
    elif sort_by == 'newest':
        query = query.order_by(ShopeeProduct.scraped_time.desc())
    else:  # sold_count (default)
        query = query.order_by(ShopeeProduct.sold_count.desc())

    # Pagination
    products = query.paginate(page=page, per_page=per_page, error_out=False)

    # Available keywords and categories for filters
    available_keywords = db.session.query(ShopeeProduct.search_keyword.distinct()).all()
    available_categories = db.session.query(ShopeeProduct.category.distinct()).filter(
        ShopeeProduct.category.isnot(None)
    ).all()

    return render_template('shopee/products.html',
                           products=products,
                           available_keywords=[k[0] for k in available_keywords],
                           available_categories=[c[0] for c in available_categories],
                           current_keyword=keyword,
                           current_category=category,
                           current_sort=sort_by,
                           min_price=min_price,
                           max_price=max_price)


@shopee_bp.route('/products/<product_id>')
def product_detail(product_id):
    """แสดงรายละเอียดสินค้า"""
    product = ShopeeProduct.query.filter_by(product_id=product_id).first_or_404()

    # หาสินค้าที่คล้ายกัน (keyword เดียวกัน, ราคาใกล้เคียง)
    price_range = product.price * 0.3  # +/- 30% ของราคา
    similar_products = ShopeeProduct.query.filter(
        ShopeeProduct.search_keyword == product.search_keyword,
        ShopeeProduct.product_id != product.product_id,
        ShopeeProduct.price.between(
            product.price - price_range,
            product.price + price_range
        )
    ).order_by(ShopeeProduct.sold_count.desc()).limit(8).all()

    # หาร้านค้าอื่นๆ ของ shop เดียวกัน
    other_products_from_shop = ShopeeProduct.query.filter(
        ShopeeProduct.shop_id == product.shop_id,
        ShopeeProduct.product_id != product.product_id
    ).order_by(ShopeeProduct.sold_count.desc()).limit(6).all()

    return render_template('shopee/product_detail.html',
                           product=product,
                           similar_products=similar_products,
                           other_products_from_shop=other_products_from_shop)


@shopee_bp.route('/bestsellers')
def bestsellers():
    """หน้าสินค้าขายดี"""
    keyword = request.args.get('keyword', '')
    days = request.args.get('days', 7, type=int)
    min_sold = request.args.get('min_sold', 50, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query สำหรับสินค้าขายดี
    query = ShopeeProduct.query.filter(ShopeeProduct.sold_count >= min_sold)

    # Filter by keyword
    if keyword:
        query = query.filter(ShopeeProduct.search_keyword == keyword)

    # Filter by date
    if days > 0:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ShopeeProduct.scraped_time >= since_date)

    # Order by sold count
    query = query.order_by(ShopeeProduct.sold_count.desc())

    # Pagination
    products = query.paginate(page=page, per_page=per_page, error_out=False)

    # Stats for bestsellers
    total_bestsellers = query.count()
    total_revenue = query.with_entities(
        func.sum(ShopeeProduct.price * ShopeeProduct.sold_count)
    ).scalar() or 0

    avg_price = query.with_entities(
        func.avg(ShopeeProduct.price)
    ).scalar() or 0

    # Available keywords
    available_keywords = db.session.query(ShopeeProduct.search_keyword.distinct()).all()

    return render_template('shopee/bestsellers.html',
                           products=products,
                           available_keywords=[k[0] for k in available_keywords],
                           current_keyword=keyword,
                           current_days=days,
                           current_min_sold=min_sold,
                           total_bestsellers=total_bestsellers,
                           total_revenue=total_revenue,
                           avg_price=avg_price)


@shopee_bp.route('/analytics/<keyword>')
def keyword_analytics(keyword):
    """แสดง Analytics สำหรับ keyword เฉพาะ"""
    try:
        # ข้อมูลพื้นฐาน
        products = ShopeeProduct.query.filter_by(search_keyword=keyword).all()

        if not products:
            flash(f'ไม่พบข้อมูลสำหรับ keyword "{keyword}"', 'warning')
            return redirect(url_for('shopee.keywords'))

        # สถิติพื้นฐาน
        total_products = len(products)
        total_sales = sum(p.sold_count for p in products)
        total_revenue = sum(p.price * p.sold_count for p in products)
        avg_price = sum(p.price for p in products) / total_products
        avg_rating = sum(p.rating for p in products if p.rating > 0) / len(
            [p for p in products if p.rating > 0]) if any(p.rating > 0 for p in products) else 0

        # Top performers
        top_sellers = sorted(products, key=lambda x: x.sold_count, reverse=True)[:10]
        top_rated = sorted([p for p in products if p.rating > 0], key=lambda x: x.rating, reverse=True)[:10]

        # Price distribution
        price_ranges = {
            'ต่ำกว่า 100': len([p for p in products if p.price < 100]),
            '100-500': len([p for p in products if 100 <= p.price < 500]),
            '500-1000': len([p for p in products if 500 <= p.price < 1000]),
            '1000-5000': len([p for p in products if 1000 <= p.price < 5000]),
            'มากกว่า 5000': len([p for p in products if p.price >= 5000])
        }

        # Shop distribution
        shop_stats = {}
        for product in products:
            shop_name = product.shop_name or 'Unknown'
            if shop_name not in shop_stats:
                shop_stats[shop_name] = {
                    'product_count': 0,
                    'total_sales': 0,
                    'total_revenue': 0
                }
            shop_stats[shop_name]['product_count'] += 1
            shop_stats[shop_name]['total_sales'] += product.sold_count
            shop_stats[shop_name]['total_revenue'] += product.price * product.sold_count

        top_shops = sorted(shop_stats.items(), key=lambda x: x[1]['total_sales'], reverse=True)[:10]

        # Time series data (if available)
        daily_stats = db.session.query(
            func.date(ShopeeProduct.scraped_time).label('date'),
            func.count(ShopeeProduct.id).label('products_found'),
            func.sum(ShopeeProduct.sold_count).label('total_sales'),
            func.avg(ShopeeProduct.price).label('avg_price')
        ).filter(
            ShopeeProduct.search_keyword == keyword
        ).group_by(
            func.date(ShopeeProduct.scraped_time)
        ).order_by('date').all()

        return render_template('shopee/keyword_analytics.html',
                               keyword=keyword,
                               total_products=total_products,
                               total_sales=total_sales,
                               total_revenue=total_revenue,
                               avg_price=avg_price,
                               avg_rating=avg_rating,
                               top_sellers=top_sellers,
                               top_rated=top_rated,
                               price_ranges=price_ranges,
                               top_shops=top_shops,
                               daily_stats=daily_stats)

    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return redirect(url_for('shopee.keywords'))


@shopee_bp.route('/export/<format>')
def export_data(format):
    """Export ข้อมูลในรูปแบบต่างๆ"""
    if format not in ['csv', 'json', 'excel']:
        flash('รูปแบบไฟล์ไม่ถูกต้อง', 'error')
        return redirect(url_for('shopee.dashboard'))

    try:
        from services.shopee_analytics import ShopeeAnalyticsService
        analytics = ShopeeAnalyticsService()

        if format == 'csv':
            return analytics.export_to_csv()
        elif format == 'json':
            return analytics.export_to_json()
        elif format == 'excel':
            return analytics.export_to_excel()

    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการ export: {str(e)}', 'error')
        return redirect(url_for('shopee.dashboard'))


# API Routes
@shopee_bp.route('/api/scrape-all', methods=['POST'])
def api_scrape_all():
    """API สำหรับ scrape ข้อมูลทุก keywords"""
    try:
        keywords = ShopeeKeyword.query.filter_by(is_active=True).all()

        if not keywords:
            return jsonify({'success': False, 'message': 'ไม่มี active keywords'})

        scraper = ShopeeScraper()
        total_products = 0

        for keyword in keywords:
            products_saved = scraper.scrape_keyword(keyword.keyword, keyword.max_pages)
            total_products += products_saved

            # อัพเดท keyword stats
            keyword.total_products_found += products_saved
            keyword.last_scrape_time = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Scrape สำเร็จ! รวม {total_products} สินค้า',
            'products_found': total_products
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@shopee_bp.route('/api/keyword-stats/<keyword>')
def api_keyword_stats(keyword):
    """API สำหรับดึงสถิติ keyword"""
    try:
        products = ShopeeProduct.query.filter_by(search_keyword=keyword).all()

        if not products:
            return jsonify({'error': 'ไม่พบข้อมูล'})

        stats = {
            'total_products': len(products),
            'total_sales': sum(p.sold_count for p in products),
            'total_revenue': sum(p.price * p.sold_count for p in products),
            'avg_price': sum(p.price for p in products) / len(products),
            'avg_rating': sum(p.rating for p in products if p.rating > 0) / len(
                [p for p in products if p.rating > 0]) if any(p.rating > 0 for p in products) else 0,
            'bestseller': max(products, key=lambda x: x.sold_count).name if products else None
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)})