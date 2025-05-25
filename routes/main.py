from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import func, desc
import json

from models.models import db, TikTokPost, Keyword, HashtagTrend, ContentIdea, CollectionLog
from services.analytics import AnalyticsService
from config import Config

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """หน้า Dashboard หลัก"""
    try:
        # ข้อมูลสถิติพื้นฐาน
        total_posts = TikTokPost.query.count()
        total_keywords = Keyword.query.filter_by(is_active=True).count()

        # คำนวณ total engagement
        engagement_sum = db.session.query(
            func.sum(TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count)
        ).scalar() or 0

        # Posts ที่ trending (มี engagement สูง)
        trending_threshold = Config.TRENDING_THRESHOLD
        trending_posts = TikTokPost.query.filter(
            TikTokPost.like_count >= trending_threshold
        ).count()

        # ข้อมูลสำหรับกราฟ Engagement Over Time (7 วันล่าสุด)
        analytics = AnalyticsService()
        engagement_data = analytics.get_daily_engagement_data(days=7)

        # Top hashtags จาก 7 วันล่าสุด
        trending_hashtags = analytics.get_trending_hashtags(days=7, limit=15)

        # Recent collection logs
        recent_logs = CollectionLog.query.order_by(
            desc(CollectionLog.start_time)
        ).limit(10).all()

        # ข้อมูลสำหรับกราฟ keywords
        keyword_stats = analytics.get_keyword_distribution()

        return render_template('dashboard.html',
                               total_posts=total_posts,
                               total_keywords=total_keywords,
                               total_engagement=engagement_sum,
                               trending_posts=trending_posts,
                               trending_hashtags=trending_hashtags,
                               recent_logs=recent_logs,
                               engagement_dates=json.dumps([d['date'] for d in engagement_data]),
                               engagement_data=json.dumps([d['engagement'] for d in engagement_data]),
                               keyword_labels=json.dumps([k['keyword'] for k in keyword_stats]),
                               keyword_data=json.dumps([k['count'] for k in keyword_stats]),
                               last_update=datetime.now().strftime('%d/%m/%Y %H:%M'))

    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}', 'error')
        return render_template('dashboard.html',
                               total_posts=0, total_keywords=0,
                               total_engagement=0, trending_posts=0,
                               trending_hashtags=[], recent_logs=[])


@main_bp.route('/keywords')
def keywords():
    """หน้าจัดการ Keywords"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    keywords = Keyword.query.order_by(desc(Keyword.created_time)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('keywords.html', keywords=keywords)


@main_bp.route('/keywords/add', methods=['POST'])
def add_keyword():
    """เพิ่ม Keyword ใหม่"""
    try:
        keyword_text = request.form.get('keyword', '').strip()
        category = request.form.get('category', '').strip()
        priority = request.form.get('priority', 1, type=int)
        description = request.form.get('description', '').strip()

        if not keyword_text:
            flash('กรุณาใส่ keyword', 'error')
            return redirect(url_for('main.keywords'))

        # ตรวจสอบว่ามี keyword นี้แล้วหรือไม่
        existing = Keyword.query.filter_by(keyword=keyword_text).first()
        if existing:
            flash(f'Keyword "{keyword_text}" มีอยู่แล้ว', 'warning')
            return redirect(url_for('main.keywords'))

        # สร้าง keyword ใหม่
        new_keyword = Keyword(
            keyword=keyword_text,
            category=category if category else None,
            priority=priority,
            description=description if description else None
        )

        db.session.add(new_keyword)
        db.session.commit()

        flash(f'เพิ่ม keyword "{keyword_text}" สำเร็จ', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('main.keywords'))


@main_bp.route('/keywords/<int:keyword_id>/toggle')
def toggle_keyword(keyword_id):
    """เปิด/ปิด keyword"""
    try:
        keyword = Keyword.query.get_or_404(keyword_id)
        keyword.is_active = not keyword.is_active
        db.session.commit()

        status = 'เปิดใช้งาน' if keyword.is_active else 'ปิดใช้งาน'
        flash(f'{status} keyword "{keyword.keyword}" แล้ว', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('main.keywords'))


@main_bp.route('/keywords/<int:keyword_id>/delete', methods=['POST'])
def delete_keyword(keyword_id):
    """ลบ keyword"""
    try:
        keyword = Keyword.query.get_or_404(keyword_id)
        keyword_name = keyword.keyword

        # ลบ posts ที่เกี่ยวข้อง (หรือจะเก็บไว้ก็ได้)
        # TikTokPost.query.filter_by(keyword=keyword_name).delete()

        db.session.delete(keyword)
        db.session.commit()

        flash(f'ลบ keyword "{keyword_name}" สำเร็จ', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('main.keywords'))


@main_bp.route('/trending')
def trending():
    """หน้า Trending Content"""
    # Parameters
    hashtag = request.args.get('hashtag', '')
    keyword = request.args.get('keyword', '')
    days = request.args.get('days', 7, type=int)
    sort_by = request.args.get('sort', 'engagement')  # engagement, likes, views
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Base query
    query = TikTokPost.query

    # Filters
    if hashtag:
        query = query.filter(TikTokPost.hashtags.contains(f'"{hashtag}"'))

    if keyword:
        query = query.filter(TikTokPost.keyword == keyword)

    # Date filter
    since_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(TikTokPost.created_time >= since_date)

    # Sorting
    if sort_by == 'likes':
        query = query.order_by(desc(TikTokPost.like_count))
    elif sort_by == 'views':
        query = query.order_by(desc(TikTokPost.view_count))
    elif sort_by == 'comments':
        query = query.order_by(desc(TikTokPost.comment_count))
    else:  # engagement
        query = query.order_by(desc(
            TikTokPost.like_count + TikTokPost.comment_count + TikTokPost.share_count
        ))

    # Pagination
    posts = query.paginate(page=page, per_page=per_page, error_out=False)

    # Trending hashtags for sidebar
    analytics = AnalyticsService()
    trending_hashtags = analytics.get_trending_hashtags(days=days, limit=20)

    # Available keywords for filter
    available_keywords = Keyword.query.filter_by(is_active=True).all()

    return render_template('trending.html',
                           posts=posts,
                           trending_hashtags=trending_hashtags,
                           available_keywords=available_keywords,
                           current_hashtag=hashtag,
                           current_keyword=keyword,
                           current_days=days,
                           current_sort=sort_by)


@main_bp.route('/content-ideas')
def content_ideas():
    """หน้า Content Ideas"""
    try:
        analytics = AnalyticsService()

        # Generate content ideas based on trending data
        ideas = analytics.generate_content_ideas(limit=20)

        # Get high engagement posts for inspiration
        high_engagement_posts = TikTokPost.query.filter(
            TikTokPost.like_count >= Config.TRENDING_THRESHOLD
        ).order_by(desc(TikTokPost.like_count)).limit(10).all()

        # Top performing hashtags
        top_hashtags = analytics.get_trending_hashtags(days=30, limit=25)

        # Content categories analysis
        categories = analytics.get_content_categories()

        return render_template('content_ideas.html',
                               ideas=ideas,
                               high_engagement_posts=high_engagement_posts,
                               top_hashtags=top_hashtags,
                               categories=categories)

    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการโหลดข้อมูล: {str(e)}', 'error')
        return render_template('content_ideas.html',
                               ideas=[], high_engagement_posts=[],
                               top_hashtags=[], categories=[])


@main_bp.route('/analytics/<keyword>')
def keyword_analytics(keyword):
    """แสดง Analytics สำหรับ keyword เฉพาะ"""
    try:
        analytics = AnalyticsService()

        # ข้อมูลพื้นฐาน
        posts = TikTokPost.query.filter_by(keyword=keyword).all()

        if not posts:
            flash(f'ไม่พบข้อมูลสำหรับ keyword "{keyword}"', 'warning')
            return redirect(url_for('main.keywords'))

        # คำนวณสถิติ
        stats = analytics.get_keyword_analytics(keyword)

        # Engagement timeline
        timeline = analytics.get_keyword_timeline(keyword, days=30)

        # Top posts
        top_posts = sorted(posts, key=lambda x: x.like_count, reverse=True)[:10]

        # Hashtag analysis
        hashtag_analysis = analytics.analyze_keyword_hashtags(keyword)

        return render_template('keyword_analytics.html',
                               keyword=keyword,
                               stats=stats,
                               timeline=timeline,
                               top_posts=top_posts,
                               hashtag_analysis=hashtag_analysis)

    except Exception as e:
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return redirect(url_for('main.keywords'))


@main_bp.route('/post/<video_id>')
def post_detail(video_id):
    """แสดงรายละเอียด post"""
    post = TikTokPost.query.filter_by(video_id=video_id).first_or_404()

    # Similar posts (same hashtags)
    post_hashtags = post.get_hashtags()
    similar_posts = []

    if post_hashtags:
        for hashtag in post_hashtags[:3]:  # ใช้ 3 hashtags แรก
            similar = TikTokPost.query.filter(
                TikTokPost.hashtags.contains(f'"{hashtag}"'),
                TikTokPost.id != post.id
            ).limit(5).all()
            similar_posts.extend(similar)

    # Remove duplicates
    similar_posts = list({p.id: p for p in similar_posts}.values())[:10]

    return render_template('post_detail.html',
                           post=post,
                           similar_posts=similar_posts)


@main_bp.route('/export/<format>')
def export_data(format):
    """Export ข้อมูลในรูปแบบต่างๆ"""
    if format not in ['csv', 'json', 'excel']:
        flash('รูปแบบไฟล์ไม่ถูกต้อง', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        analytics = AnalyticsService()

        if format == 'csv':
            return analytics.export_to_csv()
        elif format == 'json':
            return analytics.export_to_json()
        elif format == 'excel':
            return analytics.export_to_excel()

    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการ export: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))