from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app import   crud
import asyncio
from starlette.websockets import WebSocketState
from app.database import get_db
from app.models import CommentDB, BookDB
from app.metrics_service import MetricsService

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.sentiment_stats = {"positive": 0, "negative": 0}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        async with self.lock:
            self.active_connections.append(websocket)
            print(f"Client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                print(f"Client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if message["type"] == "new_comment" and message["data"]["sentiment"]:
            self.update_stats(message["data"]["sentiment"])
            # Gửi stats sau khi cập nhật
            stats_message = {
                "type": "stats",
                "data": {
                    "positive": self.sentiment_stats["positive"],
                    "negative": self.sentiment_stats["negative"],
                    "total": sum(self.sentiment_stats.values()),
                    "positive_percentage": (self.sentiment_stats["positive"] / sum(self.sentiment_stats.values()) * 100) if sum(self.sentiment_stats.values()) > 0 else 0,
                    "negative_percentage": (self.sentiment_stats["negative"] / sum(self.sentiment_stats.values()) * 100) if sum(self.sentiment_stats.values()) > 0 else 0
                }
            }
            # Gửi một lần duy nhất cho mỗi kết nối
            for connection in self.active_connections:
                await connection.send_json(message)  # Gửi comment
                await connection.send_json(stats_message)  # Gửi stats
        else:
            # Gửi message khác
            for connection in self.active_connections:
                await connection.send_json(message)

    def update_stats(self, sentiment: str):
        if sentiment in self.sentiment_stats:
            self.sentiment_stats[sentiment] += 1

    async def send_stats(self, websocket: WebSocket):
        await websocket.send_json({
            "type": "stats",
            "data": self.sentiment_stats
        })

    async def broadcast_book_stats(self, db: Session):
        books = crud.get_books(db)
        book_stats = []
        
        for book in books:
            stats = crud.get_sentiment_stats(db, book.id)
            book_stats.append({
                "id": book.id,
                "title": book.title,
                "stats": stats
            })
        
        stats_message = {
            "type": "book_stats",
            "data": book_stats
        }
        
        for connection in self.active_connections:
            await connection.send_json(stats_message)

    async def broadcast_sentiment_update(self, comment_id: str, sentiment: str):
        if not self.active_connections:
            print("No active connections")
            return

        try:
            # Lấy database session
            db = next(get_db())
            
            # Lấy thông tin comment và book
            comment = db.query(CommentDB).filter(CommentDB.id == comment_id).first()
            book = db.query(BookDB).filter(BookDB.id == comment.book_id).first()

            if not comment:
                print(f"Comment {comment_id} not found")
                return

            # Cập nhật metrics
            try:
                metrics_service = MetricsService(db)
                metrics_service.calculate_batch_metrics()
                metrics_service.log_sentiment_correction(comment_id, sentiment)
                print("Metrics updated after sentiment correction")
            except Exception as e:
                print(f"Error updating metrics: {e}")

            # Chuẩn bị message để broadcast
            message = {
                "type": "reviewUpdated",
                "data": {
                    "id": comment.id,
                    "content": comment.content,
                    "userId": comment.userId,
                    "userName": comment.userName,
                    "bookId": comment.book_id,
                    "bookTitle": book.title if book else None,
                    "sentiment": sentiment,
                    "timestamp": comment.timestamp.isoformat(),
                    "isEditing": False
                }
            }
            
            print("Message to be sent:", json.dumps(message, indent=2))
            
            # Broadcast message
            async with self.lock:
                for connection in list(self.active_connections):
                    try:
                        if connection.application_state != WebSocketState.DISCONNECTED:
                            await connection.send_json(message)
                            print(f"Sent update successfully with full data")
                    except Exception as e:
                        print(f"Error sending to client: {e}")
                        if connection in self.active_connections:
                            self.active_connections.remove(connection)

        except Exception as e:
            print(f"Error in broadcast_sentiment_update: {e}")
        finally:
            db.close()

manager = ConnectionManager() 