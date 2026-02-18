FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# tesseract-ocr: for OCRProcessor
# libpq-dev: for psycopg2 (if needed later)
# curl: for healthchecks
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Healthcheck to ensure app is running
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "client_dashboard_main_new.py", "--server.port=8501", "--server.address=0.0.0.0"]
