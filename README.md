# Sentiment Analysis Dashboard

Hệ thống phân tích cảm xúc (sentiment) cho các đánh giá sách với dashboard theo dõi hiệu suất model.

## Tính năng chính

- Phân tích sentiment tự động cho các đánh giá sách
- Dashboard theo dõi hiệu suất model theo thời gian thực
- Cho phép người dùng sửa sentiment để cải thiện độ chính xác
- Thu thập dữ liệu training từ các corrections
- WebSocket để cập nhật realtime

## Kiến trúc hệ thống

### Backend (FastAPI)

- `app/main.py`: API endpoints và WebSocket handlers
- `app/sentiment_service.py`: Xử lý phân tích sentiment với DistilBERT
- `app/metrics_service.py`: Thu thập và tính toán metrics
- `app/models.py`: Database models (SQLAlchemy)
- `app/websocket_manager.py`: Quản lý WebSocket connections

### Frontend (React)

- `review-dashboard/`: Dashboard hiển thị metrics
- Material UI cho giao diện người dùng
- WebSocket client để cập nhật realtime

## Metrics được theo dõi

1. Model Performance

   - Accuracy
   - Tổng số predictions
   - Thời gian phản hồi trung bình

2. Sentiment Distribution

   - Tỷ lệ positive/negative
   - Phân phối theo thời gian

3. Recent Corrections
   - Timeline các corrections gần đây
   - Tracking sự thay đổi sentiment

## Cấu trúc Project

```
├── app/
│   ├── main.py              # FastAPI app & routes
│   ├── models.py            # Database models
│   ├── sentiment_service.py # Sentiment analysis
│   ├── metrics_service.py   # Performance tracking
│   ├── websocket_manager.py # WebSocket handler
│   └── database.py         # Database configuration
│
├── review-dashboard/
│   ├── src/
│   │   ├── components/     # React components
│   │   └── App.tsx        # Main app
│   └── package.json
│
├── model/                  # Pre-trained model
├── training_data/         # Correction data
├── requirements.txt
└── README.md
```

## Cài đặt

1. Backend

```bash
# Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

```bash
# Cài đặt dependencies
pip install -r requirements.txt
```

```bash
# Khởi động server
uvicorn app.main:app --reload
```

2. Frontend

```bash
cd review-dashboard
npm install
npm start
```

3. Model

```bash
# Tạo model
mkdir model
cd model
# Download model từ link: https://drive.google.com/drive/folders/1JZb9AWXe_6KxRMv-arAe8zBl1IVKrLDa?usp=sharing
# Giải nén file và đặt tên thư mục là `my-imdb-sentiment-model`
# Đặt thư mục vừa giải nén vào thư mục `model/`

# Cài đặt torch
pip3 install torch --index-url https://download.pytorch.org/whl/cpu
```

## Cấu hình

1. Database

   - SQLite cho development
   - MySQL/PostgreSQL cho production

2. Model

   - DistilBERT fine-tuned trên dữ liệu IMDB
   - Đường dẫn model: `model/my-imdb-sentiment-model/`

3. API

   - Development: http://localhost:8000
   - WebSocket: ws://localhost:8000/ws

4. Dashboard
   - http://localhost:3000/dashboard

## Cải thiện Model

1. Thu thập dữ liệu training

   - Corrections được lưu trong `training_data/`
   - Format: CSV với timestamp, text, predicted/correct sentiment

2. Retraining
   - Sử dụng dữ liệu corrections để fine-tune model
   - Theo dõi accuracy trên dashboard để quyết định thời điểm retrain

## License

MIT License
