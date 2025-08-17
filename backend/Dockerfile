FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for AI model loading
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for better AI model loading
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HOME=/app/.cache/huggingface
ENV TOKENIZERS_PARALLELISM=false
ENV TRANSFORMERS_OFFLINE=0

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]