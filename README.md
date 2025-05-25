# TikTok Social Listening Tool

เครื่องมือสำหรับ Social Listening จาก TikTok เพื่อวิเคราะห์ trends และสร้าง content ideas

## คุณสมบัติ

- 📊 Dashboard แสดงภาพรวมข้อมูล
- 🔍 ติดตาม keywords และเก็บข้อมูลอัตโนมัติ
- 🔥 วิเคราะห์ trending content และ hashtags
- 💡 สร้าง content ideas จากข้อมูลที่วิเคราะห์
- 📈 Analytics และ reporting ครบครัน
- 📥 Export ข้อมูลในรูปแบบ CSV, JSON, Excel

## การติดตั้ง

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd tiktok-social-listening
```

### 2. สร้าง Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup MySQL Database

```sql
CREATE DATABASE tiktok_social_listening CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Configuration

1. Copy `.env.example` เป็น `.env`
2. แก้ไขค่าต่างๆ ใน `.env`:

```bash
cp .env.example .env
```

แก้ไขไฟล์ `.env`:
```
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DB=tiktok_social_listening

TIKTOK_ACCESS_TOKEN=your_token_here
# ... ค่าอื่นๆ
```

### 6. Initialize Database

```bash
flask init-db
```

### 7. รัน Application

```bash
python app.py
```

เปิดเบราว์เซอร์ไปที่: `http://localhost:5000`

## การตั้งค่า TikTok API

### 1. สมัคร TikTok for Developers

1. ไปที่ https://developers.tiktok.com/
2. สร้างแอปพลิเคชัน
3. สมัครใช้ Research API

### 2. ได้รับ API Credentials

หลังจากอนุมัติแล้ว จะได้:
- Client Key
- Client Secret  
- Access Token

### 3. ใส่ในไฟล์ .env

```
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_ACCESS_TOKEN=your_access_token
```

## การใช้งาน

### 1. เพิ่ม Keywords

1. ไปที่หน้า Keywords
2. กดปุ่ม "Add Keyword"
3. ใส่ keyword ที่ต้องการติดตาม
4. ระบุ category และ priority

### 2. เก็บข้อมูล

ระบบจะเก็บข้อมูลอัตโนมัติทุก 1 ชั่วโมง หรือสามารถเก็บด้วยตนเองได้:

```bash
flask collect-data
```

### 3. ดู Analytics

- **Dashboard**: ภาพรวมข้อมูลทั้งหมด
- **Trending**: Content ที่กำลัง viral
- **Content Ideas**: แนะนำ content ที่น่าสนใจ

### 4. Export ข้อมูล

ไปที่ Dashboard → Export Data → เลือกรูปแบบ (CSV/JSON/Excel)

## Commands ที่มีประโยชน์

```bash
# Initialize database
flask init-db

# Collect data manually
flask collect-data

# Run in production mode
FLASK_CONFIG=production python app.py
```

## การ Deploy

### 1. Production Settings

สร้างไฟล์ `.env.production`:

```
FLASK_CONFIG=production
SECRET_KEY=super-secure-secret-key
DEBUG=False
MYSQL_HOST=production_db_host
# ... ค่าอื่นๆ
```

### 2. Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 3. Using Docker

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

## โครงสร้างโปรเจค

```
tiktok-social-listening/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Dependencies
├── .env.example         # Environment variables template
├── models/
│   ├── __init__.py
│   └── models.py        # Database models
├── routes/
│   ├── __init__.py
│   ├── main.py          # Main routes
│   └── api.py           # API routes
├── services/
│   ├── __init__.py
│   ├── tiktok_collector.py  # TikTok data collection
│   └── analytics.py     # Analytics functions
├── static/
│   ├── css/style.css    # Custom CSS
│   └── js/main.js       # Custom JavaScript
├── templates/
│   ├── base.html        # Base template
│   ├── dashboard.html   # Dashboard page
│   ├── keywords.html    # Keywords management
│   ├── trending.html    # Trending content
│   └── content_ideas.html # Content ideas
└── utils/
    └── helpers.py       # Helper functions
```

## การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อ Database

```bash
# ตรวจสอบการเชื่อมต่อ MySQL
mysql -u username -p -h localhost

# ตรวจสอบว่าสร้าง database แล้ว
SHOW DATABASES;
```

### ปัญหา TikTok API

1. ตรวจสอบว่า access token ยังใช้งานได้
2. ตรวจสอบ rate limits
3. ดู logs ใน console

### ปัญหา Performance

1. เพิ่ม database indexing
2. ลด frequency ของการเก็บข้อมูล
3. ใช้ caching

## การพัฒนาต่อ

### เพิ่มฟีเจอร์ใหม่

1. Sentiment Analysis
2. Image/Video Analysis
3. Competitor Tracking
4. Real-time Alerts
5. Advanced ML Predictions

### การปรับปรุง

1. เพิ่ม unit tests
2. ปรับปรุง UI/UX
3. เพิ่ม API endpoints
4. เพิ่ม caching layer

## Support

หากมีปัญหาหรือข้อสงสัย กรุณา:

1. ตรวจสอบ logs ใน console
2. ดูในไฟล์ README นี้
3. สร้าง issue ใน repository

## License

MIT License