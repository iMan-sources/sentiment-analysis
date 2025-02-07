from transformers import DistilBertConfig, AutoModelForSequenceClassification, AutoTokenizer, pipeline
from typing import Dict
import os
from .websocket_manager import manager
import time
from .metrics_service import MetricsService
from sqlalchemy.orm import Session
from . import crud, models, database
from .database import engine, get_db
class SentimentAnalyzer:
    # Model loading

    def __init__(self, model_path: str = "model/my-imdb-sentiment-model/checkpoint-2343", db = None):
        
        try:
            if not os.path.exists(model_path):
                raise ValueError(f"Model path does not exist: {model_path}")
                
            print("Loading model from:", model_path)
            
            config = DistilBertConfig.from_pretrained(
                "distilbert-base-uncased",
                num_labels=2
            )
            
            model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                config=config,
                local_files_only=True,
                ignore_mismatched_sizes=True
            )
            
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            self.model = pipeline(
                task="sentiment-analysis",
                model=model,
                tokenizer=tokenizer
            )
            print("Model loaded successfully!")

        except Exception as e:
            print(f"Error loading model: {str(e)}")
            # Fallback to simple sentiment analysis
            self.model = None
            
    async def analyze_and_broadcast(self, text: str, comment_id: str, db: Session = None):
        try:
            start_time = time.time()
            metrics_service = MetricsService(db)  # Truyền session trực tiếp
            # Phân tích sentiment
            result = self.analyze_text(text) if self.model else {'sentiment': 'positive', 'score': 0.5}
            sentiment = result['sentiment'].lower()
            
            print(f"Analyzed sentiment for comment {comment_id}: {sentiment}")
            
            # Log prediction nếu có metrics_service
            if metrics_service is not None:
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                metrics_service.log_prediction(
                    text=text,
                    prediction=sentiment,
                    confidence=float(result['score']),
                    response_time=response_time,
                    comment_id=comment_id
                )
                
                # Tính toán batch metrics mỗi giờ
                metrics_service.calculate_batch_metrics()
            
            # Broadcast kết quả qua WebSocket
            await manager.broadcast_sentiment_update(comment_id, sentiment)
            print(f"Broadcasted sentiment update for comment {comment_id}")
            
            return sentiment
        except Exception as e:
            print(f"Error in analyze_and_broadcast: {e}")
            return None

    def analyze(self, text: str) -> str:
        """Return simple sentiment analysis result"""
        try:
            if self.model is None:
                # Fallback simple analysis
                result = {'sentiment': 'positive' if len(text) % 2 == 0 else 'negative', 'score': 0.5}
            else:
                result = self.analyze_text(text)
            
            return result['sentiment'].lower()
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return "positive"  # Default fallback
    
    def analyze_text(self, text: str) -> Dict:
        """Detailed sentiment analysis with confidence"""
        result = self.model(text)[0]
        sentiment = 'POSITIVE' if result['label'] == 'LABEL_1' else 'NEGATIVE'
        
        if result['score'] > 0.9:
            confidence = 'Very High'
        elif result['score'] > 0.75:
            confidence = 'High'
        elif result['score'] > 0.6:
            confidence = 'Moderate'
        else:
            confidence = 'Low'
            
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': float(result['score'])
        } 

