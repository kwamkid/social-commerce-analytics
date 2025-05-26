from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import threading

from models.models import db, TikTokPost, Keyword, HashtagTrend, ContentIdea, CollectionLog
from services.tiktok_collector import TikTokCollector
from services.analytics import AnalyticsService

api_bp = Blueprint('api', __name__)


@api_bp.route('/dashboard-stats')
def dashboard_stats():
    """API สำหรับ Dashboard statistics"""
    try:
        # Basic stats
        total_posts = TikTokPost.query.count()
        total_keywords = Keyword.query.filter_by(is_active=True).count()

        # Total engagement
        engagement_sum = db.session.query(
            func.sum(TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count)
        ).scalar() or 0

        # Trending posts count
        from config import Config
        trending_posts = TikTokPost.query.filter(
            TikTokPost.like_count >= Config.TRENDING_THRESHOLD
        ).count()

        # Recent activity
        recent_logs = CollectionLog.query.order_by(
            desc(CollectionLog.start_time)
        ).limit(5).all()

        recent_activity = []
        for log in recent_logs:
            recent_activity.append({
                'keyword': log.keyword,
                'posts_collected': log.posts_collected,
                'success': log.success,
                'start_time': log.start_time.isoformat() if log.start_time else None,
                'duration': log.duration_seconds
            })

        return jsonify({
            'success': True,
            'data': {
                'total_posts': total_posts,
                'total_keywords': total_keywords,
                'total_engagement': engagement_sum,
                'trending_posts': trending_posts,
                'recent_activity': recent_activity,
                'last_updated': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/collect-now', methods=['POST'])
def collect_now():
    """API สำหรับเก็บข้อมูลทันที"""
    try:
        def background_collect():
            """Background task สำหรับเก็บข้อมูล"""
            collector = TikTokCollector()
            total_collected = 0

            keywords = Keyword.query.filter_by(is_active=True).all()

            for keyword in keywords:
                collected = collector.collect_for_keyword(keyword.keyword)
                total_collected += collected

                # Update keyword stats
                keyword.last_collection_time = datetime.utcnow()
                keyword.total_posts_found += collected

            db.session.commit()
            return total_collected

        # Start background collection
        thread = threading.Thread(target=background_collect)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Data collection started',
            'status': 'processing'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/trending-hashtags')
def trending_hashtags_api():
    """API สำหรับ trending hashtags"""
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 20, type=int)

        analytics = AnalyticsService()
        trending = analytics.get_trending_hashtags(days=days, limit=limit)

        hashtags_data = []
        for hashtag_info in trending:
            hashtags_data.append({
                'hashtag': hashtag_info[0],
                'count': hashtag_info[1],
                'avg_engagement': hashtag_info[2],
                'trending_score': hashtag_info[3],
                'total_views': hashtag_info[4],
                'total_likes': hashtag_info[5]
            })

        return jsonify({
            'success': True,
            'data': hashtags_data,
            'period_days': days
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/keyword/<keyword>/analytics')
def keyword_analytics_api(keyword):
    """API สำหรับ analytics ของ keyword เฉพาะ"""
    try:
        analytics = AnalyticsService()
        stats = analytics.get_keyword_analytics(keyword)

        if not stats:
            return jsonify({
                'success': False,
                'error': 'Keyword not found or no data available'
            }), 404

        # Timeline data
        timeline = analytics.get_keyword_timeline(keyword, days=30)

        # Hashtag analysis
        hashtag_analysis = analytics.analyze_keyword_hashtags(keyword)

        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'timeline': timeline,
                'hashtag_analysis': hashtag_analysis
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/posts/search')
def search_posts():
    """API สำหรับค้นหา posts"""
    try:
        # Parameters
        keyword = request.args.get('keyword', '')
        hashtag = request.args.get('hashtag', '')
        min_likes = request.args.get('min_likes', 0, type=int)
        days = request.args.get('days', 30, type=int)
        sort_by = request.args.get('sort', 'likes')  # likes, engagement, views
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Build query
        query = TikTokPost.query

        if keyword:
            query = query.filter(TikTokPost.keyword.ilike(f'%{keyword}%'))

        if hashtag:
            query = query.filter(TikTokPost.hashtags.contains(f'"{hashtag}"'))

        if min_likes > 0:
            query = query.filter(TikTokPost.like_count >= min_likes)

        # Date filter
        if days > 0:
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(TikTokPost.created_time >= since_date)

        # Sorting
        if sort_by == 'engagement':
            query = query.order_by(desc(
                TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count
            ))
        elif sort_by == 'views':
            query = query.order_by(desc(TikTokPost.view_count))
        elif sort_by == 'comments':
            query = query.order_by(desc(TikTokPost.comment_count))
        else:  # likes
            query = query.order_by(desc(TikTokPost.like_count))

        # Pagination
        paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        posts_data = []
        for post in paginated.items:
            posts_data.append({
                'id': post.id,
                'video_id': post.video_id,
                'username': post.username,
                'description': post.description,
                'like_count': post.like_count,
                'comment_count': post.comment_count,
                'share_count': post.share_count,
                'view_count': post.view_count,
                'engagement_rate': post.engagement_rate,
                'viral_score': post.viral_score,
                'hashtags': post.get_hashtags(),
                'created_time': post.created_time.isoformat(),
                'keyword': post.keyword
            })

        return jsonify({
            'success': True,
            'data': posts_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            },
            'filters': {
                'keyword': keyword,
                'hashtag': hashtag,
                'min_likes': min_likes,
                'days': days,
                'sort_by': sort_by
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/content-ideas/generate', methods=['POST'])
def generate_content_ideas():
    """API สำหรับสร้าง content ideas"""
    try:
        limit = request.json.get('limit', 10) if request.is_json else 10

        analytics = AnalyticsService()
        ideas = analytics.generate_content_ideas(limit=limit)

        return jsonify({
            'success': True,
            'data': ideas,
            'generated_at': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/posts/<int:post_id>/details')
def post_details(post_id):
    """API สำหรับรายละเอียด post"""
    try:
        post = TikTokPost.query.get_or_404(post_id)

        # Similar posts
        post_hashtags = post.get_hashtags()
        similar_posts = []

        if post_hashtags:
            for hashtag in post_hashtags[:3]:
                similar = TikTokPost.query.filter(
                    TikTokPost.hashtags.contains(f'"{hashtag}"'),
                    TikTokPost.id != post.id
                ).limit(5).all()
                similar_posts.extend(similar)

        # Remove duplicates and limit
        unique_similar = list({p.id: p for p in similar_posts}.values())[:10]

        similar_data = []
        for similar_post in unique_similar:
            similar_data.append({
                'id': similar_post.id,
                'video_id': similar_post.video_id,
                'username': similar_post.username,
                'description': similar_post.description,
                'like_count': similar_post.like_count,
                'hashtags': similar_post.get_hashtags()
            })

        return jsonify({
            'success': True,
            'data': {
                'post': {
                    'id': post.id,
                    'video_id': post.video_id,
                    'username': post.username,
                    'display_name': post.display_name,
                    'description': post.description,
                    'like_count': post.like_count,
                    'comment_count': post.comment_count,
                    'share_count': post.share_count,
                    'view_count': post.view_count,
                    'engagement_rate': post.engagement_rate,
                    'viral_score': post.viral_score,
                    'hashtags': post.get_hashtags(),
                    'mentions': post.get_mentions(),
                    'music_title': post.music_title,
                    'music_author': post.music_author,
                    'created_time': post.created_time.isoformat(),
                    'keyword': post.keyword
                },
                'similar_posts': similar_data
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/keywords/<int:keyword_id>/toggle', methods=['POST'])
def toggle_keyword_api(keyword_id):
    """API สำหรับเปิด/ปิด keyword"""
    try:
        keyword = Keyword.query.get_or_404(keyword_id)
        keyword.is_active = not keyword.is_active
        keyword.updated_time = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'keyword_id': keyword.id,
                'keyword': keyword.keyword,
                'is_active': keyword.is_active
            },
            'message': f'Keyword "{keyword.keyword}" is now {"active" if keyword.is_active else "inactive"}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/export/<format>')
def export_data_api(format):
    """API สำหรับ export ข้อมูล"""
    try:
        if format not in ['csv', 'json', 'excel']:
            return jsonify({
                'success': False,
                'error': 'Invalid format. Supported: csv, json, excel'
            }), 400

        analytics = AnalyticsService()

        if format == 'csv':
            return analytics.export_to_csv()
        elif format == 'json':
            return analytics.export_to_json()
        elif format == 'excel':
            return analytics.export_to_excel()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/health')
def health_check():
    """API สำหรับตรวจสอบสถานะระบบ"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')

        # Get basic stats
        total_posts = TikTokPost.query.count()
        total_keywords = Keyword.query.count()

        # Check recent collection
        recent_log = CollectionLog.query.order_by(
            desc(CollectionLog.start_time)
        ).first()

        last_collection = None
        if recent_log:
            last_collection = recent_log.start_time.isoformat()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'data': {
                'database_connected': True,
                'total_posts': total_posts,
                'total_keywords': total_keywords,
                'last_collection': last_collection,
                'timestamp': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500