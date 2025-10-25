FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY scheduler_service/requirements.txt /app/scheduler_service/
RUN pip install --no-cache-dir -r scheduler_service/requirements.txt

# Copy entire project (needed to run other services)
COPY . /app/

# Set Python path
ENV PYTHONPATH=/app

WORKDIR /app/scheduler_service

CMD ["python", "scheduler.py"]