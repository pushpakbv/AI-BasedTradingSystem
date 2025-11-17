FROM python:3.10-slim

WORKDIR /app

# Copy crawler_service code
COPY crawler_service/ ./crawler_service

# Copy data_processor_service code so it can be imported
COPY data_processor_service/ ./data_processor_service

WORKDIR /app/crawler_service

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "continuous_crawler.py"]