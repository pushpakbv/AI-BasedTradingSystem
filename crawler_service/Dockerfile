FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY crawler_service/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -r requirements.txt

# Copy application code
COPY crawler_service/ /app/crawler_service/

# Create data directories
RUN mkdir -p /app/crawler_service/data/by_company \
    /app/crawler_service/data/by_date \
    /app/crawler_service/config

WORKDIR /app/crawler_service

CMD ["python", "continuous_crawler.py"]