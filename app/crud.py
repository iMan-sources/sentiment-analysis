from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import uuid
from datetime import datetime
from . import models
from .sentiment_service import SentimentAnalyzer
from typing import Dict, List
from . import crud, models, database
from .database import engine, get_db
sentiment_analyzer = SentimentAnalyzer()

def get_books(db: Session):
    return db.query(models.BookDB).all()

def get_book(db: Session, book_id: str):
    book = db.query(models.BookDB).filter(models.BookDB.id == book_id).first()
    if book:
        book.comments.sort(key=lambda x: x.timestamp, reverse=True)
    return book

def get_book_comments(db: Session, book_id: str):
    return db.query(models.CommentDB)\
        .filter(models.CommentDB.book_id == book_id)\
        .order_by(desc(models.CommentDB.timestamp))\
        .all()

def get_comment_replies(db: Session, comment_id: str):
    return db.query(models.ReplyDB).filter(models.ReplyDB.comment_id == comment_id).all()

async def create_comment(db: Session, book_id: str, user_id: str, user_name: str, content: str):
    try:
        # Tạo comment trước với sentiment là null
        comment = models.CommentDB(
            id=str(uuid.uuid4()),
            userId=user_id,
            userName=user_name,
            content=content,
            timestamp=datetime.utcnow(),
            sentiment=None,
            book_id=book_id
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        comment_id = str(comment.id)
        # Phân tích sentiment bất đồng bộ và broadcast kết quả
        sentiment = await sentiment_analyzer.analyze_and_broadcast(content, comment.id, db=db)
        
        # Cập nhật sentiment vào database
        if sentiment:

            comment = db.query(models.CommentDB).filter(models.CommentDB.id == comment_id).first()
            if comment:
                comment.sentiment = sentiment
                db.commit()
                db.refresh(comment)
        
        return comment
    except Exception as e:
        print(f"Error creating comment: {e}")
        db.rollback()
        raise

def create_reply(db: Session, comment_id: str, admin_id: str, admin_name: str, content: str):
    reply = models.ReplyDB(
        id=str(uuid.uuid4()),
        adminId=admin_id,
        adminName=admin_name,
        content=content,
        timestamp=datetime.utcnow(),
        comment_id=comment_id
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply

def get_sentiment_stats(db: Session, book_id: str = None):
    query = db.query(models.CommentDB)
    if book_id:
        query = query.filter(models.CommentDB.book_id == book_id)
    
    total = query.count()
    positive = query.filter(models.CommentDB.sentiment == "positive").count()
    negative = query.filter(models.CommentDB.sentiment == "negative").count()
    
    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_percentage": (positive/total * 100) if total > 0 else 0,
        "negative_percentage": (negative/total * 100) if total > 0 else 0
    }

def update_comment_sentiment(db: Session, comment_id: str, sentiment: str):
    comment = db.query(models.CommentDB).filter(models.CommentDB.id == comment_id).first()
    if comment:
        comment.sentiment = sentiment
        db.commit()
        db.refresh(comment)
    return comment

def get_total_predictions(db: Session) -> int:
    try:
        return db.query(models.Comment).filter(
            models.Comment.sentiment.isnot(None)
        ).count()
    except Exception as e:
        print(f"Error getting total predictions: {e}")
        return 0

def get_average_response_time(db: Session) -> float:
    try:
        result = db.query(func.avg(models.Comment.response_time)).filter(
            models.Comment.response_time.isnot(None)
        ).scalar()
        return float(result) if result else 0.0
    except Exception as e:
        print(f"Error getting average response time: {e}")
        return 0.0

def get_sentiment_count(db: Session, sentiment_type: str) -> int:
    try:
        return db.query(func.count(models.Comment.id)).filter(
            models.Comment.sentiment == sentiment_type
        ).scalar() or 0
    except Exception as e:
        print(f"Error getting {sentiment_type} count: {e}")
        return 0

def get_sentiment_percentage(db: Session, sentiment_type: str) -> float:
    try:
        total = get_total_predictions(db)
        if total == 0:
            return 0.0
            
        count = get_sentiment_count(db, sentiment_type)
        return (count / total) * 100
    except Exception as e:
        print(f"Error calculating sentiment percentage: {e}")
        return 0.0

def get_prediction_counts(db: Session) -> Dict[str, int]:
    results = db.query(
        models.CommentDB.sentiment,
        func.count(models.CommentDB.id)
    ).filter(
        models.CommentDB.sentiment.isnot(None)
    ).group_by(
        models.CommentDB.sentiment
    ).all()
    
    return {sentiment: count for sentiment, count in results}

def get_correct_predictions(db: Session) -> int:
    return db.query(models.Comment).filter(
        models.Comment.sentiment.isnot(None),
        models.Comment.is_correct == True
    ).count()

def get_correction_rate(db: Session) -> float:
    total = db.query(models.Comment).filter(
        models.Comment.sentiment.isnot(None)
    ).count()
    corrected = db.query(models.Comment).filter(
        models.Comment.sentiment.isnot(None),
        models.Comment.is_corrected == True
    ).count()
    return corrected / total if total > 0 else 0

def get_sentiment_distribution(db: Session) -> Dict[str, int]:
    results = db.query(
        models.Comment.sentiment,
        func.count(models.Comment.id)
    ).filter(
        models.Comment.sentiment.isnot(None)
    ).group_by(
        models.Comment.sentiment
    ).all()
    return dict(results)

def get_recent_corrections(db: Session) -> List[Dict]:
    corrections = db.query(models.Comment).filter(
        models.Comment.is_corrected == True
    ).order_by(
        models.Comment.created_at.desc()
    ).limit(10).all()
    
    return [{
        "timestamp": str(c.created_at),
        "content": c.content,
        "prediction": c.original_sentiment,
        "corrected_sentiment": c.sentiment
    } for c in corrections]

def get_comment(db: Session, comment_id: str):
    """Get a comment by ID"""
    try:
        return db.query(models.Comment).filter(
            models.Comment.id == comment_id
        ).first()
    except Exception as e:
        print(f"Error getting comment: {e}")
        return None 