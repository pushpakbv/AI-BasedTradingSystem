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

## Microservices and Their Roles

### 1. Crawler Service (`crawler_service/`)

**Purpose:**  
Continuously and batch crawls news articles for tracked companies, normalizes and stores them for downstream processing.

**Key Components:**
- `continuous_crawler.py`: Runs every 30 minutes (or as configured), fetching the latest articles for each company and triggering downstream processing.
- `run_daily_crawl.py`: Supports daily batch crawls.
- `export_for_sentiment_analysis.py`: Prepares articles for sentiment analysis.
- `get_daily_articles.py`: Fetches daily articles.
- `config/`: Contains company and crawler configuration.
- `data/`: Stores crawled articles by company and date.

**Pipeline:**
1. **Crawling:** Uses Scrapy and requests to fetch news from multiple sources.
2. **Normalization:** Converts raw articles to a common JSON schema (title, content, source, date, company).
3. **Deduplication:** Uses a hash-based SQLite DB to prevent duplicate articles.
4. **Quality Filtering:** Filters by word count, language, and removes boilerplate.
5. **Metadata Extraction:** Extracts company names, tickers, and classifies articles as "financial" or "general".
6. **Storage:** Saves articles locally under `data/by_company/{TICKER}/{DATE}/` and uploads to AWS S3.
7. **Trigger:** After each crawl, triggers the Data Processor Service for the affected ticker.

---

### 2. Market Data Service (`market_data_service/`)

**Purpose:**  
Fetches and stores historical and real-time market data and technical indicators for tracked companies.

**Key Components:**
- `market_data_service/`: Contains scripts for fetching OHLCV data and technical indicators.
- Stores data as Parquet files locally and in AWS S3.

**Pipeline:**
1. **Data Ingestion:** Fetches OHLCV and technical indicators (SMA, EMA, RSI, MACD, etc.) from public APIs.
2. **Snapshot Storage:** Stores market data locally and in S3.
3. **Integration:** Provides data for feature engineering and model training.

---

### 3. Data Processor Service (`data_processor_service/`)

**Purpose:**  
Processes articles and market data, performs NLP and ML, and generates predictions.

**Key Components:**
- `continuous_processor.py`: Watches for new articles and triggers the full processing pipeline.
- `article_classifier.py`: Classifies articles as "financial" or "general".
- `sentiment_analysis.py`: Uses transformer models (e.g., FinBERT) for sentiment scoring.
- `financial_analyzer/`: Contains:
  - `market_predictor.py`: Predicts market impact of financial news.
  - `earnings_parser.py`: Extracts and parses earnings data.
  - `financial_event_classifier.py`: Detects financial events (earnings, guidance, etc.).
  - `signal_combiner.py`: Combines sentiment and financial signals for final prediction.
- `ml_pipeline/`: Contains:
  - `feature_engineer.py`: Computes technical, news-based, and interaction features.
  - `historical_data_collector.py`: Aggregates features and aligns them with market data.
  - `model_trainer.py`: Trains XGBoost, LightGBM, and Random Forest models.
  - `ml_predictor.py`: Loads trained models and makes predictions.

**Pipeline:**
1. **Article Classification:** Classifies articles using weighted keyword techniques.
2. **Sentiment Analysis:** Scores sentiment for titles and content using transformer models.
3. **Financial Event Extraction:** Extracts structured events (earnings beat/miss, guidance changes) and predicts market impact.
4. **Feature Engineering:** Computes technical, news-based, and interaction features.
5. **Dataset Creation:** Aggregates features and aligns them with market data for ML training.
6. **Model Training:** Trains and evaluates ML models (XGBoost, LightGBM, Random Forest).
7. **Model Interpretation:** Provides feature importance and explainability for predictions.
8. **Signal Combination:** Combines sentiment and financial signals for final trading recommendations.
9. **Prediction Storage:** Saves predictions as JSON in `final_predictions/{TICKER}_prediction.json`.

**Real-Time Updates:**  
Whenever new articles are crawled, the processor is triggered to re-run the pipeline for the affected ticker, updating all analytics and predictions dynamically.

---

### 4. API Service (`api_service/`)

**Purpose:**  
Serves predictions, explanations, and data slices via REST and WebSocket endpoints.

**Key Components:**
- `server.js`: Node.js/Express server for REST and WebSocket endpoints.
- `server.py`: (If used) Python/Flask server for API endpoints.
- `package.json`: Node.js dependencies.

**Pipeline:**
1. **REST Endpoints:** Serves predictions, explanations, company data, and news slices.
2. **WebSocket Support:** Pushes real-time updates to connected clients whenever prediction JSONs are updated.
3. **Authentication & Security:** Endpoints are authenticated and rate-limited.

---

### 5. Frontend Service (`frontend_service/`)

**Purpose:**  
Provides an interactive dashboard for users to explore predictions, news, and analytics.

**Key Components:**
- React-based frontend.
- Components for prediction cards, news timelines, sentiment charts, and financial breakdowns.

**Pipeline:**
1. **Symbol Lookup:** Allows users to search for companies.
2. **Prediction Display:** Shows real-time predictions, news, and analytics.
3. **WebSocket Integration:** Receives live updates from the API service and updates the UI automatically.

---

### 6. Scheduler Service (`scheduler_service/`)

**Purpose:**  
Orchestrates periodic tasks across the pipeline.

**Key Components:**
- Schedules recurring jobs: crawling, market data refresh, nightly training, and inference updates.

---

## Data Flow

1. **Crawling:** News articles are fetched, normalized, deduplicated, and stored.
2. **Market Data:** OHLCV and indicators are ingested and stored.
3. **Processing:** Articles are classified, analyzed for sentiment and financial events.
4. **Feature Engineering:** News and market features are aligned and engineered.
5. **Model Training:** ML models are trained and evaluated.
6. **Prediction:** Models generate forecasts, which are served via the API.
7. **Frontend:** Users interact with predictions and analytics in real time.

---

## Storage & Cloud Integration

- **AWS S3:**  
  - Stores raw, cleaned, and feature-enriched articles, as well as market data and model artifacts.
  - Versioning and lifecycle policies for cost optimization and reproducibility.
- **Security:**  
  - IAM roles restrict access per service.
  - Data encrypted in transit and at rest.

---

## Deployment

- **Dockerized Services:**  
  - Each service has its own Dockerfile.
  - `docker-compose.yml` for local orchestration.
- **Kubernetes Ready:**  
  - Services can be scaled independently in production.
- **CI/CD:**  
  - Automated testing and deployment pipelines.

---

## Monitoring & Logging

- **Centralized Logging:**  
  - ELK stack (Elasticsearch, Logstash, Kibana) for logs.
- **Metrics & Alerting:**  
  - Prometheus and Grafana for monitoring.
- **S3 & CloudWatch:**  
  - Track storage usage and access.

---

## Testing

- **Unit Tests:**  
  - For deduplication, classification, sentiment, event extraction, and feature engineering.
- **Integration Tests:**  
  - For end-to-end data flow and API endpoints.
- **Frontend E2E Tests:**  
  - For dashboard rendering and user interactions.

---

## Getting Started

1. **Clone the repository**
2. **Set up environment variables** in `.env`
3. **Build and run services** with Docker Compose:
   ```sh
   docker-compose up --build
   ```
4. **Access the frontend dashboard** at `http://localhost:3000`
5. **API documentation** available at `/api/docs` (if enabled)

---

## Directory Structure

```
api_service/           # REST API and WebSocket server
crawler_service/       # News crawling and normalization
data_processor_service/# Article processing, ML pipeline, feature engineering
frontend_service/      # React dashboard
market_data_service/   # Market data ingestion
scheduler_service/     # Task scheduling
tests/                 # Unit and integration tests
docker-compose.yml     # Multi-service orchestration
.env                   # Environment variables
```

---

## Data Pipeline Example

1. **Crawler Service** scrapes and normalizes news articles, storing them in `crawler_service/data/by_company/{TICKER}/{DATE}/`.
2. **Data Processor Service** is triggered, classifies articles, runs sentiment analysis, extracts financial events, engineers features, and updates predictions.
3. **Market Data Service** fetches and stores OHLCV and technical indicators.
4. **API Service** serves the latest predictions and pushes updates via WebSocket.
5. **Frontend Service** displays real-time predictions and analytics to users.
6. **Scheduler Service** ensures all tasks run on schedule.

---

## Real-Time & Dynamic Updates

- Whenever new articles are scraped, the data processor is triggered to update all analytics and predictions for the affected company.
- The API service detects updated prediction files and pushes changes to the frontend via WebSocket.
- The frontend updates prediction cards and analytics in real time, with no manual refresh needed.

---

## Contributing

1. Fork the repo and create your branch.
2. Add/modify code and tests.
3. Submit a pull request with a clear description.

---

## License

This project is for academic and research purposes. See [LICENSE](LICENSE) for details.

---

## Contact

For questions or support, contact the maintainers listed in the project or open an issue.
