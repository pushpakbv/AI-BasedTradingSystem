FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY data_processor_service/requirements.txt /app/data_processor_service/

# Install PyTorch CPU version (much smaller, faster download)
RUN pip install --no-cache-dir \
    --timeout 600 \
    --default-timeout=600 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch>=2.0.0

# Install other dependencies
RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -r /app/data_processor_service/requirements.txt

# Copy application code
COPY data_processor_service/ /app/data_processor_service/

# Create output directories
RUN mkdir -p /app/data_processor_service/final_predictions \
    /app/data_processor_service/sentiment_results \
    /app/data_processor_service/financial_analysis_results \
    /app/data_processor_service/classified_articles

WORKDIR /app/data_processor_service

CMD ["python", "continuous_processor.py"]