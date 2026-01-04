FROM python:3.10-slim

WORKDIR /app

COPY market_data_service/requirements.txt /app/

RUN pip install --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    -r requirements.txt

COPY market_data_service/ /app/

EXPOSE 8001

CMD ["python", "app.py"]