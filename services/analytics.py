import json
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import func, desc
from flask import jsonify, make_response

from models.models import db, TikTokPost, Keyword, HashtagTrend, ContentIdea
from config import Config


class AnalyticsService:
    """Service class สำหรับการวิเคราะห์ข้อมูล"""

    def get_daily_engagement_data(self, days=30):
        """ดึงข้อมูล engagement รายวัน"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            # Query engagement by date
            results = db.session.query(
                func.date(TikTokPost.created_time).label('date'),
                func.sum(TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count).label('engagement'),
                func.count(TikTokPost.id).label('post_count')
            ).filter(
                func.date(TikTokPost.created_time) >= start_date
            ).group_by(
                func.date(TikTokPost.created_time)
            ).order_by('date').all()

            # Format data
            engagement_data = []
            for result in results:
                engagement_data.append({
                    'date': result.date.strftime('%d/%m'),
                    'engagement': int(result.engagement or 0),
                    'post_count': result.post_count
                })

            return engagement_data

        except Exception as e:
            print(f"Error getting daily engagement data: {e}")
            return []

    def get_trending_hashtags(self, days=7, limit=20):
        """หา hashtags ที่กำลัง trending"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # ดึง posts ในช่วงเวลาที่กำหนด
            posts = TikTokPost.query.filter(
                TikTokPost.created_time >= since_date
            ).all()

            hashtag_stats = defaultdict(lambda: {
                'count': 0,
                'total_likes': 0,
                'total_views': 0,
                'total_engagement': 0,
                'avg_engagement': 0,
                'posts': []
            })

            # วิเคราะห์ hashtags
            for post in posts:
                hashtags = post.get_hashtags()
                total_engagement = post.like_count + post.comment_count + post.share_count

                for hashtag in hashtags:
                    stats = hashtag_stats[hashtag]
                    stats['count'] += 1
                    stats['total_likes'] += post.like_count
                    stats['total_views'] += post.view_count
                    stats['total_engagement'] += total_engagement
                    stats['posts'].append(post.id)

            # คำนวณ average และ trending score
            trending_hashtags = []
            for hashtag, stats in hashtag_stats.items():
                if stats['count'] >= 2:  # อย่างน้อย 2 posts
                    stats['avg_engagement'] = stats['total_engagement'] / stats['count']

                    # Trending score = count * avg_engagement
                    trending_score = stats['count'] * stats['avg_engagement']

                    trending_hashtags.append((
                        hashtag,
                        stats['count'],
                        stats['avg_engagement'],
                        trending_score,
                        stats['total_views'],
                        stats['total_likes']
                    ))

            # เรียงตาม trending score
            trending_hashtags.sort(key=lambda x: x[3], reverse=True)

            return trending_hashtags[:limit]

        except Exception as e:
            print(f"Error getting trending hashtags: {e}")
            return []

    def get_keyword_distribution(self):
        """ดึงการกระจายของ posts ตาม keywords"""
        try:
            results = db.session.query(
                TikTokPost.keyword,
                func.count(TikTokPost.id).label('count')
            ).group_by(TikTokPost.keyword).order_by(desc('count')).limit(10).all()

            return [{'keyword': r.keyword, 'count': r.count} for r in results]

        except Exception as e:
            print(f"Error getting keyword distribution: {e}")
            return []

    def get_keyword_analytics(self, keyword):
        """วิเคราะห์ข้อมูลสำหรับ keyword เฉพาะ"""
        try:
            posts = TikTokPost.query.filter_by(keyword=keyword).all()

            if not posts:
                return None

            # คำนวณสถิติ
            total_posts = len(posts)
            total_views = sum(p.view_count for p in posts)
            total_likes = sum(p.like_count for p in posts)
            total_comments = sum(p.comment_count for p in posts)
            total_shares = sum(p.share_count for p in posts)
            total_engagement = total_likes + total_comments + total_shares

            avg_views = total_views / total_posts if total_posts > 0 else 0
            avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
            engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0

            # หา post ที่ดีที่สุด
            best_post = max(posts, key=lambda p: p.like_count + p.comment_count + p.share_count)

            # วิเคราะห์ timing
            posting_hours = Counter([p.created_time.hour for p in posts])
            best_hour = posting_hours.most_common(1)[0] if posting_hours else (0, 0)

            return {
                'keyword': keyword,
                'total_posts': total_posts,
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_shares': total_shares,
                'total_engagement': total_engagement,
                'avg_views': avg_views,
                'avg_engagement': avg_engagement,
                'engagement_rate': engagement_rate,
                'best_post': best_post,
                'best_posting_hour': best_hour[0],
                'posts_at_best_hour': best_hour[1]
            }

        except Exception as e:
            print(f"Error getting keyword analytics: {e}")
            return None

    def get_keyword_timeline(self, keyword, days=30):
        """ดึงข้อมูล timeline สำหรับ keyword"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            results = db.session.query(
                func.date(TikTokPost.created_time).label('date'),
                func.count(TikTokPost.id).label('post_count'),
                func.sum(TikTokPost.like_count).label('total_likes'),
                func.sum(TikTokPost.view_count).label('total_views'),
                func.avg(TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count).label(
                    'avg_engagement')
            ).filter(
                TikTokPost.keyword == keyword,
                func.date(TikTokPost.created_time) >= start_date
            ).group_by(
                func.date(TikTokPost.created_time)
            ).order_by('date').all()

            timeline_data = []
            for result in results:
                timeline_data.append({
                    'date': result.date.strftime('%Y-%m-%d'),
                    'post_count': result.post_count,
                    'total_likes': int(result.total_likes or 0),
                    'total_views': int(result.total_views or 0),
                    'avg_engagement': float(result.avg_engagement or 0)
                })

            return timeline_data

        except Exception as e:
            print(f"Error getting keyword timeline: {e}")
            return []

    def analyze_keyword_hashtags(self, keyword):
        """วิเคราะห์ hashtags สำหรับ keyword เฉพาะ"""
        try:
            posts = TikTokPost.query.filter_by(keyword=keyword).all()

            hashtag_performance = defaultdict(lambda: {
                'count': 0,
                'total_engagement': 0,
                'avg_engagement': 0,
                'best_post_id': None,
                'best_engagement': 0
            })

            for post in posts:
                hashtags = post.get_hashtags()
                engagement = post.like_count + post.comment_count + post.share_count

                for hashtag in hashtags:
                    stats = hashtag_performance[hashtag]
                    stats['count'] += 1
                    stats['total_engagement'] += engagement

                    if engagement > stats['best_engagement']:
                        stats['best_engagement'] = engagement
                        stats['best_post_id'] = post.id

            # คำนวณ average
            for hashtag, stats in hashtag_performance.items():
                stats['avg_engagement'] = stats['total_engagement'] / stats['count']

            # เรียงตาม performance
            sorted_hashtags = sorted(
                hashtag_performance.items(),
                key=lambda x: x[1]['avg_engagement'],
                reverse=True
            )

            return dict(sorted_hashtags[:20])  # top 20

        except Exception as e:
            print(f"Error analyzing keyword hashtags: {e}")
            return {}

    def generate_content_ideas(self, limit=20):
        """สร้าง content ideas จากข้อมูลที่วิเคราะห์"""
        try:
            ideas = []

            # 1. Ideas จาก trending hashtags
            trending_hashtags = self.get_trending_hashtags(days=7, limit=10)
            for hashtag_data in trending_hashtags[:5]:
                hashtag = hashtag_data[0]
                avg_engagement = hashtag_data[2]

                idea = {
                    'title': f'Content ที่ใช้ #{hashtag}',
                    'description': f'สร้าง content ที่เกี่ยวข้องกับ #{hashtag} ซึ่งกำลัง trending',
                    'predicted_engagement': avg_engagement,
                    'confidence_score': min(hashtag_data[1] / 10 * 100, 100),  # base on usage count
                    'category': 'trending_hashtag',
                    'hashtags': [hashtag],
                    'type': 'hashtag_based'
                }
                ideas.append(idea)

            # 2. Ideas จาก high-performing content patterns
            high_performers = TikTokPost.query.filter(
                TikTokPost.like_count >= Config.TRENDING_THRESHOLD
            ).order_by(desc(TikTokPost.like_count)).limit(20).all()

            # วิเคราะห์ patterns
            common_hashtags = Counter()
            common_keywords = Counter()

            for post in high_performers:
                hashtags = post.get_hashtags()
                common_hashtags.update(hashtags)
                common_keywords[post.keyword] += 1

            # สร้าง ideas จาก patterns
            for hashtag, count in common_hashtags.most_common(5):
                if count >= 3:  # ปรากฏอย่างน้อย 3 ครั้ง
                    avg_performance = sum(
                        p.like_count + p.comment_count + p.share_count
                        for p in high_performers
                        if hashtag in p.get_hashtags()
                    ) / count

                    idea = {
                        'title': f'Content Pattern: #{hashtag}',
                        'description': f'Pattern ที่พบในผลงานยอดนิยม: ใช้ #{hashtag} ร่วมกับ content ที่มีคุณภาพ',
                        'predicted_engagement': avg_performance,
                        'confidence_score': min(count / 5 * 100, 100),
                        'category': 'high_performer_pattern',
                        'hashtags': [hashtag],
                        'type': 'pattern_based'
                    }
                    ideas.append(idea)

            # 3. Ideas จาก keyword performance
            for keyword, count in common_keywords.most_common(3):
                keyword_posts = [p for p in high_performers if p.keyword == keyword]
                avg_performance = sum(
                    p.like_count + p.comment_count + p.share_count
                    for p in keyword_posts
                ) / len(keyword_posts)

                idea = {
                    'title': f'Focus on "{keyword}" Content',
                    'description': f'Keyword "{keyword}" แสดงผลลัพธ์ที่ดี ควรสร้าง content เพิ่มเติม',
                    'predicted_engagement': avg_performance,
                    'confidence_score': min(count / 3 * 100, 100),
                    'category': 'keyword_opportunity',
                    'hashtags': self._get_keyword_top_hashtags(keyword),
                    'type': 'keyword_based'
                }
                ideas.append(idea)

            # 4. Time-based ideas
            time_analysis = self._analyze_posting_times()
            if time_analysis:
                idea = {
                    'title': f'โพสต์ในช่วงเวลา {time_analysis["best_hour"]}:00',
                    'description': f'ข้อมูลแสดงว่าการโพสต์ในช่วง {time_analysis["best_hour"]}:00 น. ได้ engagement ดีที่สุด',
                    'predicted_engagement': time_analysis['avg_engagement'],
                    'confidence_score': time_analysis['confidence'],
                    'category': 'timing_optimization',
                    'hashtags': [],
                    'type': 'timing_based'
                }
                ideas.append(idea)

            # 5. Combination ideas (hashtag combinations ที่ work ดี)
            combo_ideas = self._find_hashtag_combinations()
            ideas.extend(combo_ideas[:3])

            # เรียงตาม predicted engagement
            ideas.sort(key=lambda x: x['predicted_engagement'], reverse=True)

            return ideas[:limit]

        except Exception as e:
            print(f"Error generating content ideas: {e}")
            return []

    def _get_keyword_top_hashtags(self, keyword, limit=5):
        """หา hashtags ยอดนิยมสำหรับ keyword"""
        try:
            posts = TikTokPost.query.filter_by(keyword=keyword).all()
            hashtag_counter = Counter()

            for post in posts:
                hashtags = post.get_hashtags()
                hashtag_counter.update(hashtags)

            return [hashtag for hashtag, count in hashtag_counter.most_common(limit)]

        except Exception as e:
            print(f"Error getting keyword top hashtags: {e}")
            return []

    def _analyze_posting_times(self):
        """วิเคราะห์เวลาที่ดีที่สุดในการโพสต์"""
        try:
            posts = TikTokPost.query.filter(
                TikTokPost.created_time >= datetime.utcnow() - timedelta(days=30)
            ).all()

            hour_performance = defaultdict(list)

            for post in posts:
                hour = post.created_time.hour
                engagement = post.like_count + post.comment_count + post.share_count
                hour_performance[hour].append(engagement)

            # คำนวณ average engagement ต่อชั่วโมง
            hour_averages = {}
            for hour, engagements in hour_performance.items():
                if len(engagements) >= 5:  # อย่างน้อย 5 posts
                    hour_averages[hour] = sum(engagements) / len(engagements)

            if hour_averages:
                best_hour = max(hour_averages, key=hour_averages.get)
                return {
                    'best_hour': best_hour,
                    'avg_engagement': hour_averages[best_hour],
                    'confidence': min(len(hour_performance[best_hour]) / 10 * 100, 100)
                }

            return None

        except Exception as e:
            print(f"Error analyzing posting times: {e}")
            return None

    def _find_hashtag_combinations(self):
        """หา combination ของ hashtags ที่ให้ผลดี"""
        try:
            high_performers = TikTokPost.query.filter(
                TikTokPost.like_count >= Config.TRENDING_THRESHOLD
            ).limit(50).all()

            # หา combinations ที่พบบ่อย
            combo_performance = defaultdict(list)

            for post in posts:
                hashtags = post.get_hashtags()
                engagement = post.like_count + post.comment_count + post.share_count

                # สร้าง combinations (pairs)
                for i in range(len(hashtags)):
                    for j in range(i + 1, len(hashtags)):
                        combo = tuple(sorted([hashtags[i], hashtags[j]]))
                        combo_performance[combo].append(engagement)

            # หา combinations ที่ดีที่สุด
            ideas = []
            for combo, engagements in combo_performance.items():
                if len(engagements) >= 3:  # ปรากฏอย่างน้อย 3 ครั้ง
                    avg_engagement = sum(engagements) / len(engagements)

                    idea = {
                        'title': f'Combination: #{combo[0]} + #{combo[1]}',
                        'description': f'การใช้ #{combo[0]} และ #{combo[1]} ร่วมกันแสดงผลลัพธ์ที่ดี',
                        'predicted_engagement': avg_engagement,
                        'confidence_score': min(len(engagements) / 5 * 100, 100),
                        'category': 'hashtag_combination',
                        'hashtags': list(combo),
                        'type': 'combination_based'
                    }
                    ideas.append(idea)

            # เรียงตาม performance
            ideas.sort(key=lambda x: x['predicted_engagement'], reverse=True)
            return ideas[:3]

        except Exception as e:
            print(f"Error finding hashtag combinations: {e}")
            return []

    def get_content_categories(self):
        """วิเคราะห์ categories ของ content"""
        try:
            # Group by keyword (ใช้ keyword เป็น category)
            results = db.session.query(
                TikTokPost.keyword,
                func.count(TikTokPost.id).label('post_count'),
                func.avg(TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count).label(
                    'avg_engagement'),
                func.sum(TikTokPost.view_count).label('total_views')
            ).group_by(TikTokPost.keyword).all()

            categories = []
            for result in results:
                categories.append({
                    'category': result.keyword,
                    'post_count': result.post_count,
                    'avg_engagement': float(result.avg_engagement or 0),
                    'total_views': int(result.total_views or 0),
                    'engagement_per_view': (result.avg_engagement / (
                                result.total_views / result.post_count)) * 100 if result.total_views else 0
                })

            # เรียงตาม avg_engagement
            categories.sort(key=lambda x: x['avg_engagement'], reverse=True)

            return categories

        except Exception as e:
            print(f"Error getting content categories: {e}")
            return []

    def export_to_csv(self):
        """Export ข้อมูลเป็น CSV"""
        try:
            posts = TikTokPost.query.all()

            data = []
            for post in posts:
                data.append({
                    'video_id': post.video_id,
                    'username': post.username,
                    'description': post.description,
                    'keyword': post.keyword,
                    'like_count': post.like_count,
                    'comment_count': post.comment_count,
                    'share_count': post.share_count,
                    'view_count': post.view_count,
                    'engagement_rate': post.engagement_rate,
                    'viral_score': post.viral_score,
                    'hashtags': ','.join(post.get_hashtags()),
                    'created_time': post.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'scraped_time': post.scraped_time.strftime('%Y-%m-%d %H:%M:%S')
                })

            df = pd.DataFrame(data)

            response = make_response(df.to_csv(index=False, encoding='utf-8-sig'))
            response.headers[
                "Content-Disposition"] = f"attachment; filename=tiktok_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response.headers["Content-type"] = "text/csv"

            return response

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None

    def export_to_json(self):
        """Export ข้อมูลเป็น JSON"""
        try:
            posts = TikTokPost.query.all()

            data = {
                'export_date': datetime.now().isoformat(),
                'total_posts': len(posts),
                'posts': []
            }

            for post in posts:
                data['posts'].append({
                    'video_id': post.video_id,
                    'username': post.username,
                    'description': post.description,
                    'keyword': post.keyword,
                    'metrics': {
                        'like_count': post.like_count,
                        'comment_count': post.comment_count,
                        'share_count': post.share_count,
                        'view_count': post.view_count,
                        'engagement_rate': post.engagement_rate,
                        'viral_score': post.viral_score
                    },
                    'content': {
                        'hashtags': post.get_hashtags(),
                        'mentions': post.get_mentions(),
                        'music_title': post.music_title,
                        'music_author': post.music_author
                    },
                    'timestamps': {
                        'created_time': post.created_time.isoformat(),
                        'scraped_time': post.scraped_time.isoformat()
                    }
                })

            response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
            response.headers[
                "Content-Disposition"] = f"attachment; filename=tiktok_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            response.headers["Content-type"] = "application/json"

            return response

        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return None

    def export_to_excel(self):
        """Export ข้อมูลเป็น Excel"""
        try:
            posts = TikTokPost.query.all()

            # สร้าง DataFrame
            data = []
            for post in posts:
                data.append({
                    'Video ID': post.video_id,
                    'Username': post.username,
                    'Description': post.description,
                    'Keyword': post.keyword,
                    'Likes': post.like_count,
                    'Comments': post.comment_count,
                    'Shares': post.share_count,
                    'Views': post.view_count,
                    'Engagement Rate (%)': round(post.engagement_rate, 2),
                    'Viral Score': round(post.viral_score, 2),
                    'Hashtags': ', '.join(post.get_hashtags()),
                    'Music Title': post.music_title,
                    'Created Time': post.created_time,
                    'Scraped Time': post.scraped_time
                })

            df = pd.DataFrame(data)

            # สร้าง Excel file
            from io import BytesIO
            output = BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='TikTok Posts', index=False)

                # เพิ่ม summary sheet
                summary_data = {
                    'Metric': ['Total Posts', 'Total Likes', 'Total Views', 'Avg Engagement Rate'],
                    'Value': [
                        len(posts),
                        sum(p.like_count for p in posts),
                        sum(p.view_count for p in posts),
                        round(sum(p.engagement_rate for p in posts) / len(posts), 2) if posts else 0
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

            output.seek(0)

            response = make_response(output.read())
            response.headers[
                "Content-Disposition"] = f"attachment; filename=tiktok_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            return response

        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return None