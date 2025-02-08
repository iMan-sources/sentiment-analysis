# Sentiment Analysis Dashboard

Hệ thống phân tích cảm xúc (sentiment) cho các đánh giá sách với dashboard theo dõi hiệu suất model.

## Tóm tắt

Ngày nay, việc hiểu được cảm xúc của khách hàng về sản phẩm và dịch vụ là vô cùng quan trọng. Dự án này xây dựng một hệ thống phân tích cảm xúc tự động dành cho các đánh giá sách, giúp theo dõi hiệu suất của mô hình phân tích và cải thiện độ chính xác theo thời gian. Hệ thống cung cấp một dashboard trực quan để theo dõi hiệu suất, cho phép người dùng sửa các phân loại cảm xúc sai, và sử dụng các sửa đổi này để liên tục cải thiện mô hình. Việc cập nhật theo thời gian thực thông qua WebSocket giúp người dùng luôn nắm bắt được thông tin mới nhất.

## Giới thiệu

Các đánh giá sách chứa đựng lượng lớn thông tin về cảm xúc của độc giả đối với các tác phẩm. Việc phân tích thủ công khối lượng lớn đánh giá này là một nhiệm vụ tốn thời gian và công sức. Dự án "Sentiment Analysis Dashboard" được phát triển để tự động hóa quá trình này, sử dụng các kỹ thuật Machine Learning và Xử lý ngôn ngữ tự nhiên (NLP) để phân loại cảm xúc (tích cực, tiêu cực, trung tính) của các đánh giá. Dashboard theo dõi hiệu suất giúp đánh giá và cải thiện độ chính xác của mô hình theo thời gian.

### Mục tiêu

Mục tiêu chính của dự án là xây dựng một hệ thống phân tích cảm xúc tự động và trực quan cho các đánh giá sách, cho phép:

*   Phân tích cảm xúc tự động và chính xác.
*   Theo dõi hiệu suất mô hình theo thời gian thực thông qua dashboard.
*   Cải thiện độ chính xác của mô hình bằng cách thu thập dữ liệu training từ các sửa đổi của người dùng.
*   Cung cấp cập nhật theo thời gian thực thông qua WebSocket.

### Phạm vi dự án

Dự án này có phạm vi ứng dụng rộng rãi, không giới hạn trong một tổ chức cụ thể. Hệ thống có thể được sử dụng bởi bất kỳ ai quan tâm đến việc phân tích cảm xúc của các đánh giá sách, bao gồm:

*   Nhà xuất bản: Để đánh giá phản hồi của độc giả về sách mới.
*   Tác giả: Để hiểu rõ hơn về cách độc giả cảm nhận về tác phẩm của họ.
*   Các trang web bán sách trực tuyến: Để cải thiện hệ thống đề xuất và cá nhân hóa trải nghiệm người dùng.
*   Các nhà nghiên cứu thị trường: Để thu thập thông tin về xu hướng đọc sách và sở thích của độc giả.

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

2. Download Model

```bash
# Tạo model
mkdir model
cd model
# Download model từ link: https://drive.google.com/drive/folders/1JZb9AWXe_6KxRMv-arAe8zBl1IVKrLDa?usp=sharing
# Giải nén file và đặt tên thư mục là `my-imdb-sentiment-model`
# Đặt thư mục vừa giải nén vào thư mục `model/`
```

3. (Tùy chọn) Tạo file `.env` để cấu hình:

```env
MYSQL_USER=root
MYSQL_PASSWORD=anhle3720
MYSQL_DATABASE=bookstore
```

4. Build và chạy với Docker:

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
