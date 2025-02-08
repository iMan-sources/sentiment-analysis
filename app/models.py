from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from pydantic import BaseModel
from typing import List, Optional

# SQLAlchemy Models
class BookDB(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    author = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(10000))
    imageUrl = Column(String(500))
    comments = relationship("CommentDB", back_populates="book", cascade="all, delete-orphan")

class CommentDB(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True)
    content = Column(String(10000))
    userId = Column(String(36))
    userName = Column(String(255))
    sentiment = Column(String(20))
    timestamp = Column(DateTime)
    book_id = Column(String(20), ForeignKey("books.id"))
    
    book = relationship("BookDB", back_populates="comments")
    replies = relationship("ReplyDB", back_populates="comment", cascade="all, delete-orphan")

class ReplyDB(Base):
    __tablename__ = "replies"

    id = Column(String(36), primary_key=True)
    adminId = Column(String(36), nullable=False)
    adminName = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    comment_id = Column(String(36), ForeignKey("comments.id"))
    comment = relationship("CommentDB", back_populates="replies")

# Pydantic Models for API
class Reply(BaseModel):
    id: str
    adminId: str
    adminName: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class Comment(BaseModel):
    id: str
    userId: str
    userName: str
    content: str
    timestamp: datetime
    sentiment: Optional[str] = None
    replies: List[Reply] = []

    class Config:
        from_attributes = True

class Book(BaseModel):
    id: str
    title: str
    author: str
    price: float
    description: str
    imageUrl: str
    comments: List[Comment] = []

    class Config:
        from_attributes = True

class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Performance metrics
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float)
    avg_response_time = Column(Float)  # milliseconds
    
    # Sentiment distribution
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    
    # Confidence metrics
    avg_confidence = Column(Float)
    min_confidence = Column(Float)
    max_confidence = Column(Float)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    
    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    text = Column(String(1000))
    predicted_sentiment = Column(String(20))
    confidence_score = Column(Float)
    response_time = Column(Float)  # milliseconds
    comment_id = Column(String(36), ForeignKey("comments.id")) 