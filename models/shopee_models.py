from datetime import datetime
import json

# Import db จาก models.__init__
from models import db


class ShopeeProduct(db.Model):
    __tablename__ = 'shopee_products'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    shop_id = db.Column(db.String(50), nullable=False, index=True)

    # Product Information
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    brand = db.Column(db.String(100))

    # Pricing
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)
    discount_percentage = db.Column(db.Float, default=0)

    # Sales Metrics
    sold_count = db.Column(db.Integer, default=0)
    stock_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0)
    rating_count = db.Column(db.Integer, default=0)

    # Shop Information
    shop_name = db.Column(db.String(200))
    shop_location = db.Column(db.String(100))
    shop_rating = db.Column(db.Float, default=0)

    # Product Images and Links
    image_url = db.Column(db.Text)
    product_url = db.Column(db.Text)

    # Analytics
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)

    # Search Information
    search_keyword = db.Column(db.String(200), nullable=False, index=True)
    search_position = db.Column(db.Integer, default=0)

    # Timestamps
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ShopeeProduct {self.name[:30]}...>'

    def calculate_popularity_score(self):
        """คำนวณคะแนนความนิยม"""
        # คะแนนตาม sold_count, rating, และ review count
        sold_score = min(self.sold_count / 1000, 100)  # max 100 points
        rating_score = (self.rating / 5) * 50 if self.rating else 0  # max 50 points
        review_score = min(self.rating_count / 100, 50)  # max 50 points

        return sold_score + rating_score + review_score

    def get_revenue_estimate(self):
        """ประมาณการรายได้"""
        return self.price * self.sold_count

    def get_discount_amount(self):
        """จำนวนเงินที่ลด"""
        if self.original_price and self.original_price > self.price:
            return self.original_price - self.price
        return 0


class ShopeeKeyword(db.Model):
    __tablename__ = 'shopee_keywords'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

    # Statistics
    total_products_found = db.Column(db.Integer, default=0)
    last_scrape_time = db.Column(db.DateTime)

    # Settings
    max_pages = db.Column(db.Integer, default=5)
    price_min = db.Column(db.Float)
    price_max = db.Column(db.Float)

    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ShopeeKeyword {self.keyword}>'


class ShopeeTrend(db.Model):
    __tablename__ = 'shopee_trends'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)

    # Trend Data
    total_products = db.Column(db.Integer, default=0)
    avg_price = db.Column(db.Float, default=0)
    avg_sold = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0)

    # Top Performers
    top_product_id = db.Column(db.String(50))
    top_shop_name = db.Column(db.String(200))

    # Time Period
    date = db.Column(db.Date, nullable=False, index=True)
    period = db.Column(db.String(20), default='daily')

    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ShopeeTrend {self.keyword} on {self.date}>'


class ScrapeLog(db.Model):
    __tablename__ = 'scrape_logs'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False)

    # Scrape Results
    products_found = db.Column(db.Integer, default=0)
    products_saved = db.Column(db.Integer, default=0)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    # Timing
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)

    # Pages scraped
    pages_scraped = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<ScrapeLog {self.keyword} at {self.start_time}>'