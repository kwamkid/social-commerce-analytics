from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class TikTokPost(db.Model):
    __tablename__ = 'tiktok_posts'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    display_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    video_duration = db.Column(db.Integer, default=0)  # in seconds

    # Engagement Metrics
    view_count = db.Column(db.BigInteger, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)

    # Content Analysis
    hashtags = db.Column(db.Text)  # JSON string of hashtags
    mentions = db.Column(db.Text)  # JSON string of mentions
    music_title = db.Column(db.String(200))
    music_author = db.Column(db.String(100))

    # Timestamps
    created_time = db.Column(db.DateTime, nullable=False)
    scraped_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    keyword = db.Column(db.String(100), nullable=False, index=True)
    language = db.Column(db.String(10), default='th')
    region = db.Column(db.String(10), default='TH')

    # Analytics
    engagement_rate = db.Column(db.Float, default=0.0)
    viral_score = db.Column(db.Float, default=0.0)  # Custom calculated score

    def __repr__(self):
        return f'<TikTokPost {self.video_id} by @{self.username}>'

    def get_hashtags(self):
        """Get hashtags as list"""
        if self.hashtags:
            return json.loads(self.hashtags)
        return []

    def set_hashtags(self, hashtag_list):
        """Set hashtags from list"""
        self.hashtags = json.dumps(hashtag_list)

    def get_mentions(self):
        """Get mentions as list"""
        if self.mentions:
            return json.loads(self.mentions)
        return []

    def set_mentions(self, mention_list):
        """Set mentions from list"""
        self.mentions = json.dumps(mention_list)

    def calculate_engagement_rate(self):
        """Calculate engagement rate (likes + comments + shares) / views * 100"""
        if self.view_count > 0:
            total_engagement = self.like_count + self.comment_count + self.share_count
            self.engagement_rate = (total_engagement / self.view_count) * 100
        else:
            self.engagement_rate = 0.0
        return self.engagement_rate

    def calculate_viral_score(self):
        """Calculate viral score based on engagement and growth"""
        # Simple viral score calculation
        # You can make this more sophisticated
        base_score = self.like_count * 1.0 + self.comment_count * 2.0 + self.share_count * 3.0
        if self.view_count > 0:
            self.viral_score = (base_score / self.view_count) * 100
        else:
            self.viral_score = 0.0
        return self.viral_score


class Keyword(db.Model):
    __tablename__ = 'keywords'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    category = db.Column(db.String(50))  # e.g., 'fashion', 'food', 'tech'
    priority = db.Column(db.Integer, default=1)  # 1=low, 5=high
    description = db.Column(db.Text)

    # Statistics
    total_posts_found = db.Column(db.Integer, default=0)
    last_collection_time = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Keyword {self.keyword}>'


class HashtagTrend(db.Model):
    __tablename__ = 'hashtag_trends'

    id = db.Column(db.Integer, primary_key=True)
    hashtag = db.Column(db.String(100), nullable=False, index=True)

    # Trend Data
    usage_count = db.Column(db.Integer, default=0)
    total_likes = db.Column(db.BigInteger, default=0)
    total_views = db.Column(db.BigInteger, default=0)
    avg_engagement = db.Column(db.Float, default=0.0)

    # Time Period
    date = db.Column(db.Date, nullable=False, index=True)
    period = db.Column(db.String(20), default='daily')  # daily, weekly, monthly

    # Trend Analysis
    growth_rate = db.Column(db.Float, default=0.0)  # compared to previous period
    trend_score = db.Column(db.Float, default=0.0)

    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HashtagTrend #{self.hashtag} on {self.date}>'


class ContentIdea(db.Model):
    __tablename__ = 'content_ideas'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Based on Analysis
    based_on_hashtags = db.Column(db.Text)  # JSON string
    based_on_posts = db.Column(db.Text)  # JSON string of post IDs

    # Performance Prediction
    predicted_engagement = db.Column(db.Float, default=0.0)
    confidence_score = db.Column(db.Float, default=0.0)

    # Category and Tags
    category = db.Column(db.String(50))
    tags = db.Column(db.Text)  # JSON string

    # Status
    is_used = db.Column(db.Boolean, default=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContentIdea {self.title}>'

    def get_hashtags(self):
        if self.based_on_hashtags:
            return json.loads(self.based_on_hashtags)
        return []

    def get_tags(self):
        if self.tags:
            return json.loads(self.tags)
        return []


class CollectionLog(db.Model):
    __tablename__ = 'collection_logs'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)

    # Collection Results
    posts_collected = db.Column(db.Integer, default=0)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    # Timing
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)

    # API Usage
    api_requests_made = db.Column(db.Integer, default=0)
    api_rate_limit_hit = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<CollectionLog {self.keyword} at {self.start_time}>'