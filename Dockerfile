FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU version first
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Expose port để FastAPI chạy
EXPOSE 8000

# Command để chạy ứng dụng
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 