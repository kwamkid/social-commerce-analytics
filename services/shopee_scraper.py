import requests
import time
import json
import re
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup
from models import db
from models.shopee_models import ShopeeProduct, ScrapeLog
import random


class ShopeeScraper:
    def __init__(self):
        self.base_url = "https://shopee.co.th"
        self.search_url = "https://shopee.co.th/api/v4/search/search_items"

        # Headers สำหรับหลบ detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://shopee.co.th/',
            'Origin': 'https://shopee.co.th',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Delay settings
        self.min_delay = 3
        self.max_delay = 7

    def search_products(self, keyword, page=0, limit=60):
        """ค้นหาสินค้าตาม keyword ใน Shopee"""
        try:
            # พารามิเตอร์สำหรับ API
            params = {
                'by': 'relevancy',
                'keyword': keyword,
                'limit': limit,
                'newest': page * limit,
                'order': 'desc',
                'page_type': 'search',
                'scenario': 'PAGE_GLOBAL_SEARCH',
                'version': 2,
                'view_mode': 'list'
            }

            print(f"🔍 Searching for '{keyword}' page {page + 1}")

            # เพิ่ม delay random เพื่อหลบ detection
            delay = random.uniform(self.min_delay, self.max_delay)
            print(f"⏱️  Waiting {delay:.2f} seconds...")
            time.sleep(delay)

            response = self.session.get(self.search_url, params=params, timeout=30)

            if response.status_code == 200:
                try:
                    data = response.json()

                    if 'items' in data and data['items']:
                        products = []
                        for item in data['items']:
                            if 'item_basic' in item:
                                product_data = self._parse_search_item(item['item_basic'], keyword, page)
                                if product_data:
                                    products.append(product_data)

                        print(f"✅ Found {len(products)} products")
                        return products
                    else:
                        print(f"⚠️  No items found in response")
                        return []

                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return []
            elif response.status_code == 429:
                print("⚠️  Rate limit hit, waiting longer...")
                time.sleep(60)  # Wait 1 minute
                return []
            else:
                print(f"❌ API Error: {response.status_code}")
                if response.status_code == 403:
                    print("🚫 Access denied - might need to change headers or use proxy")
                return []

        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []

    def _parse_search_item(self, item, keyword, page):
        """แปลงข้อมูลจาก search API"""
        try:
            # ข้อมูลพื้นฐาน
            product_id = str(item.get('itemid', ''))
            shop_id = str(item.get('shopid', ''))

            if not product_id or not shop_id:
                return None

            # ราคา (Shopee ใช้หน่วยเป็น 1/100000 ของบาท)
            price = item.get('price', 0) / 100000
            price_min = item.get('price_min', 0) / 100000
            price_max = item.get('price_max', 0) / 100000

            # ใช้ price_min ถ้ามี range, ไม่งั้นใช้ price
            final_price = price_min if price_min > 0 else price

            # ราคาเดิม (ก่อนลด)
            original_price = None
            price_before_discount = item.get('price_before_discount')
            if price_before_discount and price_before_discount > 0:
                original_price = price_before_discount / 100000

            # คำนวณ discount
            discount_percentage = 0
            if original_price and original_price > final_price:
                discount_percentage = ((original_price - final_price) / original_price) * 100

            # ข้อมูลการขาย
            sold_count = item.get('sold', 0)
            stock_count = item.get('stock', 0)

            # Rating
            rating = 0
            rating_count = 0
            if 'item_rating' in item and item['item_rating']:
                rating_data = item['item_rating']
                if 'rating_star' in rating_data:
                    rating = rating_data['rating_star'] / 20  # Shopee ใช้ scale 0-100, แปลงเป็น 0-5
                if 'rating_count' in rating_data and rating_data['rating_count']:
                    rating_count = rating_data['rating_count'][0] if isinstance(rating_data['rating_count'], list) else \
                    rating_data['rating_count']

            # รูปภาพ
            image_url = None
            if item.get('image'):
                image_url = f"https://cf.shopee.co.th/file/{item['image']}"

            # URL สินค้า
            product_name_slug = re.sub(r'[^a-zA-Z0-9\u0E00-\u0E7F]+', '-', item.get('name', '')).strip('-').lower()
            product_url = f"https://shopee.co.th/{product_name_slug}-i.{shop_id}.{product_id}"

            # ข้อมูลร้านค้า
            shop_name = item.get('shop_name', '')
            shop_location = item.get('shop_location', '')

            return {
                'product_id': product_id,
                'shop_id': shop_id,
                'name': item.get('name', ''),
                'price': final_price,
                'original_price': original_price,
                'discount_percentage': discount_percentage,
                'sold_count': sold_count,
                'stock_count': stock_count,
                'rating': rating,
                'rating_count': rating_count,
                'shop_name': shop_name,
                'shop_location': shop_location,
                'image_url': image_url,
                'product_url': product_url,
                'search_keyword': keyword,
                'search_position': (page * 60) + 1,  # ตำแหน่งในการค้นหา
                'view_count': item.get('view_count', 0),
                'like_count': item.get('liked_count', 0)
            }

        except Exception as e:
            print(f"❌ Error parsing search item: {e}")
            return None

    def save_products_to_db(self, products_data, keyword):
        """บันทึกข้อมูลสินค้าลงฐานข้อมูล"""
        if not products_data:
            return 0

        products_saved = 0
        products_updated = 0

        try:
            for product_data in products_data:
                # ตรวจสอบว่ามีสินค้านี้แล้วหรือไม่
                existing_product = ShopeeProduct.query.filter_by(
                    product_id=product_data['product_id']
                ).first()

                if existing_product:
                    # อัพเดทข้อมูลสินค้าที่มีอยู่
                    self._update_product(existing_product, product_data)
                    products_updated += 1
                else:
                    # สร้างสินค้าใหม่
                    new_product = ShopeeProduct(**product_data)
                    db.session.add(new_product)
                    products_saved += 1

            db.session.commit()
            print(f"💾 Saved {products_saved} new products, updated {products_updated} products for keyword '{keyword}'")
            return products_saved

        except Exception as e:
            print(f"❌ Error saving products to database: {e}")
            db.session.rollback()
            return 0

    def _update_product(self, existing_product, new_data):
        """อัพเดทข้อมูลสินค้าที่มีอยู่"""
        try:
            # อัพเดทข้อมูลที่อาจเปลี่ยนแปลง
            existing_product.price = new_data['price']
            existing_product.original_price = new_data['original_price']
            existing_product.discount_percentage = new_data['discount_percentage']
            existing_product.sold_count = new_data['sold_count']
            existing_product.stock_count = new_data['stock_count']
            existing_product.rating = new_data['rating']
            existing_product.rating_count = new_data['rating_count']
            existing_product.view_count = new_data['view_count']
            existing_product.like_count = new_data['like_count']
            existing_product.updated_time = datetime.utcnow()
            existing_product.scraped_time = datetime.utcnow()

        except Exception as e:
            print(f"❌ Error updating product: {e}")

    def scrape_keyword(self, keyword, max_pages=3):
        """Scrape ข้อมูลสำหรับ keyword หนึ่งตัว"""
        start_time = datetime.utcnow()

        # สร้าง log record
        log = ScrapeLog(
            keyword=keyword,
            start_time=start_time
        )

        total_products_found = 0
        total_products_saved = 0

        try:
            print(f"\n🚀 Starting scrape for keyword: '{keyword}'")
            print(f"📄 Max pages to scrape: {max_pages}")

            for page in range(max_pages):
                print(f"\n📖 Scraping page {page + 1}/{max_pages}")

                # ค้นหาสินค้า
                products = self.search_products(keyword, page)

                if not products:
                    print(f"⚠️  No products found on page {page + 1}, stopping")
                    break

                total_products_found += len(products)

                # บันทึกลงฐานข้อมูล
                saved = self.save_products_to_db(products, keyword)
                total_products_saved += saved

                # หน่วงเวลาระหว่างหน้า
                if page < max_pages - 1:  # ไม่ต้องรอหลังหน้าสุดท้าย
                    delay = random.uniform(self.min_delay, self.max_delay)
                    print(f"⏱️  Waiting {delay:.2f} seconds before next page...")
                    time.sleep(delay)

            log.products_found = total_products_found
            log.products_saved = total_products_saved
            log.pages_scraped = min(page + 1, max_pages)
            log.success = True

            print(f"\n✅ Scraping completed for '{keyword}'")
            print(f"📊 Found: {total_products_found} products")
            print(f"💾 Saved: {total_products_saved} new products")

        except Exception as e:
            log.success = False
            log.error_message = str(e)
            print(f"\n❌ Scraping failed for keyword '{keyword}': {e}")

        finally:
            # Complete the log
            log.end_time = datetime.utcnow()
            log.duration_seconds = int((log.end_time - log.start_time).total_seconds())

            try:
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                print(f"❌ Error saving scrape log: {e}")
                db.session.rollback()

        return total_products_saved