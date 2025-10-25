FROM python:3.10-slim

WORKDIR /app

# Copy requirements from correct path (context is root)
COPY market_data_service/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -r requirements.txt

# Copy application code
COPY market_data_service/ /app/market_data_service/

# Create stock data directory
RUN mkdir -p /app/market_data_service/stock_data

WORKDIR /app/market_data_service

CMD ["python", "stock_data_fetcher.py"]