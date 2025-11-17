# TradingSystem: Microservice-Based Financial Market Forecasting Platform

## Overview

**TradingSystem** is a modular, microservice-based platform for financial market prediction. It integrates real-time and historical market data with news analytics, leveraging advanced machine learning and NLP to forecast stock movements. The system is designed for scalability, reproducibility, and explainability, using AWS S3 for data storage and Docker for deployment.

---

## Architecture

The platform is composed of several independently deployable services:

- **Crawler Service**: Scrapes and normalizes financial and general news articles.
- **Market Data Service**: Ingests OHLCV and technical indicators from public APIs.
- **Data Processor Service**: Performs article classification, sentiment analysis, financial event extraction, feature engineering, and ML model training.
- **API Service**: Serves predictions, explanations, and data slices via REST and WebSocket endpoints.
- **Frontend Service**: Interactive dashboard for users to explore predictions, news, and analytics.
- **Scheduler Service**: Orchestrates periodic tasks across the pipeline.

---

## Functionalities

### 1. Crawler Service (`crawler_service/`)

- **Continuous and Batch Crawling**:  
  - `continuous_crawler.py` runs every 30 minutes, fetching the latest articles for each company.
  - `run_daily_crawl.py` supports daily batch crawls.
- **Article Normalization**:  
  - Articles are normalized to a common JSON schema (title, content, source, date, company).
- **Deduplication**:  
  - Prevents duplicate articles using a hash-based SQLite database.
- **Quality Filtering**:  
  - Filters by word count, language, and removes boilerplate.
- **Metadata Extraction**:  
  - Extracts company names, tickers, and classifies articles as "financial" or "general".
- **Storage**:  
  - Stores articles locally and uploads to AWS S3 in structured directories by date and company.
- **Monitoring**:  
  - Logs crawl statistics and errors for each cycle.

### 2. Market Data Service (`market_data_service/`)

- **Market Data Ingestion**:  
  - Fetches OHLCV and technical indicators (SMA, EMA, RSI, MACD, etc.) from public APIs.
- **Snapshot Storage**:  
  - Stores market data locally and in AWS S3 as Parquet files.
- **Integration**:  
  - Provides data for feature engineering and model training.

### 3. Data Processor Service (`data_processor_service/`)

- **Article Classification**:  
  - `article_classifier.py` classifies articles as "financial" or "general" using weighted keyword techniques.
- **Sentiment Analysis**:  
  - Uses transformer models (e.g., FinBERT) to score sentiment for titles and content.
- **Financial Event Extraction**:  
  - `financial_analyzer/market_predictor.py` and `earnings_parser.py` extract structured events (earnings beat/miss, guidance changes) and predict market impact.
- **Feature Engineering**:  
  - `ml_pipeline/feature_engineer.py` computes technical, news-based, and interaction features.
- **Dataset Creation**:  
  - Aggregates features and aligns them with market data for ML training.
- **Model Training**:  
  - `ml_pipeline/model_trainer.py` supports XGBoost, LightGBM, and Random Forest models.
  - Evaluates models with RMSE, MAE, R², and direction accuracy.
- **Model Interpretation**:  
  - Provides feature importance and explainability for predictions.
- **Signal Combination**:  
  - Combines sentiment and financial signals for final trading recommendations.

### 4. API Service (`api_service/`)

- **REST Endpoints**:  
  - Serves predictions, explanations, company data, and news slices.
- **WebSocket Support**:  
  - Pushes real-time updates to connected clients.
- **Authentication & Security**:  
  - Endpoints are authenticated and rate-limited.

### 5. Frontend Service (`frontend_service/`)

- **Interactive Dashboard**:  
  - Built with React.
  - Allows symbol lookup, displays predictions, news timelines, sentiment, and financial breakdowns.
- **Real-Time Updates**:  
  - Receives live data via WebSocket.

### 6. Scheduler Service (`scheduler_service/`)

- **Task Orchestration**:  
  - Schedules recurring jobs: crawling, market data refresh, nightly training, and inference updates.

---

## Data Flow

1. **Crawling**: News articles are fetched, normalized, deduplicated, and stored.
2. **Market Data**: OHLCV and indicators are ingested and stored.
3. **Processing**: Articles are classified, analyzed for sentiment and financial events.
4. **Feature Engineering**: News and market features are aligned and engineered.
5. **Model Training**: ML models are trained and evaluated.
6. **Prediction**: Models generate forecasts, which are served via the API.
7. **Frontend**: Users interact with predictions and analytics in real time.

---

## Storage & Cloud Integration

- **AWS S3**:  
  - Stores raw, cleaned, and feature-enriched articles, as well as market data and model artifacts.
  - Versioning and lifecycle policies for cost optimization and reproducibility.
- **Security**:  
  - IAM roles restrict access per service.
  - Data encrypted in transit and at rest.

---

## Deployment

- **Dockerized Services**:  
  - Each service has its own Dockerfile.
  - `docker-compose.yml` for local orchestration.
- **Kubernetes Ready**:  
  - Services can be scaled independently in production.
- **CI/CD**:  
  - Automated testing and deployment pipelines.

---

## Monitoring & Logging

- **Centralized Logging**:  
  - ELK stack (Elasticsearch, Logstash, Kibana) for logs.
- **Metrics & Alerting**:  
  - Prometheus and Grafana for monitoring.
- **S3 & CloudWatch**:  
  - Track storage usage and access.

---

## Testing

- **Unit Tests**:  
  - For deduplication, classification, sentiment, event extraction, and feature engineering.
- **Integration Tests**:  
  - For end-to-end data flow and API endpoints.
- **Frontend E2E Tests**:  
  - For dashboard rendering and user interactions.

---

## Getting Started

1. **Clone the repository**
2. **Set up environment variables** in `.env`
3. **Build and run services** with Docker Compose:
   ```sh
   docker-compose up --build