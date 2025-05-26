import requests
import json
import time
from datetime import datetime, timedelta
# เป็น
from models import db
from models.models import TikTokPost, CollectionLog
from config import Config


class TikTokCollector:
    def __init__(self):
        self.access_token = Config.TIKTOK_ACCESS_TOKEN
        self.client_key = Config.TIKTOK_CLIENT_KEY
        self.client_secret = Config.TIKTOK_CLIENT_SECRET
        self.base_url = "https://open.tiktokapis.com/v2/research"
        self.rate_limit_delay = 1  # seconds between requests

    def get_headers(self):
        """Get API headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'TikTok-Social-Listening/1.0'
        }

    def search_videos(self, keyword, max_count=100, days_back=30):
        """
        ค้นหาวิดีโอตาม keyword ใน TikTok Research API
        """
        # คำนวณวันที่สำหรับการค้นหา
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        headers = self.get_headers()

        # TikTok Research API payload
        payload = {
            "query": {
                "and": [
                    {
                        "operation": "IN",
                        "field_name": "keyword",
                        "field_values": [keyword]
                    }
                ]
            },
            "max_count": min(max_count, 1000),  # TikTok API limit
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "fields": [
                "id",
                "video_description",
                "create_time",
                "region_code",
                "language_code",
                "username",
                "display_name",
                "view_count",
                "like_count",
                "comment_count",
                "share_count",
                "hashtag_names",
                "music_title",
                "music_author",
                "video_duration"
            ]
        }

        try:
            print(f"Searching TikTok for keyword: {keyword}")
            response = requests.post(
                f"{self.base_url}/video/query/",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"Found {len(data.get('data', {}).get('videos', []))} videos for '{keyword}'")
                return data
            elif response.status_code == 429:
                print("Rate limit hit, waiting...")
                time.sleep(60)  # Wait 1 minute
                return None
            else:
                print(f"API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def save_posts_to_db(self, posts_data, keyword):
        """
        บันทึกข้อมูล posts ลงฐานข้อมูล MySQL
        """
        if not posts_data or 'data' not in posts_data:
            return 0

        posts_saved = 0

        try:
            for post_data in posts_data['data']['videos']:
                # ตรวจสอบว่ามีข้อมูลนี้แล้วหรือไม่
                existing_post = TikTokPost.query.filter_by(video_id=post_data['id']).first()

                if existing_post:
                    # อัพเดทข้อมูล engagement หากมีการเปลี่ยนแปลง
                    self._update_post_metrics(existing_post, post_data)
                    continue

                # สร้าง post ใหม่
                new_post = self._create_post_from_data(post_data, keyword)

                if new_post:
                    db.session.add(new_post)
                    posts_saved += 1

            db.session.commit()
            print(f"Saved {posts_saved} new posts for keyword '{keyword}'")
            return posts_saved

        except Exception as e:
            print(f"Error saving posts to database: {e}")
            db.session.rollback()
            return 0

    def _create_post_from_data(self, post_data, keyword):
        """สร้าง TikTokPost object จากข้อมูล API"""
        try:
            # แปลงเวลา
            create_time_str = post_data.get('create_time', '')
            if create_time_str:
                create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
            else:
                create_time = datetime.utcnow()

            # สร้าง post object
            post = TikTokPost(
                video_id=post_data['id'],
                username=post_data.get('username', ''),
                display_name=post_data.get('display_name', ''),
                description=post_data.get('video_description', ''),
                video_duration=post_data.get('video_duration', 0),

                # Metrics
                view_count=post_data.get('view_count', 0),
                like_count=post_data.get('like_count', 0),
                comment_count=post_data.get('comment_count', 0),
                share_count=post_data.get('share_count', 0),

                # Content info
                music_title=post_data.get('music_title', ''),
                music_author=post_data.get('music_author', ''),

                # Metadata
                created_time=create_time,
                keyword=keyword,
                language=post_data.get('language_code', 'th'),
                region=post_data.get('region_code', 'TH')
            )

            # ตั้งค่า hashtags
            hashtags = post_data.get('hashtag_names', [])
            if hashtags:
                post.set_hashtags(hashtags)

            # คำนวณ metrics
            post.calculate_engagement_rate()
            post.calculate_viral_score()

            return post

        except Exception as e:
            print(f"Error creating post object: {e}")
            return None

    def _update_post_metrics(self, existing_post, new_data):
        """อัพเดท metrics ของ post ที่มีอยู่แล้ว"""
        try:
            # อัพเดทตัวเลข engagement
            existing_post.view_count = new_data.get('view_count', existing_post.view_count)
            existing_post.like_count = new_data.get('like_count', existing_post.like_count)
            existing_post.comment_count = new_data.get('comment_count', existing_post.comment_count)
            existing_post.share_count = new_data.get('share_count', existing_post.share_count)

            # คำนวณ metrics ใหม่
            existing_post.calculate_engagement_rate()
            existing_post.calculate_viral_score()

            # อัพเดทเวลา
            existing_post.updated_time = datetime.utcnow()

        except Exception as e:
            print(f"Error updating post metrics: {e}")

    def collect_for_keyword(self, keyword, max_posts=100):
        """
        เก็บข้อมูลสำหรับ keyword หนึ่งตัว และบันทึก log
        """
        start_time = datetime.utcnow()

        # สร้าง log record
        log = CollectionLog(
            keyword=keyword,
            start_time=start_time,
            api_requests_made=0
        )

        try:
            # ค้นหาข้อมูล
            posts_data = self.search_videos(keyword, max_posts)
            log.api_requests_made += 1

            if posts_data:
                # บันทึกลงฐานข้อมูล
                posts_saved = self.save_posts_to_db(posts_data, keyword)
                log.posts_collected = posts_saved
                log.success = True
            else:
                log.success = False
                log.error_message = "No data returned from API"

        except Exception as e:
            log.success = False
            log.error_message = str(e)
            print(f"Collection failed for keyword '{keyword}': {e}")

        finally:
            # Complete the log
            log.end_time = datetime.utcnow()
            log.duration_seconds = int((log.end_time - log.start_time).total_seconds())

            try:
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                print(f"Error saving collection log: {e}")
                db.session.rollback()

        # เพิ่มหน่วงเวลาเพื่อป้องกัน rate limiting
        time.sleep(self.rate_limit_delay)

        return log.posts_collected if log.success else 0

    def get_trending_hashtags(self, days=7, limit=50):
        """
        หา hashtags ที่กำลัง trending จากข้อมูลที่เก็บไว้
        """
        try:
            # ค้นหา posts ในช่วงเวลาที่กำหนด
            since_date = datetime.utcnow() - timedelta(days=days)
            recent_posts = TikTokPost.query.filter(
                TikTokPost.created_time >= since_date
            ).all()

            # นับ hashtags
            hashtag_stats = {}

            for post in recent_posts:
                hashtags = post.get_hashtags()
                for hashtag in hashtags:
                    if hashtag not in hashtag_stats:
                        hashtag_stats[hashtag] = {
                            'count': 0,
                            'total_likes': 0,
                            'total_views': 0,
                            'posts': []
                        }

                    hashtag_stats[hashtag]['count'] += 1
                    hashtag_stats[hashtag]['total_likes'] += post.like_count
                    hashtag_stats[hashtag]['total_views'] += post.view_count
                    hashtag_stats[hashtag]['posts'].append(post.id)

            # คำนวณ trending score และเรียงลำดับ
            trending = []
            for hashtag, stats in hashtag_stats.items():
                if stats['count'] >= 3:  # อย่างน้อย 3 posts
                    avg_likes = stats['total_likes'] / stats['count']
                    trending_score = stats['count'] * avg_likes

                    trending.append({
                        'hashtag': hashtag,
                        'count': stats['count'],
                        'avg_likes': avg_likes,
                        'total_views': stats['total_views'],
                        'trending_score': trending_score
                    })

            # เรียงตาม trending score
            trending.sort(key=lambda x: x['trending_score'], reverse=True)

            return trending[:limit]

        except Exception as e:
            print(f"Error getting trending hashtags: {e}")
            return []