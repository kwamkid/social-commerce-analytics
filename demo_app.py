"""
TikTok Social Listening - Demo Application
สร้างไว้สำหรับทำ Demo Video ส่ง TikTok Developer Platform

วิธีรัน:
1. pip install flask
2. python demo_app.py
3. เปิด http://localhost:5000
4. บันทึกวิดีโอด้วย OBS หรือ Loom
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import random
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'demo-secret-key'

# Mock Data สำหรับ Demo
mock_posts = [
    {
        'id': 1,
        'video_id': 'demo001',
        'username': 'thaifood_lover',
        'display_name': 'Thai Food Lover',
        'description': 'สูตรผัดไทยที่ได้รสชาติแบบต้นตำรับ! 🍜✨ #ผัดไทย #อาหารไทย #ทำอาหาร #สูตรเด็ด',
        'like_count': 15420,
        'comment_count': 234,
        'share_count': 89,
        'view_count': 125000,
        'engagement_rate': 12.5,
        'viral_score': 78.5,
        'hashtags': ['ผัดไทย', 'อาหารไทย', 'ทำอาหาร', 'สูตรเด็ด'],
        'created_time': datetime.now() - timedelta(hours=2)
    },
    {
        'id': 2,
        'video_id': 'demo002',
        'username': 'travel_thailand_official',
        'display_name': 'Travel Thailand',
        'description': 'เที่ยวกรุงเทพ 24 ชั่วโมง สถานที่เด็ดๆ ที่ไม่ควรพลาด! 🏛️🚇 #กรุงเทพ #ท่องเที่ยว #เที่ยวไทย',
        'like_count': 8900,
        'comment_count': 156,
        'share_count': 67,
        'view_count': 89000,
        'engagement_rate': 10.2,
        'viral_score': 65.3,
        'hashtags': ['กรุงเทพ', 'ท่องเที่ยว', 'เที่ยวไทย'],
        'created_time': datetime.now() - timedelta(hours=5)
    },
    {
        'id': 3,
        'video_id': 'demo003',
        'username': 'fashion_bangkok',
        'display_name': 'Bangkok Fashion',
        'description': 'แฟชั่นสไตล์เกาหลีในงบ 500 บาท! โดนใจสาวออฟฟิศแน่นอน 💄👗 #แฟชั่น #สไตล์เกาหลี #งบน้อย',
        'like_count': 12300,
        'comment_count': 189,
        'share_count': 156,
        'view_count': 98000,
        'engagement_rate': 13.1,
        'viral_score': 72.8,
        'hashtags': ['แฟชั่น', 'สไตล์เกาหลี', 'งบน้อย'],
        'created_time': datetime.now() - timedelta(hours=8)
    },
    {
        'id': 4,
        'video_id': 'demo004',
        'username': 'tech_reviewer_th',
        'display_name': 'Tech Reviewer TH',
        'description': 'รีวิวมือถือใหม่ล่าสุด! ราคาหมื่นต้นๆ คุ้มค่าสุดๆ 📱⚡ #รีวิวมือถือ #เทคโนโลยี #มือถือใหม่',
        'like_count': 7800,
        'comment_count': 234,
        'share_count': 45,
        'view_count': 76000,
        'engagement_rate': 10.6,
        'viral_score': 58.9,
        'hashtags': ['รีวิวมือถือ', 'เทคโนโลยี', 'มือถือใหม่'],
        'created_time': datetime.now() - timedelta(hours=12)
    },
    {
        'id': 5,
        'video_id': 'demo005',
        'username': 'fitness_thailand',
        'display_name': 'Fitness Thailand',
        'description': 'ออกกำลังกายที่บ้าน 15 นาที เผาผลาญ 200 แคลอรี่! 💪🔥 #ออกกำลังกาย #ลดน้ำหนัก #ฟิตเนส',
        'like_count': 9200,
        'comment_count': 167,
        'share_count': 234,
        'view_count': 87000,
        'engagement_rate': 11.1,
        'viral_score': 63.7,
        'hashtags': ['ออกกำลังกาย', 'ลดน้ำหนัก', 'ฟิตเนส'],
        'created_time': datetime.now() - timedelta(hours=15)
    }
]

mock_keywords = [
    {'id': 1, 'keyword': 'อาหารไทย', 'category': 'Food', 'posts_found': 234, 'active': True, 'priority': 5},
    {'id': 2, 'keyword': 'ท่องเที่ยว', 'category': 'Travel', 'posts_found': 189, 'active': True, 'priority': 4},
    {'id': 3, 'keyword': 'แฟชั่น', 'category': 'Fashion', 'posts_found': 156, 'active': True, 'priority': 3},
    {'id': 4, 'keyword': 'เทคโนโลยี', 'category': 'Technology', 'posts_found': 134, 'active': True, 'priority': 3},
    {'id': 5, 'keyword': 'ฟิตเนส', 'category': 'Fitness', 'posts_found': 98, 'active': False, 'priority': 2},
]

mock_content_ideas = [
    {
        'title': 'วิธีทำส้มตำแบบเดิมๆ ที่บ้าน',
        'description': 'สร้าง content แนว tutorial ทำส้มตำ เพราะ #อาหารไทย กำลัง trending และมี engagement rate สูง',
        'confidence_score': 85.2,
        'predicted_engagement': 8500,
        'category': 'Food',
        'hashtags': ['ส้มตำ', 'อาหารไทย', 'ทำอาหาร'],
        'type': 'trending_hashtag'
    },
    {
        'title': 'เที่ยวตลาดนัดกรุงเทพในงบ 500 บาท',
        'description': 'Content แนว budget travel ที่กำลังได้รับความนิยม ควรทำช่วงเย็นวันศุกร์-อาทิตย์',
        'confidence_score': 78.9,
        'predicted_engagement': 6700,
        'category': 'Travel',
        'hashtags': ['ท่องเที่ยว', 'กรุงเทพ', 'งบน้อย'],
        'type': 'pattern_based'
    },
    {
        'title': 'แต่งหน้าลุคเกาหลีในวันฝนตก',
        'description': 'Makeup tutorial ที่เน้นความทนทาน เพราะกำลังเป็นฤดูฝน และ #แฟชั่น มี engagement สูง',
        'confidence_score': 73.4,
        'predicted_engagement': 5900,
        'category': 'Beauty',
        'hashtags': ['แฟชั่น', 'แต่งหน้า', 'สไตล์เกาหลี'],
        'type': 'timing_based'
    }
]


# Routes
@app.route('/')
def dashboard():
    total_posts = len(mock_posts)
    total_keywords = len([k for k in mock_keywords if k['active']])
    total_engagement = sum(p['like_count'] + p['comment_count'] + p['share_count'] for p in mock_posts)
    trending_posts = len([p for p in mock_posts if p['viral_score'] >= 60])

    # Top hashtags
    all_hashtags = []
    for post in mock_posts:
        all_hashtags.extend(post['hashtags'])

    from collections import Counter
    trending_hashtags = Counter(all_hashtags).most_common(8)

    return render_template_string(DASHBOARD_TEMPLATE,
                                  posts=mock_posts[:3],
                                  total_posts=total_posts,
                                  total_keywords=total_keywords,
                                  total_engagement=total_engagement,
                                  trending_posts=trending_posts,
                                  trending_hashtags=trending_hashtags)


@app.route('/keywords')
def keywords():
    return render_template_string(KEYWORDS_TEMPLATE, keywords=mock_keywords)


@app.route('/add-keyword', methods=['POST'])
def add_keyword():
    keyword = request.form.get('keyword', '').strip()
    category = request.form.get('category', '')
    priority = int(request.form.get('priority', 3))

    if keyword:
        # จำลองการเพิ่ม keyword
        new_keyword = {
            'id': len(mock_keywords) + 1,
            'keyword': keyword,
            'category': category,
            'posts_found': random.randint(20, 200),
            'active': True,
            'priority': priority
        }
        mock_keywords.append(new_keyword)
        flash(f'เพิ่ม keyword "{keyword}" เรียบร้อยแล้ว!', 'success')
    else:
        flash('กรุณาใส่ keyword', 'error')

    return redirect(url_for('keywords'))


@app.route('/trending')
def trending():
    # Filter และ sort posts
    hashtag = request.args.get('hashtag', '')
    sort_by = request.args.get('sort', 'engagement')

    filtered_posts = mock_posts.copy()

    if hashtag:
        filtered_posts = [p for p in filtered_posts if hashtag in p['hashtags']]

    # Sort
    if sort_by == 'likes':
        filtered_posts.sort(key=lambda x: x['like_count'], reverse=True)
    elif sort_by == 'views':
        filtered_posts.sort(key=lambda x: x['view_count'], reverse=True)
    else:  # engagement
        filtered_posts.sort(key=lambda x: x['like_count'] + x['comment_count'] + x['share_count'], reverse=True)

    return render_template_string(TRENDING_TEMPLATE,
                                  posts=filtered_posts,
                                  current_hashtag=hashtag,
                                  current_sort=sort_by)


@app.route('/content-ideas')
def content_ideas():
    return render_template_string(CONTENT_IDEAS_TEMPLATE,
                                  ideas=mock_content_ideas,
                                  high_engagement_posts=mock_posts[:3])


@app.route('/collect-data')
def collect_data():
    # จำลองการเก็บข้อมูล
    flash('กำลังเก็บข้อมูลจาก TikTok Research API...', 'info')
    time.sleep(2)  # จำลองเวลาประมวลผล

    new_posts = random.randint(15, 35)
    flash(f'เก็บข้อมูลเสร็จสิ้น! พบ posts ใหม่ {new_posts} รายการ', 'success')

    return redirect(url_for('dashboard'))


@app.route('/api/generate-ideas', methods=['POST'])
def generate_ideas():
    # จำลองการสร้าง content ideas ใหม่
    time.sleep(1)
    return jsonify({
        'success': True,
        'message': 'สร้าง content ideas ใหม่เรียบร้อย',
        'ideas_count': len(mock_content_ideas)
    })


# HTML Templates
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Social Listening - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { padding-top: 70px; background-color: #f8f9fa; }
        .navbar-brand { font-weight: 700; font-size: 1.5rem; }
        .stats-card { 
            background: linear-gradient(135deg, #ff0050 0%, #ff4081 100%); 
            color: white; border-radius: 15px; padding: 1.5rem; text-align: center; margin-bottom: 20px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stats-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255, 0, 80, 0.3); }
        .stats-card.secondary { background: linear-gradient(135deg, #25f4ee 0%, #00bcd4 100%); }
        .stats-card.success { background: linear-gradient(135deg, #25d366 0%, #4caf50 100%); }
        .stats-card.warning { background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%); }
        .stats-number { font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
        .stats-label { font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; }
        .post-item { 
            border-left: 4px solid #ff0050; background: white; margin-bottom: 15px; 
            padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .hashtag { 
            display: inline-block; background: #e3f2fd; color: #1976d2; 
            padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.85rem; 
            margin: 0.125rem; text-decoration: none; transition: all 0.2s ease;
        }
        .hashtag:hover { background: #bbdefb; color: #1565c0; transform: scale(1.05); }
        .engagement-stats { display: flex; gap: 20px; margin-top: 15px; }
        .engagement-stats .metric { text-align: center; }
        .engagement-stats .metric i { font-size: 1.2rem; margin-bottom: 5px; }
        .engagement-stats .metric .value { font-weight: 700; font-size: 1.1rem; }
        .engagement-stats .metric .label { font-size: 0.8rem; color: #666; }
        .card { border: none; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); }
        .card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12); }
        .trending-item { 
            border-left: 3px solid #25f4ee; background: #f8f9fa; 
            margin-bottom: 10px; padding: 12px; border-radius: 0 8px 8px 0;
        }
        .btn-tiktok { 
            background: linear-gradient(135deg, #ff0050 0%, #ff4081 100%); 
            color: white; border: none; 
        }
        .btn-tiktok:hover { 
            background: linear-gradient(135deg, #e60048 0%, #e6386f 100%); 
            color: white; transform: translateY(-1px); 
        }
        .demo-badge {
            position: fixed; top: 15px; right: 15px; z-index: 9999;
            background: #ff0050; color: white; padding: 5px 10px; border-radius: 15px;
            font-size: 0.8rem; font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="demo-badge">🎬 DEMO MODE</div>

    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fab fa-tiktok me-2"></i>TikTok Social Listening
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link active" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('keywords') }}">Keywords</a>
                <a class="nav-link" href="{{ url_for('trending') }}">Trending</a>
                <a class="nav-link" href="{{ url_for('content_ideas') }}">Content Ideas</a>
            </div>
        </div>
    </nav>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="container mt-3">
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'info' if category == 'info' else 'danger' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12">
                <h2><i class="fas fa-chart-line me-2"></i>Dashboard</h2>
                <p class="text-muted">ภาพรวมข้อมูล Social Listening จาก TikTok</p>
            </div>
        </div>

        <!-- Stats Cards -->
        <div class="row mb-4">
            <div class="col-lg-3 col-md-6">
                <div class="stats-card">
                    <div class="stats-number">{{ "{:,}".format(total_posts) }}</div>
                    <div class="stats-label">Total Posts</div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="stats-card secondary">
                    <div class="stats-number">{{ total_keywords }}</div>
                    <div class="stats-label">Active Keywords</div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="stats-card success">
                    <div class="stats-number">{{ "{:,}".format(total_engagement) }}</div>
                    <div class="stats-label">Total Engagement</div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="stats-card warning">
                    <div class="stats-number">{{ trending_posts }}</div>
                    <div class="stats-label">Trending Posts</div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Recent Viral Posts -->
            <div class="col-lg-8 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-fire me-2"></i>Recent Viral Posts</h5>
                    </div>
                    <div class="card-body">
                        {% for post in posts %}
                        <div class="post-item">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <strong class="text-primary">@{{ post.username }}</strong>
                                    <span class="text-muted ms-2">({{ post.display_name }})</span>
                                </div>
                                <span class="badge bg-danger">VIRAL {{ "%.1f"|format(post.viral_score) }}%</span>
                            </div>
                            <p class="mb-3">{{ post.description }}</p>
                            <div class="mb-3">
                                {% for hashtag in post.hashtags %}
                                    <a href="{{ url_for('trending', hashtag=hashtag) }}" class="hashtag">#{{ hashtag }}</a>
                                {% endfor %}
                            </div>
                            <div class="engagement-stats">
                                <div class="metric">
                                    <i class="fas fa-heart text-danger"></i>
                                    <div class="value">{{ "{:,}".format(post.like_count) }}</div>
                                    <div class="label">Likes</div>
                                </div>
                                <div class="metric">
                                    <i class="fas fa-comment text-primary"></i>
                                    <div class="value">{{ "{:,}".format(post.comment_count) }}</div>
                                    <div class="label">Comments</div>
                                </div>
                                <div class="metric">
                                    <i class="fas fa-share text-success"></i>
                                    <div class="value">{{ "{:,}".format(post.share_count) }}</div>
                                    <div class="label">Shares</div>
                                </div>
                                <div class="metric">
                                    <i class="fas fa-eye text-info"></i>
                                    <div class="value">{{ "{:,}".format(post.view_count) }}</div>
                                    <div class="label">Views</div>
                                </div>
                                <div class="metric">
                                    <i class="fas fa-chart-line text-warning"></i>
                                    <div class="value">{{ "%.1f"|format(post.engagement_rate) }}%</div>
                                    <div class="label">Engagement</div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Sidebar -->
            <div class="col-lg-4">
                <!-- Quick Actions -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-bolt me-2"></i>Quick Actions</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="{{ url_for('keywords') }}" class="btn btn-primary">
                                <i class="fas fa-plus-circle me-2"></i>Add Keywords
                            </a>
                            <a href="{{ url_for('collect_data') }}" class="btn btn-tiktok">
                                <i class="fas fa-download me-2"></i>Collect Data Now
                            </a>
                            <a href="{{ url_for('trending') }}" class="btn btn-outline-warning">
                                <i class="fas fa-fire me-2"></i>View Trending
                            </a>
                            <a href="{{ url_for('content_ideas') }}" class="btn btn-outline-info">
                                <i class="fas fa-lightbulb me-2"></i>Get Content Ideas
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Trending Hashtags -->
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-hashtag me-2"></i>Trending Hashtags</h6>
                    </div>
                    <div class="card-body">
                        {% for hashtag, count in trending_hashtags %}
                        <div class="trending-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <a href="{{ url_for('trending', hashtag=hashtag) }}" class="text-decoration-none">
                                    <strong>#{{ hashtag }}</strong>
                                </a>
                                <span class="badge bg-primary">{{ count }}</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

KEYWORDS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Keywords Management - TikTok Social Listening</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { padding-top: 70px; background-color: #f8f9fa; }
        .navbar-brand { font-weight: 700; font-size: 1.5rem; }
        .card { border: none; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); }
        .card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12); }
        .demo-badge {
            position: fixed; top: 15px; right: 15px; z-index: 9999;
            background: #ff0050; color: white; padding: 5px 10px; border-radius: 15px;
            font-size: 0.8rem; font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="demo-badge">🎬 DEMO MODE</div>

    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fab fa-tiktok me-2"></i>TikTok Social Listening
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link active" href="{{ url_for('keywords') }}">Keywords</a>
                <a class="nav-link" href="{{ url_for('trending') }}">Trending</a>
                <a class="nav-link" href="{{ url_for('content_ideas') }}">Content Ideas</a>
            </div>
        </div>
    </nav>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="container mt-3">
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    <div class="container mt-4">
        <h2><i class="fas fa-key me-2"></i>Keywords Management</h2>
        <p class="text-muted">จัดการ keywords สำหรับติดตาม content บน TikTok</p>

        <!-- Add New Keyword -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-plus-circle me-2"></i>Add New Keyword</h5>
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('add_keyword') }}">
                    <div class="row">
                        <div class="col-md-3">
                            <input type="text" name="keyword" class="form-control" placeholder="เช่น อาหารไทย, แฟชั่น" required>
                        </div>
                        <div class="col-md-2">
                            <select name="category" class="form-select">
                                <option value="">เลือก Category</option>
                                <option value="Food">Food</option>
                                <option value="Travel">Travel</option>
                                <option value="Fashion">Fashion</option>
                                <option value="Technology">Technology</option>
                                <option value="Fitness">Fitness</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <select name="priority" class="form-select">
                                <option value="1">Low (1)</option>
                                <option value="2">Medium (2)</option>
                                <option value="3" selected>Normal (3)</option>
                                <option value="4">High (4)</option>
                                <option value="5">Critical (5)</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <input type="text" name="description" class="form-control" placeholder="รายละเอียดเพิ่มเติม">
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-plus me-1"></i>Add Keyword
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Keywords List -->
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-list me-2"></i>Active Keywords</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Keyword</th>
                                <th>Category</th>
                                <th>Priority</th>
                                <th>Posts Found</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for keyword in keywords %}
                            <tr>
                                <td><strong class="text-primary">{{ keyword.keyword }}</strong></td>
                                <td>
                                    {% if keyword.category %}
                                        <span class="badge bg-info">{{ keyword.category }}</span>
                                    {% else %}
                                        <span class="text-muted">-</span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if keyword.priority == 5 %}
                                        <span class="badge bg-danger">Critical</span>
                                    {% elif keyword.priority == 4 %}
                                        <span class="badge bg-warning">High</span>
                                    {% elif keyword.priority == 3 %}
                                        <span class="badge bg-primary">Normal</span>
                                    {% elif keyword.priority == 2 %}
                                        <span class="badge bg-info">Medium</span>
                                    {% else %}
                                        <span class="badge bg-secondary">Low</span>
                                    {% endif %}
                                </td>
                                <td><span class="fw-semibold">{{ keyword.posts_found }}</span></td>
                                <td>
                                    {% if keyword.active %}
                                        <span class="badge bg-success">Active</span>
                                    {% else %}
                                        <span class="badge bg-secondary">Inactive</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" title="View Analytics">
                                            <i class="fas fa-chart-line"></i>
                                        </button>
                                        <button class="btn btn-outline-warning" title="Toggle">
                                            <i class="fas fa-pause"></i>
                                        </button>
                                        <button class="btn btn-outline-danger" title="Delete">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

TRENDING_TEMPLATE = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trending Content - TikTok Social Listening</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { padding-top: 70px; background-color: #f8f9fa; }
        .navbar-brand { font-weight: 700; font-size: 1.5rem; }
        .card { border: none; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); }
        .post-card { transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .post-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12); }
        .hashtag { 
            display: inline-block; background: #e3f2fd; color: #1976d2; 
            padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.85rem; 
            margin: 0.125rem; text-decoration: none; transition: all 0.2s ease;
        }
        .hashtag:hover { background: #bbdefb; color: #1565c0; transform: scale(1.05); }
        .demo-badge {
            position: fixed; top: 15px; right: 15px; z-index: 9999;
            background: #ff0050; color: white; padding: 5px 10px; border-radius: 15px;
            font-size: 0.8rem; font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="demo-badge">🎬 DEMO MODE</div>

    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fab fa-tiktok me-2"></i>TikTok Social Listening
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('keywords') }}">Keywords</a>
                <a class="nav-link active" href="{{ url_for('trending') }}">Trending</a>
                <a class="nav-link" href="{{ url_for('content_ideas') }}">Content Ideas</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h2><i class="fas fa-fire me-2 text-danger"></i>Trending Content</h2>
        <p class="text-muted">Content ที่กำลัง viral และมี engagement สูงบน TikTok</p>

        <!-- Filters -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-filter me-2"></i>Filters</h5>
            </div>
            <div class="card-body">
                <form method="GET" class="row g-3">
                    <div class="col-md-3">
                        <input type="text" name="hashtag" class="form-control" placeholder="Hashtag" value="{{ current_hashtag }}">
                    </div>
                    <div class="col-md-3">
                        <select name="sort" class="form-select">
                            <option value="engagement" {% if current_sort == 'engagement' %}selected{% endif %}>Engagement</option>
                            <option value="likes" {% if current_sort == 'likes' %}selected{% endif %}>Likes</option>
                            <option value="views" {% if current_sort == 'views' %}selected{% endif %}>Views</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search me-1"></i>Apply
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Posts Grid -->
        <div class="row">
            {% for post in posts %}
            <div class="col-lg-6 mb-4">
                <div class="card post-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <strong class="text-primary">@{{ post.username }}</strong>
                                <span class="text-muted ms-2">({{ post.display_name }})</span>
                            </div>
                            <span class="badge bg-danger">VIRAL {{ "%.0f"|format(post.viral_score) }}%</span>
                        </div>

                        <p class="card-text">{{ post.description }}</p>

                        <!-- Hashtags -->
                        <div class="mb-3">
                            {% for hashtag in post.hashtags %}
                                <a href="{{ url_for('trending', hashtag=hashtag) }}" class="hashtag">#{{ hashtag }}</a>
                            {% endfor %}
                        </div>

                        <!-- Metrics -->
                        <div class="row text-center">
                            <div class="col-3">
                                <i class="fas fa-heart text-danger"></i><br>
                                <strong>{{ "{:,}".format(post.like_count) }}</strong><br>
                                <small class="text-muted">Likes</small>
                            </div>
                            <div class="col-3">
                                <i class="fas fa-comment text-primary"></i><br>
                                <strong>{{ "{:,}".format(post.comment_count) }}</strong><br>
                                <small class="text-muted">Comments</small>
                            </div>
                            <div class="col-3">
                                <i class="fas fa-share text-success"></i><br>
                                <strong>{{ "{:,}".format(post.share_count) }}</strong><br>
                                <small class="text-muted">Shares</small>
                            </div>
                            <div class="col-3">
                                <i class="fas fa-eye text-info"></i><br>
                                <strong>{{ "{:,}".format(post.view_count) }}</strong><br>
                                <small class="text-muted">Views</small>
                            </div>
                        </div>

                        <hr>

                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">{{ post.created_time.strftime('%d/%m/%Y %H:%M') }}</small>
                            <div>
                                <span class="badge bg-success">{{ "%.1f"|format(post.engagement_rate) }}% Engagement</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

CONTENT_IDEAS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Ideas - TikTok Social Listening</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { padding-top: 70px; background-color: #f8f9fa; }
        .navbar-brand { font-weight: 700; font-size: 1.5rem; }
        .card { border: none; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); }
        .idea-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border-radius: 16px; position: relative;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .idea-card:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); }
        .idea-score { 
            position: absolute; top: 1rem; right: 1rem; 
            background: rgba(255, 255, 255, 0.2); padding: 0.25rem 0.75rem; 
            border-radius: 12px; font-weight: 600; font-size: 0.85rem; 
        }
        .hashtag { 
            display: inline-block; background: rgba(255, 255, 255, 0.2); color: white; 
            padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.85rem; 
            margin: 0.125rem; text-decoration: none; 
        }
        .demo-badge {
            position: fixed; top: 15px; right: 15px; z-index: 9999;
            background: #ff0050; color: white; padding: 5px 10px; border-radius: 15px;
            font-size: 0.8rem; font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="demo-badge">🎬 DEMO MODE</div>

    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fab fa-tiktok me-2"></i>TikTok Social Listening
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('keywords') }}">Keywords</a>
                <a class="nav-link" href="{{ url_for('trending') }}">Trending</a>
                <a class="nav-link active" href="{{ url_for('content_ideas') }}">Content Ideas</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h2><i class="fas fa-lightbulb me-2 text-warning"></i>Content Ideas</h2>
        <p class="text-muted">AI-generated content suggestions based on trending data</p>

        <!-- Generate Button -->
        <div class="card mb-4">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h5 class="mb-1">Generate New Ideas</h5>
                        <p class="text-muted mb-0">สร้าง content ideas ใหม่จากข้อมูล trending ล่าสุด</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-primary" onclick="generateIdeas()">
                            <i class="fas fa-magic me-2"></i>Generate Ideas
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Ideas Grid -->
        <div class="row mb-4">
            {% for idea in ideas %}
            <div class="col-lg-4 mb-4">
                <div class="card idea-card h-100">
                    <div class="card-body">
                        <div class="idea-score">{{ "%.0f"|format(idea.confidence_score) }}%</div>

                        <div class="mb-2">
                            {% if idea.type == 'trending_hashtag' %}
                                <span class="badge bg-danger">🔥 Trending</span>
                            {% elif idea.type == 'pattern_based' %}
                                <span class="badge bg-primary">📊 Pattern</span>
                            {% else %}
                                <span class="badge bg-info">⏰ Timing</span>
                            {% endif %}
                        </div>

                        <h6 class="card-title mb-3">{{ idea.title }}</h6>
                        <p class="card-text mb-3" style="color: rgba(255,255,255,0.9);">{{ idea.description }}</p>

                        {% if idea.hashtags %}
                        <div class="mb-3">
                            {% for hashtag in idea.hashtags %}
                                <span class="hashtag">#{{ hashtag }}</span>
                            {% endfor %}
                        </div>
                        {% endif %}

                        <div class="mb-3">
                            <small style="color: rgba(255,255,255,0.8);">Predicted Engagement:</small>
                            <div class="progress mt-1" style="height: 6px; background: rgba(255,255,255,0.2);">
                                <div class="progress-bar bg-light" style="width: 75%"></div>
                            </div>
                            <small style="color: rgba(255,255,255,0.8);">{{ "{:,}".format(idea.predicted_engagement) }} engagements</small>
                        </div>

                        <div class="d-grid">
                            <button class="btn btn-light btn-sm" onclick="useIdea('{{ idea.title }}')">
                                <i class="fas fa-check me-1"></i>Use This Idea
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- High Engagement Posts -->
        <h4 class="mb-3"><i class="fas fa-trophy me-2 text-success"></i>High Performing Content</h4>
        <div class="row">
            {% for post in high_engagement_posts %}
            <div class="col-lg-4 mb-3">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <strong class="text-primary">@{{ post.username }}</strong>
                            <span class="badge bg-success">{{ "%.1f"|format(post.engagement_rate) }}%</span>
                        </div>
                        <p class="card-text">{{ post.description }}</p>
                        <div class="row text-center">
                            <div class="col-4">
                                <small class="text-muted">Likes</small><br>
                                <strong>{{ "{:,}".format(post.like_count) }}</strong>
                            </div>
                            <div class="col-4">
                                <small class="text-muted">Comments</small><br>
                                <strong>{{ "{:,}".format(post.comment_count) }}</strong>
                            </div>
                            <div class="col-4">
                                <small class="text-muted">Shares</small><br>
                                <strong>{{ "{:,}".format(post.share_count) }}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function generateIdeas() {
            alert('🎉 สร้าง Content Ideas ใหม่แล้ว 3 รายการ!\n\nในระบบจริงจะใช้ AI วิเคราะห์จากข้อมูล TikTok Research API');
        }

        function useIdea(title) {
            alert('✅ บันทึก "' + title + '" ลงใน Content Plan แล้ว!\n\nในระบบจริงจะมีการ integrate กับ content management tools');
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Starting TikTok Social Listening Demo App...")
    print("📱 Open: http://localhost:5000")
    print("🎬 Ready for demo video recording!")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=8080)