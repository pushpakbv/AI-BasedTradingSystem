FROM python:3.10.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for Scrapy, lxml, and BeautifulSoup
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY crawler_service/requirements.txt ./crawler_service/
RUN pip install --no-cache-dir -r crawler_service/requirements.txt

# Copy the entire crawler service
COPY crawler_service ./crawler_service/

# Copy shared utilities if they exist
COPY shared ./shared/

# Create necessary data directories
RUN mkdir -p /app/crawler_service/data/raw \
             /app/crawler_service/data/by_company

# Set Python path to include app directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Set working directory to app root
WORKDIR /app

# Run the crawler main script
CMD ["python", "crawler_service/main.py"]