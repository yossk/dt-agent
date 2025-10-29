# DT-Agent Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-heb \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/quotes /data/logs /data/incoming

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config/config.yaml

# Default command
CMD ["python", "src/main.py", "--help"]

