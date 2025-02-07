from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from sqlalchemy.orm import Session
from . import crud, models, database
from .database import engine, get_db
from pydantic import BaseModel
import shutil
import os
from pathlib import Path
from .websocket_manager import manager
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.websockets import WebSocketState
from .metrics_service import MetricsService
from datetime import datetime
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bookstore API")

# Cấu hình CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Thêm class để validate request body cho comment
class CommentCreate(BaseModel):
    content: str
    user_id: str
    user_name: str

class SentimentUpdate(BaseModel):
    id: str
    sentiment: str

@app.get("/books", response_model=List[models.Book])
def list_books(db: Session = Depends(database.get_db)):
    return crud.get_books(db)

@app.get("/books/{book_id}", response_model=models.Book)
def get_book(book_id: str, db: Session = Depends(database.get_db)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.post("/books/{book_id}/comments")
async def create_comment(
    book_id: str,
    comment: CommentCreate,
    db: Session = Depends(database.get_db)
):
    try:
        new_comment = await crud.create_comment(
            db,
            book_id=book_id,
            user_id=comment.user_id,
            user_name=comment.user_name,
            content=comment.content
        )
        return new_comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/books/{book_id}/upload-cover")
async def upload_book_cover(book_id: str, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    # Kiểm tra book tồn tại
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Kiểm tra file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Tạo tên file mới
    file_extension = Path(file.filename).suffix
    new_filename = f"book_{book_id}{file_extension}"
    file_path = f"app/static/book_covers/{new_filename}"
    
    # Lưu file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Cập nhật URL trong database
    image_url = f"/static/book_covers/{new_filename}"
    crud.update_book_image(db, book_id, image_url)
    
    return {"image_url": image_url}

# Endpoint lấy thống kê sentiment
@app.get("/books/{book_id}/sentiment-stats")
def get_book_sentiment_stats(book_id: str, db: Session = Depends(database.get_db)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_sentiment_stats(db, book_id)

# Endpoint lấy thống kê sentiment tổng thể
@app.get("/sentiment-stats")
def get_overall_sentiment_stats(db: Session = Depends(database.get_db)):
    return crud.get_sentiment_stats(db)

# Endpoint lấy comments với sentiment
@app.get("/books/{book_id}/comments-with-sentiment", response_model=List[models.Comment])
def get_book_comments_with_sentiment(
    book_id: str, 
    sentiment: str = None,
    db: Session = Depends(database.get_db)
):
    comments = crud.get_book_comments(db, book_id)
    if sentiment:
        comments = [c for c in comments if c.sentiment == sentiment]
    return comments

# Thêm WebSocket endpoints
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f"New WebSocket connection attempt from: {websocket.client}")
    try:
        await websocket.accept()
        await manager.connect(websocket)
        print("WebSocket connected successfully")
        
        while True:
            try:
                if websocket.application_state == WebSocketState.DISCONNECTED:
                    break
                    
                data = await websocket.receive_json()
                print(f"Received message: {data}")
                
                if data.get("type") == "reviewUpdate":
                    await manager.broadcast_sentiment_update(
                        data["data"]["id"],
                        data["data"]["sentiment"]
                    )
            except WebSocketDisconnect:
                print("Client disconnected normally")
                break
            except Exception as e:
                print(f"Error in WebSocket communication: {e}")
                break
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        await manager.disconnect(websocket)
        print("WebSocket connection closed")

@app.put("/comments/{comment_id}/sentiment")
async def update_comment_sentiment(
    comment_id: str,
    update: SentimentUpdate,
    db: Session = Depends(database.get_db)
):
    comment = crud.update_comment_sentiment(db, comment_id, update.sentiment)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Broadcast update through WebSocket
    await manager.broadcast_sentiment_update(comment_id, update.sentiment)
    
    return comment

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(db: Session = Depends(get_db)):
    try:
        metrics_service = MetricsService(db)
        metrics = metrics_service.get_dashboard_metrics()
        if not metrics:
            logger.error("Failed to get metrics")
            raise HTTPException(status_code=500, detail="Failed to get metrics")
        logger.info("Successfully retrieved metrics")
        return {"success": True, "data": metrics}
    except Exception as e:
        logger.error(f"Error in dashboard metrics endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 