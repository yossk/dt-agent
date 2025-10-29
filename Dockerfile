# DT-Agent Dockerfile
# Supports both production (pip) and development (uv) modes
ARG BUILD_MODE=production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-heb \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Production mode: use pip with requirements.txt
# Development mode: use uv with pyproject.toml
ARG BUILD_MODE=production

# Install uv for faster dependency resolution
RUN pip install --no-cache-dir uv || true

# Copy dependency files
COPY requirements.txt pyproject.toml* ./

# Install dependencies based on mode
RUN if [ "$BUILD_MODE" = "dev" ] && [ -f pyproject.toml ]; then \
        uv pip install --system -e ".[dev]"; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/quotes /data/logs /data/incoming

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config/config.yaml

# Default command
CMD ["python", "src/main.py", "--help"]

