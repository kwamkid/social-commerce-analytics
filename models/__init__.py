from flask_sqlalchemy import SQLAlchemy

# สร้าง instance เดียวของ SQLAlchemy
db = SQLAlchemy()

# Import models หลังจากสร้าง db แล้ว
from .models import TikTokPost, Keyword, HashtagTrend, ContentIdea, CollectionLog
from .shopee_models import ShopeeProduct, ShopeeKeyword, ShopeeTrend, ScrapeLog

__all__ = [
    'db',
    'TikTokPost', 'Keyword', 'HashtagTrend', 'ContentIdea', 'CollectionLog',
    'ShopeeProduct', 'ShopeeKeyword', 'ShopeeTrend', 'ScrapeLog'
]