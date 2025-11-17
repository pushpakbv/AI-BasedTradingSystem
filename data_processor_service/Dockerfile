FROM python:3.10-slim

WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt ./

# Install dependencies (this will be cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your code
COPY . .

# Expose a volume for final_predictions
VOLUME ["/app/final_predictions"]

CMD ["python", "continuous_processor.py"]