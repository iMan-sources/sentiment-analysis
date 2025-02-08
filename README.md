# Sentiment Analysis Dashboard

Hệ thống phân tích cảm xúc (sentiment) cho các đánh giá sách với dashboard theo dõi hiệu suất model.

## Tính năng chính

- Phân tích sentiment tự động cho các đánh giá sách
- Dashboard theo dõi hiệu suất model theo thời gian thực
- Cho phép người dùng sửa sentiment để cải thiện độ chính xác
- Thu thập dữ liệu training từ các corrections
- WebSocket để cập nhật realtime

## Yêu cầu hệ thống

- Docker Desktop (Windows/Mac) hoặc Docker Engine (Linux)
- Git

## Cài đặt và Chạy

1. Clone repository:

```bash
git clone <repository-url>
cd <project-folder>
```

2. (Tùy chọn) Tạo file `.env` để cấu hình:

```env
MYSQL_USER=root
MYSQL_PASSWORD=anhle3720
MYSQL_DATABASE=bookstore
```

3. Build và chạy với Docker:

```bash
docker-compose up --build
```

Sau khi chạy:

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- MySQL: localhost:3307

## Kiến trúc hệ thống

### Backend (FastAPI + MySQL)

- FastAPI application
- MySQL database
- WebSocket cho realtime updates
- DistilBERT model cho sentiment analysis

### Frontend (React)

- Dashboard hiển thị metrics
- Material UI cho giao diện
- WebSocket client

## Docker Services

```yaml
services:
  web: # Backend API (FastAPI)
    - Port: 8000
    - Dependencies: Python, PyTorch, etc.

  frontend: # React Dashboard
    - Port: 3000
    - Dependencies: Node.js, npm packages

  db: # MySQL Database
    - Port: 3307
    - Volumes: mysql_data, init scripts
```

## API Endpoints

- `GET /books`: Danh sách sách
- `GET /books/{id}`: Chi tiết sách
- `GET /books/{id}/comments`: Comments của sách
- `POST /comments`: Thêm comment mới
- `GET /api/dashboard/metrics`: Metrics của model

## Development

1. Chạy development mode:

```bash
docker-compose up --build
```

2. Xem logs:

```bash
docker-compose logs -f
```

3. Insert dữ liệu mẫu:

```bash
# Lấy container ID của MySQL
docker ps

# Truy cập MySQL
docker exec -it <container_id> mysql -u root -p
# Nhập password: anhle3720

# Trong MySQL shell
USE bookstore;

# Insert sample books data
INSERT INTO books VALUES
('1','The Great Gatsby','F. Scott Fitzgerald',15.99,'A story of decadence and excess...','/static/book_covers/book_1.png'),
('2','To Kill a Mockingbird','Harper Lee',12.99,'A classic of modern American literature...','/static/book_covers/book_2.png'),
('3','The Design of Books','Debbie Berne',24.99,'An Explainer for Authors, Editors, Agents, and Other Curious Readers','/static/book_covers/book_3.png'),
('4','A Million To One','Robert C. Martin',29.99,'A Handbook of Agile Software Craftsmanship','/static/book_covers/book_4.png'),
('5','Educated','Andrew Hunt',34.99,'Your journey to mastery in software development','/static/book_covers/book_5.png'),
('6','The Lord Of Ring','George Orwell',14.99,'A dystopian social science fiction novel','/static/book_covers/book_6.png'),
('7','The Search For Wondla','Jane Austen',12.99,'A romantic novel of manners','/static/book_covers/book_7.png'),
('8','Princess Freedom','J.R.R. Tolkien',19.99,'A fantasy novel and children\'s book','/static/book_covers/book_8.png'),
('9','Harry Porter','J.D. Salinger',16.99,'A story of teenage alienation and loss of innocence','/static/book_covers/book_9.png'),
('10','The Big Deal','William Golding',13.99,'A novel about the dark side of human nature','/static/book_covers/book_10.png');

# Kiểm tra dữ liệu
SELECT * FROM books;
```

## Troubleshooting

1. Port conflicts:

- Đảm bảo ports 8000, 3000, và 3307 không bị sử dụng
- Hoặc thay đổi port mapping trong docker-compose.yml
