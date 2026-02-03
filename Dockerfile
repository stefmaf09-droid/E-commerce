# Production-ready Docker image for Agent IA Recouvrement
FROM python:3.11-slim

LABEL maintainer="agent-ia-recouvrement"
LABEL version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies  
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/reports data/claims data/confirmations data/scraped

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8501
ENV ENVIRONMENT=production

# Expose ports
EXPOSE 8501 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command (can be overridden)
CMD streamlit run dashboard.py --server.port=${PORT} --server.address=0.0.0.0
