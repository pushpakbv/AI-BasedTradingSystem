# TradingSystem: Microservice-Based Financial Market Forecasting Platform

## Overview

**TradingSystem** is a modular, microservice-based platform for financial market prediction. It integrates real-time and historical market data with news analytics, leveraging advanced machine learning and NLP to forecast stock movements. The system is designed for scalability, reproducibility, and explainability, using AWS S3 for data storage and Docker for deployment.

---

## Recent Updates & Fixes (January 2026)

### Data Processor Service Fixes

#### 1. **Path Resolution & Docker Compatibility** ✅
- **Issue:** Processor couldn't find crawler data in Docker containers due to hardcoded absolute paths
- **Fix:** 
  - Updated [`process_pipeline.py`](data_processor_service/process_pipeline.py) to check environment variables first (`CRAWLER_DATA_DIR`)
  - Added fallback logic for Docker (`/app/crawler_service`) and local development paths
  - Ensures paths work in both containerized and local environments
- **Code:**
  ```python
  crawler_data_env = os.getenv('CRAWLER_DATA_DIR')
  if crawler_data_env and os.path.exists(crawler_data_env):
      CRAWLER_DIR = Path(crawler_data_env)
  else:
      if os.path.exists('/app/crawler_service'):
          CRAWLER_DIR = Path('/app/crawler_service/data/by_company')
      else:
          CRAWLER_DIR = CUR_DIR.parent / "crawler_service" / "data" / "by_company"
  ```

#### 2. **Article Classification Pipeline** ✅
- **Issue:** `process_pipeline.py` was calling non-existent methods like `classify_company_articles()` on ArticleClassifier
- **Fix:**
  - Updated [`continuous_processor.py`](data_processor_service/continuous_processor.py) to use `ProcessingPipeline` instead of direct classifier methods
  - Removed redundant `process_all_existing()` and `process_company_data()` implementations
  - Now delegates all processing to `ProcessingPipeline.process_company(ticker)`
- **Impact:** Consistent 5-step pipeline execution for all articles

#### 3. **Article Dict vs. String Handling** ✅
- **Issue:** `classifier.classify_article()` was receiving strings instead of article dicts, causing `AttributeError: 'str' object has no attribute 'get'`
- **Fix:**
  - Updated [`process_pipeline.py`](data_processor_service/process_pipeline.py) line 140 to pass full article dicts:
    ```python
    # BEFORE (WRONG):
    result = self.classifier.classify_article(article.get('content', ''))
    
    # AFTER (CORRECT):
    result = self.classifier.classify_article(article)
    ```
  - Article classifier now receives complete article objects with `title`, `content`, `url`, etc.

#### 4. **Classification Result Normalization** ✅
- **Issue:** `classify_article()` returns vary between string and dict formats, causing inconsistent handling
- **Fix:**
  - Normalized results in [`process_pipeline.py`](data_processor_service/process_pipeline.py) lines 142-156:
    ```python
    if isinstance(result, str):
        category = result
        result_dict = {'category': category}
    elif isinstance(result, dict):
        category = result.get('category', 'general')
        result_dict = result
    else:
        category = 'general'
        result_dict = {'category': 'general'}
    ```
  - Always produces consistent dict format downstream

#### 5. **Sentiment Analysis Method Detection** ✅
- **Issue:** Code assumes single sentiment analysis method name; different models use different method names
- **Fix:**
  - Updated [`process_pipeline.py`](data_processor_service/process_pipeline.py) lines 176-182 to check for multiple method names:
    ```python
    if hasattr(self.sentiment_analyzer, 'analyze'):
        sentiment = self.sentiment_analyzer.analyze(content)
    elif hasattr(self.sentiment_analyzer, 'get_sentiment'):
        sentiment = self.sentiment_analyzer.get_sentiment(content)
    elif hasattr(self.sentiment_analyzer, 'predict'):
        sentiment = self.sentiment_analyzer.predict(content)
    ```
  - Supports FinBERT, TextBlob, and other sentiment models without code changes

#### 6. **Financial Event Classification** ✅
- **Issue:** Same method name inconsistency for financial event classifier
- **Fix:**
  - Updated [`process_pipeline.py`](data_processor_service/process_pipeline.py) line 202 to check for `classify()` method
  - Gracefully handles missing/empty results

### Docker Compose Fixes

#### 1. **Data Processor Volume Mounts** ✅
- **Issue:** Processor couldn't access crawler data in shared volumes
- **Fix:** Updated [`docker-compose.yml`](docker-compose.yml) data_processor_service section:
  ```yaml
  volumes:
    - ./crawler_service/data:/app/crawler_service/data:ro  # Shared from crawler
    - ./data_processor_service/final_predictions:/app/final_predictions
    - ./data_processor_service/final_predictions:/app/data_processor_service/final_predictions
  environment:
    - CRAWLER_DATA_DIR=/app/crawler_service/data/by_company
  ```
- **Result:** Proper read-only access to crawler data, writable output directories

#### 2. **Environment Variable Configuration** ✅
- **Issue:** Services didn't have proper path environment variables
- **Fix:**
  - Added `CRAWLER_DATA_DIR=/app/crawler_service/data/by_company` to processor environment
  - Ensures consistent path resolution across all services

### Frontend Service Fixes

#### 1. **Stock Graph Card API Calls** ✅
- **Status:** Working as expected
- **File:** [`StockGraphCard.jsx`](frontend_service/src/components/StockGraphCard.jsx)
- **Features:**
  - Fetches from Alpha Vantage API (free tier)
  - Fallback to Finnhub API
  - Generates mock data as last resort
  - Proper error handling and loading states

#### 2. **Stock Detail Page** ✅
- **Status:** Fully functional
- **File:** [`StockDetail.jsx`](frontend_service/src/pages/StockDetail.jsx)
- **Features:**
  - WebSocket real-time updates
  - Sentiment analysis display
  - Financial news timeline
  - General news timeline
  - Stock info summary

### API Service Fixes

#### 1. **Prediction File Reading** ✅
- **Status:** Working with proper validation
- **File:** [`server.js`](api_service/server.js)
- **Features:**
  - Reads `_prediction.json` files from `/app/data_processor_service/final_predictions`
  - Validates prediction structure before returning
  - Gracefully skips invalid predictions with warnings
  - Returns empty array if no predictions found (instead of error)

#### 2. **WebSocket Broadcasting** ✅
- **Status:** Real-time updates working
- **Features:**
  - Watches for file changes in prediction, sentiment, financial, and stock data directories
  - Broadcasts updates to connected clients
  - Supports dynamic ticker-specific updates

### Market Data Service

#### 1. **Stock Data Fetching** ✅
- **Status:** Functioning correctly
- **File:** [`market_data_service/app.py`](market_data_service/app.py)
- **Features:**
  - Fetches real-time data via yfinance
  - Supports 20+ tracked tickers
  - REST endpoints for individual and batch requests
  - Health check endpoint

---

## Architecture

The platform is composed of several independently deployable services:

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND SERVICE (React)                  │
│         Dashboard, Stock Charts, Predictions, News          │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket/REST
┌────────────────────────▼────────────────────────────────────┐
│                    API SERVICE (Node.js)                     │
│    REST Endpoints, WebSocket, File Watching, Broadcasting   │
└──────────┬──────────────────────────────────────────┬────────┘
           │                                          │
      ┌────▼──────────┐                    ┌─────────▼─────────┐
      │   DATA FROM   │                    │  MARKET DATA API  │
      │   PROCESSOR   │                    │   (yfinance)      │
      └────┬──────────┘                    └───────────────────┘
           │
      ┌────▼──────────────────────────────────────────────────┐
      │      DATA PROCESSOR SERVICE (Python)                  │
      │  Classification, Sentiment, Financial Analysis, ML    │
      └────┬──────────────────────────────────────────────────┘
           │ Reads from
      ┌────▼──────────────────────────────────────────────────┐
      │      CRAWLER SERVICE (Scrapy)                         │
      │  News Crawling, Normalization, Deduplication         │
      └───────────────────────────────────────────────────────┘
```

- **Crawler Service**: Scrapes and normalizes financial and general news articles
- **Market Data Service**: Fetches OHLCV and technical indicators from public APIs
- **Data Processor Service**: Performs article classification, sentiment analysis, financial event extraction
- **API Service**: Serves predictions, explanations, and data slices via REST and WebSocket endpoints
- **Frontend Service**: Interactive dashboard for users to explore predictions, news, and analytics
- **Scheduler Service**: Orchestrates periodic tasks across the pipeline

---

## Microservices and Their Roles

### 1. Crawler Service (`crawler_service/`)

**Purpose:**  
Continuously and batch crawls news articles for tracked companies, normalizes and stores them for downstream processing.

**Key Components:**
- `continuous_crawler.py`: Runs every 30 minutes (or as configured), fetching the latest articles for each company
- `run_daily_crawl.py`: Supports daily batch crawls
- `export_for_sentiment_analysis.py`: Prepares articles for sentiment analysis
- `get_daily_articles.py`: Fetches daily articles
- `config/`: Contains company and crawler configuration
- `data/`: Stores crawled articles by company and date
- `spiders/news_spider.py`: Scrapy spider for crawling FREE news sources
- `utils/dedup.py`: SQLite-based URL deduplication
- `utils/company_matcher.py`: Matches companies in article content

**Pipeline:**
1. **Crawling:** Uses Scrapy and requests to fetch news from multiple sources
2. **Normalization:** Converts raw articles to a common JSON schema (title, content, source, date, company)
3. **Deduplication:** Uses hash-based SQLite DB to prevent duplicate articles
4. **Company Matching:** Identifies which companies are mentioned in each article
5. **Quality Filtering:** Filters by word count, language, and removes boilerplate
6. **Metadata Extraction:** Extracts company names, tickers, and classifies articles as "financial" or "general"
7. **Storage:** Saves articles locally under `data/by_company/{TICKER}/{DATE}/`
8. **Trigger:** After each crawl, triggers the Data Processor Service for the affected ticker

**Output Format:** `crawler_service/data/by_company/{TICKER}/{DATE}/{article_id}.json`
```json
{
  "url": "https://...",
  "title": "Company News Title",
  "content": "Full article content...",
  "summary": "Article summary...",
  "published_date": "2026-01-04T10:30:00Z",
  "fetched_at": "2026-01-04T10:35:00Z",
  "source": "source_domain.com",
  "matched_companies": ["TICKER"],
  "relevance_score": 0.85
}
```

---

### 2. Market Data Service (`market_data_service/`)

**Purpose:**  
Fetches and stores historical and real-time market data and technical indicators for tracked companies.

**Key Components:**
- `app.py`: Flask API for serving market data
- Fetches data from yfinance (free, no API key required)
- Supports 20+ tracked tickers

**Supported Tickers:**
```
AAPL, AMKBY, AMZN, BABA, CHRW, DPW_DE, FDX, GOOGL, MSFT, NVDA,
TSLA, UNP, UPS, XPO, META, NFLX, AMD, INTC, PYPL, UBER, SPOT, ZOOM
```

**Pipeline:**
1. **Data Ingestion:** Fetches OHLCV data from yfinance
2. **Technical Indicators:** Computes SMA, EMA, RSI, MACD (can be extended)
3. **Real-Time Serving:** Provides data via REST endpoints
4. **Integration:** Data used for feature engineering and model training

**REST Endpoints:**
- `GET /api/stock/{ticker}`: Get single stock data
- `GET /api/stocks`: Get all tracked stocks
- `POST /api/stocks/batch`: Get multiple stocks
- `GET /api/supported-tickers`: List all supported tickers
- `GET /health`: Health check

---

### 3. Data Processor Service (`data_processor_service/`)

**Purpose:**  
Processes articles and market data, performs NLP and ML, and generates predictions.

**Key Components:**
- `continuous_processor.py`: Watches for new articles and triggers the processing pipeline
- `process_pipeline.py`: Orchestrates the complete 5-step processing pipeline
- `article_classifier.py`: Classifies articles as "financial" or "general"
- `sentiment_analysis.py`: Uses transformer models (FinBERT) for sentiment scoring
- `financial_analyzer/`:
  - `financial_event_classifier.py`: Detects financial events (earnings, guidance, M&A, etc.)
  - `earnings_parser.py`: Extracts and parses earnings data
  - `market_predictor.py`: Predicts market impact of financial news
  - `signal_combiner.py`: Combines sentiment and financial signals for final prediction
- `ml_pipeline/`: Contains:
  - `feature_engineer.py`: Computes technical, news-based, and interaction features
  - `model_trainer.py`: Trains XGBoost and LightGBM models
  - `run_ml_pipeline.py`: Orchestrates complete ML training pipeline

**5-Step Processing Pipeline:**

1. **Article Classification** (Step 1)
   - Input: Raw articles from crawler
   - Process: Neural network classification
   - Output: "financial" or "general" label
   - File: `classified_articles/{general,financial}/{TICKER}_*.json`

2. **Sentiment Analysis** (Step 2)
   - Input: All articles
   - Process: FinBERT transformer model
   - Output: Sentiment score (-1 to +1) and label (positive, neutral, negative)
   - File: `sentiment_results/{TICKER}_sentiment.json`

3. **Financial Event Classification** (Step 3)
   - Input: Financial articles only
   - Process: Keyword and NLP-based event detection
   - Output: Event types (earnings, guidance, M&A, etc.) with confidence
   - File: `financial_analysis_results/{TICKER}_financial.json`

4. **Feature Engineering** (Step 4)
   - Input: Sentiment, financial events, market data
   - Process: Compute technical features, news-based features, interactions
   - Output: Feature vectors for ML models

5. **Prediction Generation** (Step 5)
   - Input: Combined sentiment, financial signals, market features
   - Process: XGBoost/LightGBM inference
   - Output: Final trading signal (BUY, SELL, HOLD) with confidence
   - File: `final_predictions/{TICKER}_prediction.json`

**Output Format:** `final_predictions/{TICKER}_prediction.json`
```json
{
  "ticker": "TICKER",
  "timestamp": "2026-01-04T17:51:08.284001",
  "total_articles": 6,
  "average_sentiment": 0.45,
  "financial_events": 2,
  "confidence": 0.82,
  "prediction": {
    "final_signal": "BUY",
    "direction": "BULLISH",
    "combined_score": 0.72,
    "confidence_level": "HIGH",
    "reasoning": "Strong positive sentiment with earnings beat"
  }
}
```

**Recent Fixes (January 2026):**
- ✅ Path resolution for Docker/local environments
- ✅ Article dict vs. string handling in classification
- ✅ Classification result normalization (string → dict)
- ✅ Sentiment analysis method detection (supports multiple models)
- ✅ Financial event classification error handling
- ✅ Pipeline orchestration via ProcessingPipeline class

---

### 4. API Service (`api_service/`)

**Purpose:**  
Serves predictions, explanations, and data slices via REST and WebSocket endpoints.

**Key Components:**
- `server.js`: Node.js/Express server for REST and WebSocket endpoints
- `package.json`: Node.js dependencies

**REST Endpoints:**
- `GET /api/health`: Health check
- `GET /api/predictions/daily`: Get all daily predictions
- `GET /api/prediction/{ticker}`: Get prediction for specific ticker
- `GET /api/company/{ticker}`: Get company data (prediction, sentiment, financials, news)
- `GET /api/news/{ticker}`: Get news articles for ticker
- `GET /api/stock/{ticker}`: Get stock market data

**WebSocket Features:**
- Real-time prediction updates
- File system watching for new predictions
- Broadcasting updates to all connected clients
- Event types:
  - `prediction_updated`: New/updated prediction
  - `sentiment_updated`: New sentiment analysis
  - `file_added`: New file in watched directories
  - `stock_data_updated`: New market data

**Features:**
1. **REST Endpoints:** Serves predictions, explanations, company data, and news slices
2. **WebSocket Support:** Pushes real-time updates to connected clients whenever prediction JSONs are updated
3. **File Watching:** Uses chokidar to watch for changes in:
   - `final_predictions/`
   - `sentiment_results/`
   - `financial_analysis_results/`
   - Stock data directories
4. **Company Name Mapping:** Maps tickers to human-readable company names

**Recent Fixes (January 2026):**
- ✅ Prediction file reading with proper structure validation
- ✅ Graceful error handling for missing/invalid predictions
- ✅ Real-time WebSocket broadcasting
- ✅ Directory watching for all relevant output directories

---

### 5. Frontend Service (`frontend_service/`)

**Purpose:**  
Provides an interactive dashboard for users to explore predictions, news, and analytics.

**Key Components:**
- React-based frontend with Tailwind CSS
- Components:
  - `PredictionCard.jsx`: Displays individual stock predictions
  - `StockChart.jsx`: Interactive OHLCV chart with volume
  - `StockGraphCard.jsx`: Stock price history visualization
  - `StockDetail.jsx`: Comprehensive stock information page
  - `Dashboard.jsx`: Main dashboard with all predictions
  - `NewsTimeline.jsx`: Timeline view of news articles
  - `SentimentAnalysis.jsx`: Sentiment distribution visualization
  - `SystemStatus.jsx`: System health indicator

**Pipeline:**
1. **Symbol Lookup:** Allows users to search for companies
2. **Dashboard View:** Shows all predictions with real-time updates
3. **Stock Detail Page:** In-depth analysis for individual stocks
4. **WebSocket Integration:** Receives live updates from API service and updates UI automatically
5. **News Integration:** Displays news articles with sentiment labels
6. **Technical Analysis:** OHLCV charts with interactive features

**Key Hooks:**
- `usePrediction.js`: Fetches and manages prediction data via WebSocket

**Recent Updates (January 2026):**
- ✅ Stock Graph Card with multiple API fallbacks
- ✅ Real-time sentiment analysis display
- ✅ WebSocket-based real-time updates
- ✅ Comprehensive news timeline
- ✅ Stock information summary cards

---

### 6. Scheduler Service (`scheduler_service/`)

**Purpose:**  
Orchestrates periodic tasks across the pipeline.

**Key Components:**
- Schedules recurring jobs: crawling, market data refresh, nightly training, and inference updates

---

## Data Flow

1. **Crawling:** News articles are fetched, normalized, deduplicated, and stored under `crawler_service/data/by_company/{TICKER}/{DATE}/`
2. **Triggering:** Crawler triggers processor via file system events or API calls
3. **Processing:** Data Processor reads articles and executes 5-step pipeline:
   - Classification → Sentiment → Financial Events → Features → Prediction
4. **Storage:** Results saved to:
   - `classified_articles/` (step 1)
   - `sentiment_results/` (step 2)
   - `financial_analysis_results/` (step 3)
   - `final_predictions/` (step 5)
5. **API Serving:** API Service reads prediction files and serves via REST/WebSocket
6. **Real-Time Updates:** File changes broadcast to connected frontend clients via WebSocket
7. **Frontend Display:** Dashboard updates in real-time with new predictions and news

---

## Storage & Cloud Integration

- **Local Storage:**  
  - Raw articles: `crawler_service/data/by_company/`
  - Predictions: `data_processor_service/final_predictions/`
  - Sentiment results: `data_processor_service/sentiment_results/`
  - Financial analysis: `data_processor_service/financial_analysis_results/`
  - Market data: `market_data_service/stock_data/` (optional)

- **AWS S3 (Optional):**  
  - Stores raw, cleaned, and feature-enriched articles
  - Stores market data and model artifacts
  - Versioning and lifecycle policies for cost optimization and reproducibility

- **Security:**  
  - IAM roles restrict access per service
  - Data encrypted in transit and at rest

---

## Deployment

### Local Development

```sh
# Clone the repository
git clone <repo-url>
cd TradeSystem

# Set up environment variables in .env
cp .env.example .env

# Build and run services with Docker Compose
docker-compose up --build

# Access services:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - Market Data: http://localhost:8001
# - WebSocket: ws://localhost:8000
```

### Docker Compose Services

- **Dockerized Services:**  
  - Each service has its own Dockerfile
  - `docker-compose.yml` for local orchestration
  - Volume mounts for data sharing between services
  - Network isolation with custom bridge network

### Kubernetes Ready

- Services can be scaled independently in production
- Stateless design for horizontal scaling
- Environment variables for configuration management

### CI/CD

- Automated testing and deployment pipelines
- Unit tests for each service
- Integration tests for data flow

---

## Environment Variables

### Data Processor Service
```
PYTHONUNBUFFERED=1           # Real-time logging
PROCESSOR_CHECK_INTERVAL_SECONDS=60  # Check interval for new data
LOG_LEVEL=INFO               # Logging level
CRAWLER_DATA_DIR=/app/crawler_service/data/by_company  # Crawler data path
```

### Market Data Service
```
PYTHONUNBUFFERED=1
FLASK_ENV=production
FLASK_DEBUG=False
PORT=8001
LOG_LEVEL=INFO
```

### API Service
```
FLASK_ENV=production
PYTHONUNBUFFERED=1
MARKET_DATA_SERVICE_URL=http://market_data_service:8001/api
```

### Frontend Service
```
REACT_APP_API_URL=http://localhost:8000/api              # Browser → API
REACT_APP_MARKET_DATA_API=http://localhost:8001/api      # Browser → Market Data
REACT_APP_WS_URL=ws://localhost:8000                     # Browser → WebSocket
REACT_APP_INTERNAL_API_URL=http://api_service:8000/api   # Container → API
REACT_APP_INTERNAL_MARKET_DATA_API=http://market_data_service:8001/api  # Container → Market Data
```

---

## Monitoring & Logging

- **Logging:**  
  - All services use Python logging or console.log
  - Structured format: `timestamp - service - level - message`
  - Real-time output visible in Docker container logs

- **Health Checks:**  
  - API Service: `GET /api/health` → `{status: 'healthy', ...}`
  - Market Data: `GET /health` → `{status: 'healthy', ...}`
  - Docker Compose health checks configured for critical services

- **File Watching:**  
  - API Service watches for prediction file changes
  - Automatically broadcasts updates via WebSocket

---

## Testing

### Unit Tests
- Located in `tests/` directory
- Tests for:
  - URL deduplication (`test_crawler.py`)
  - Company matching (`test_crawler.py`)
  - Crawler output format (`test_crawler.py`)
  - Article classification
  - Sentiment analysis
  - Feature engineering

### Integration Tests
- End-to-end data flow testing
- API endpoint testing
- WebSocket communication testing

### Frontend E2E Tests
- Dashboard rendering
- Stock detail page functionality
- Real-time update handling
- User interactions

### Running Tests
```sh
# Python tests
python -m pytest tests/

# Frontend tests
cd frontend_service
npm test
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for frontend development)

### Quick Start

1. **Clone the repository**
   ```sh
   git clone <repo-url>
   cd TradeSystem
   ```

2. **Set up environment variables**
   ```sh
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and run services**
   ```sh
   docker-compose up --build
   ```

4. **Access the dashboard**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs (if enabled)
   - WebSocket: ws://localhost:8000

5. **View logs**
   ```sh
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f tradesystem_crawler
   docker-compose logs -f tradesystem_processor
   docker-compose logs -f tradesystem_api
   ```

---

## Directory Structure

```
.
├── api_service/                    # REST API and WebSocket server
│   ├── server.js                   # Node.js/Express API
│   ├── server.py                   # Python/Flask API (alternative)
│   ├── package.json
│   └── Dockerfile
│
├── crawler_service/                # News crawling service
│   ├── continuous_crawler.py       # Main crawler loop
│   ├── spiders/
│   │   └── news_spider.py          # Scrapy spider
│   ├── utils/
│   │   ├── dedup.py                # URL deduplication
│   │   └── company_matcher.py      # Company matching
│   ├── config/
│   │   └── companies.yml           # Tracked companies
│   ├── data/
│   │   └── by_company/             # Crawled articles
│   ├── requirements.txt
│   └── Dockerfile
│
├── data_processor_service/         # NLP and ML processing
│   ├── continuous_processor.py     # File watcher and processor
│   ├── process_pipeline.py         # Main processing pipeline ⭐ FIXED
│   ├── article_classifier.py       # Article classification
│   ├── sentiment_analysis.py       # Sentiment analysis
│   ├── financial_analyzer/
│   │   ├── financial_event_classifier.py
│   │   ├── earnings_parser.py
│   │   ├── market_predictor.py
│   │   └── signal_combiner.py
│   ├── ml_pipeline/
│   │   ├── feature_engineer.py
│   │   ├── model_trainer.py
│   │   └── run_ml_pipeline.py
│   ├── final_predictions/          # Output: predictions
│   ├── sentiment_results/          # Output: sentiment analysis
│   ├── financial_analysis_results/ # Output: financial events
│   ├── classified_articles/        # Output: classified articles
│   ├── requirements.txt
│   └── Dockerfile
│
├── market_data_service/            # Stock market data
│   ├── app.py                      # Flask API
│   ├── stock_data/                 # Cached data
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend_service/               # React dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Main dashboard
│   │   │   └── StockDetail.jsx     # Stock detail page
│   │   ├── components/
│   │   │   ├── PredictionCard.jsx
│   │   │   ├── StockChart.jsx
│   │   │   ├── StockGraphCard.jsx
│   │   │   ├── NewsTimeline.jsx
│   │   │   ├── SentimentAnalysis.jsx
│   │   │   └── SystemStatus.jsx
│   │   ├── hooks/
│   │   │   └── usePrediction.js
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── Dockerfile
│
├── scheduler_service/              # Task scheduling
│   ├── scheduler.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── tests/                          # Unit and integration tests
│   ├── test_crawler.py
│   └── ...
│
├── docker-compose.yml              # Service orchestration ⭐ FIXED
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

---

## Data Pipeline Example

1. **News Crawling (Crawler Service)**
   - Scrapes articles from financial news sites
   - Stores to: `crawler_service/data/by_company/MSFT/2026-01-04/article_1.json`

2. **Triggering (File System Event)**
   - New files detected in `crawler_service/data/`
   - Processor triggered automatically

3. **Processing (Data Processor Service)**
   - **Step 1:** Classify articles → `classified_articles/MSFT_financial.json`
   - **Step 2:** Sentiment analysis → `sentiment_results/MSFT_sentiment.json`
   - **Step 3:** Financial events → `financial_analysis_results/MSFT_financial.json`
   - **Step 4:** Feature engineering → Internal vectors
   - **Step 5:** ML prediction → `final_predictions/MSFT_prediction.json`

4. **API Serving (API Service)**
   - Reads `final_predictions/MSFT_prediction.json`
   - Serves via `GET /api/prediction/MSFT`
   - Watches for file changes

5. **Real-Time Broadcast (WebSocket)**
   - File change detected
   - Broadcasts `prediction_updated` event to all connected clients
   - Includes new prediction data

6. **Frontend Update (React Dashboard)**
   - Receives WebSocket message
   - Updates prediction card for MSFT in real-time
   - No manual refresh needed by user

---

## Real-Time & Dynamic Updates

- **Automatic Triggering:** Whenever new articles are crawled, the data processor is triggered to re-run the pipeline for the affected ticker
- **File Watching:** API service detects updated prediction files and pushes changes to the frontend via WebSocket
- **Frontend Updates:** The frontend automatically updates prediction cards and analytics in real time, with no manual refresh needed
- **WebSocket Events:** 
  - `prediction_updated`: New trading signal
  - `sentiment_updated`: New sentiment analysis
  - `file_added`: New article processed
  - `stock_data_updated`: New market data

---

## Troubleshooting

### Data Processor Service Issues

**Issue:** `AttributeError: 'str' object has no attribute 'get'`
- **Cause:** Passing string content instead of article dict to classifier
- **Fix:** Ensured `process_pipeline.py` passes full article objects
- **Status:** ✅ FIXED (January 2026)

**Issue:** `Warning: Crawler data directory not found`
- **Cause:** Incorrect path resolution in Docker containers
- **Fix:** Added environment variable check and fallback path logic
- **Status:** ✅ FIXED (January 2026)

**Issue:** Classification method not found
- **Cause:** Calling non-existent methods on classifier
- **Fix:** Updated to use `ProcessingPipeline.process_company()` directly
- **Status:** ✅ FIXED (January 2026)

**Issue:** Sentiment scores always 0.0
- **Cause:** Method name mismatch (analyze vs get_sentiment vs predict)
- **Fix:** Added dynamic method name detection
- **Status:** ✅ FIXED (January 2026)

### Frontend Issues

**Issue:** WebSocket connection failing
- **Solution:** Ensure API service is running on port 8000
- **Check:** `docker-compose ps` should show `tradesystem_api` running

**Issue:** Stock data not displaying
- **Solution:** Verify Market Data Service is running on port 8001
- **Check:** `curl http://localhost:8001/health`

**Issue:** Predictions not updating in real-time
- **Solution:** Check WebSocket connection in browser console
- **Fix:** Ensure `/api/health` endpoint responds with `websocket_clients` count

### Docker Issues

**Issue:** Volume mount permission denied
- **Solution:** Ensure directories exist and have proper permissions
  ```sh
  mkdir -p data_processor_service/final_predictions
  mkdir -p data_processor_service/sentiment_results
  mkdir -p crawler_service/data
  ```

**Issue:** Services can't communicate
- **Solution:** Verify they're on the same network in `docker-compose.yml`
- **Check:** `docker network ls` and `docker network inspect tradesystem_network`

---

## Contributing

1. Fork the repo and create your branch
2. Add/modify code and tests
3. Ensure all services pass tests
4. Submit a pull request with a clear description

---

## License

This project is for academic and research purposes.

---

## Contact

For questions or support, open an issue in the repository or contact the maintainers.

---

## Changelog

### January 4, 2026 - Data Processor Pipeline Overhaul

**Fixed:**
- ✅ Path resolution for Docker/local environments
- ✅ Article dict vs. string handling in classification
- ✅ Classification result normalization
- ✅ Sentiment analysis method detection
- ✅ Financial event classification error handling
- ✅ Docker Compose volume mounts and environment variables
- ✅ Data Processor initialization and pipeline orchestration

**Improved:**
- Enhanced error logging and debugging
- Better handling of missing/invalid data
- Graceful fallbacks for missing API methods
- Documentation of data flows and pipeline steps

**Status:** All core services functional and tested ✅