FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download models ahead of time (optional but recommended)
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    AutoTokenizer.from_pretrained('ProsusAI/finbert'); \
    AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')"

# Copy application code
COPY . /app/data_processor_service/

CMD ["python", "/app/data_processor_service/process_pipeline.py"]

