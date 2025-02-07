from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import ModelMetrics, PredictionLog, CommentDB
import numpy as np
import logging
import csv
import os
from datetime import datetime
# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session object
        """
        self.db = db
        # Thư mục chứa dữ liệu training
        self.training_data_dir = "training_data"
        os.makedirs(self.training_data_dir, exist_ok=True)

    def _get_error_log_path(self) -> str:
        """Tạo đường dẫn file log theo tháng hiện tại"""
        current_month = datetime.utcnow().strftime('%Y%m')
        return os.path.join(self.training_data_dir, f"sentiment_errors_{current_month}.csv")

    def _ensure_error_log_exists(self, file_path: str):
        """Đảm bảo file log tồn tại với headers"""
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'text',
                    'predicted_sentiment',
                    'correct_sentiment',
                    'confidence_score',
                    'comment_id'
                ])
            logger.info(f"Created new error log file: {file_path}")

    def _update_or_append_log(self, file_path: str, new_row: list, comment_id: str):
        """Cập nhật hoặc thêm mới dữ liệu vào file log"""
        try:
            # Đọc tất cả dữ liệu hiện tại
            rows = []
            found = False
            
            if os.path.exists(file_path):
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Lưu header
                    for row in reader:
                        if row[-1] == comment_id:  # comment_id là cột cuối
                            rows.append(new_row)  # Thay thế bằng dữ liệu mới
                            found = True
                        else:
                            rows.append(row)  # Giữ nguyên dữ liệu cũ
            
            # Nếu comment_id chưa tồn tại, thêm mới
            if not found:
                rows.append(new_row)
            
            # Ghi lại toàn bộ dữ liệu
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'text', 'predicted_sentiment', 
                               'correct_sentiment', 'confidence_score', 'comment_id'])  # Ghi header
                writer.writerows(rows)  # Ghi dữ liệu
                
            logger.info(f"{'Updated' if found else 'Added new'} entry for comment {comment_id}")
            
        except Exception as e:
            logger.error(f"Error updating log file: {str(e)}")
            raise

    def log_sentiment_correction(self, comment_id: str, correct_sentiment: str):
        """Log khi người dùng sửa sentiment"""
        try:
            # Lấy prediction gần nhất từ database
            prediction = self.db.query(PredictionLog).filter(
                PredictionLog.comment_id == comment_id
            ).order_by(
                PredictionLog.timestamp.desc()
            ).first()

            if not prediction:
                logger.error(f"No prediction found for comment {comment_id}")
                return

            # Chỉ log nếu dự đoán sai
            if prediction.predicted_sentiment.lower() != correct_sentiment.lower():
                error_log_path = self._get_error_log_path()
                self._ensure_error_log_exists(error_log_path)

                # Chuẩn bị dữ liệu mới
                new_row = [
                    datetime.utcnow().isoformat(),
                    prediction.text,
                    prediction.predicted_sentiment,
                    correct_sentiment,
                    prediction.confidence_score,
                    comment_id
                ]

                # Cập nhật hoặc thêm mới vào file log
                self._update_or_append_log(error_log_path, new_row, comment_id)

        except Exception as e:
            logger.error(f"Error logging sentiment correction: {str(e)}")
            raise

    def get_training_data_stats(self):
        """Lấy thống kê về dữ liệu training"""
        try:
            error_log_path = self._get_error_log_path()
            if not os.path.exists(error_log_path):
                return {
                    "total_errors": 0,
                    "current_month": datetime.utcnow().strftime('%Y-%m'),
                    "file_path": error_log_path
                }

            with open(error_log_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                errors = list(reader)

            return {
                "total_errors": len(errors),
                "current_month": datetime.utcnow().strftime('%Y-%m'),
                "file_path": error_log_path
            }

        except Exception as e:
            logger.error(f"Error getting training data stats: {str(e)}")
            return None

    def log_prediction(self, text: str, prediction: str, confidence: float, 
                      response_time: float, comment_id: str):
        """Log một prediction riêng lẻ vào database
        
        Args:
            text: Nội dung text cần phân tích
            prediction: Kết quả dự đoán (positive/negative)
            confidence: Độ tin cậy của prediction (0-1)
            response_time: Thời gian phản hồi (ms)
            comment_id: ID của comment
        """
        try:
            # Validate inputs
            if not text or not prediction or not comment_id:
                raise ValueError("Text, prediction và comment_id không được để trống")
            if not 0 <= confidence <= 1:
                raise ValueError("Confidence phải nằm trong khoảng 0-1")
            if response_time < 0:
                raise ValueError("Response time không được âm")

            # Create log entry
            log = PredictionLog(
                id=str(uuid.uuid4()),
                text=text,
                predicted_sentiment=prediction.lower(),
                confidence_score=confidence,
                response_time=response_time,
                comment_id=comment_id,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Creating prediction log: comment_id={comment_id}, "
                       f"prediction={prediction}, confidence={confidence:.2f}, "
                       f"response_time={response_time:.2f}ms")
            
            self.db.add(log)
            self.db.commit()
            logger.info("Successfully committed to database")
            
        except Exception as e:
            logger.error(f"Error logging prediction - comment_id={comment_id}: {str(e)}")
            self.db.rollback()
            raise

    def calculate_batch_metrics(self, time_window: timedelta = timedelta(hours=1)):
        """Tính toán metrics cho một khoảng thời gian"""
        try:
            since = datetime.utcnow() - time_window
            
            # Lấy predictions trong time window
            predictions = self.db.query(PredictionLog).filter(
                PredictionLog.timestamp >= since
            ).all()
            
            logger.info(f"Found {len(predictions)} predictions in time window")
            
            if not predictions:
                logger.info("No predictions found, creating default metrics")
                metrics = ModelMetrics(
                    id=str(uuid.uuid4()),
                    total_predictions=0,
                    positive_count=0,
                    negative_count=0,
                    accuracy=0.0,
                    avg_confidence=0.0,
                    min_confidence=0.0,
                    max_confidence=0.0,
                    avg_response_time=0.0
                )
                self.db.add(metrics)
                self.db.commit()
                return metrics
                
            # Tính toán basic metrics
            total = len(predictions)
            confidence_scores = [p.confidence_score for p in predictions]
            response_times = [p.response_time for p in predictions]
            positive_count = len([p for p in predictions if p.predicted_sentiment == "positive"])
            
            # Tính accuracy bằng cách so sánh với sentiment đã được xác nhận
            # Join PredictionLog với Comment để lấy các cặp prediction-confirmation
            prediction_results = (
                self.db.query(PredictionLog, CommentDB)
                .join(
                    CommentDB,
                    PredictionLog.comment_id == CommentDB.id
                )
                .filter(
                    PredictionLog.timestamp >= since,
                    CommentDB.sentiment.isnot(None)  # Chỉ lấy những comment đã được xác nhận
                )
                .all()
            )
            
            logger.info(f"Found {len(prediction_results)} predictions with confirmed sentiments")
            
            # Đếm số prediction đúng
            correct_predictions = sum(
                1 for pred, comment in prediction_results
                if pred.predicted_sentiment.lower() == comment.sentiment.lower()
            )
            
            # Tính accuracy
            total_confirmed = len(prediction_results)
            accuracy = float(correct_predictions / total_confirmed) if total_confirmed > 0 else 0.0
            
            logger.info(f"""
                Accuracy calculation:
                Total predictions with confirmation: {total_confirmed}
                Correct predictions: {correct_predictions}
                Accuracy: {accuracy:.2%}
            """)
            
            metrics = ModelMetrics(
                id=str(uuid.uuid4()),
                total_predictions=total,
                positive_count=positive_count,
                negative_count=total - positive_count,
                correct_predictions=correct_predictions,
                accuracy=accuracy,
                avg_confidence=float(np.mean(confidence_scores)),
                min_confidence=float(min(confidence_scores)),
                max_confidence=float(max(confidence_scores)),
                avg_response_time=float(np.mean(response_times))
            )
            
            self.db.add(metrics)
            self.db.commit()
            logger.info(f"Saved new metrics with accuracy {accuracy:.2%}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating batch metrics: {e}")
            self.db.rollback()
            return None

    def get_dashboard_metrics(self):
        """Lấy metrics cho dashboard"""
        try:
            # Tạo metrics mới nếu chưa có
            latest_metrics = self.db.query(ModelMetrics).order_by(
                ModelMetrics.timestamp.desc()
            ).first()
            
            # Log metrics object an toàn hơn
            if latest_metrics:
                logger.info("Latest metrics from database: %s", {
                    'id': latest_metrics.id,
                    'timestamp': latest_metrics.timestamp,
                    'total_predictions': latest_metrics.total_predictions,
                    'accuracy': latest_metrics.accuracy,
                    'avg_response_time': latest_metrics.avg_response_time
                })
            else:
                logger.info("No metrics found in database")
            
            if not latest_metrics:
                logger.info("Calculating new batch metrics")
                latest_metrics = self.calculate_batch_metrics()
                
            # Lấy các corrections gần đây
            recent_corrections = (
                self.db.query(CommentDB)
                .filter(CommentDB.sentiment != None)
                .order_by(CommentDB.timestamp.desc())
                .limit(10)
                .all()
            )
            
            logger.info(f"Found {len(recent_corrections)} recent corrections")
            
            # Tính toán phân phối sentiment
            total_predictions = latest_metrics.total_predictions or 1
            positive_percentage = (latest_metrics.positive_count / total_predictions * 100) if total_predictions > 0 else 0
            negative_percentage = (latest_metrics.negative_count / total_predictions * 100) if total_predictions > 0 else 0
            
            response_data = {
                "model_performance": {
                    "accuracy": latest_metrics.accuracy or 0.0,
                    "total_predictions": latest_metrics.total_predictions or 0,
                    "avg_response_time": f"{latest_metrics.avg_response_time:.2f}ms" if latest_metrics.avg_response_time else "0.00ms",
                },
                "sentiment_distribution": {
                    "positive": latest_metrics.positive_count or 0,
                    "negative": latest_metrics.negative_count or 0,
                    "positive_percentage": positive_percentage,
                    "negative_percentage": negative_percentage
                },
                "recent_corrections": [{
                    "content": comment.content,
                    "corrected_sentiment": comment.sentiment,
                    "timestamp": comment.timestamp.isoformat()
                } for comment in recent_corrections]
            }
            
            # Log response data an toàn hơn
            logger.info("Returning dashboard data: %s", response_data)
            return response_data
            
        except Exception as e:
            logger.error("Error getting dashboard metrics: %s", str(e))
            return None 

    def __del__(self):
        """Cleanup database session when object is destroyed"""
        if hasattr(self, 'db'):
            self.db.close() 