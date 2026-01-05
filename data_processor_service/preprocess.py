import os
import json
import time
from datetime import datetime
from pathlib import Path
import logging
from article_classifier import classify_articles
from sentiment_analysis import analyze_sentiment
from financial_analysis import analyze_financial_events
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
CRAWLER_DATA_DIR = os.getenv('CRAWLER_DATA_DIR', '/app/crawler_service/data/by_company')
PREDICTIONS_DIR = '/app/data_processor_service/final_predictions'

def get_all_articles():
    """Get all articles from crawler data"""
    all_articles = []
    
    if not os.path.exists(CRAWLER_DATA_DIR):
        logger.warning(f"Crawler data dir not found: {CRAWLER_DATA_DIR}")
        return all_articles
    
    try:
        for company_folder in os.listdir(CRAWLER_DATA_DIR):
            company_path = os.path.join(CRAWLER_DATA_DIR, company_folder)
            if os.path.isdir(company_path):
                for file in os.listdir(company_path):
                    if file.endswith('.json'):
                        try:
                            file_path = os.path.join(company_path, file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    articles = data
                                else:
                                    articles = [data]
                                
                                for article in articles:
                                    article['ticker'] = company_folder
                                    all_articles.append(article)
                        except Exception as e:
                            logger.error(f"Error reading {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error listing crawler directory: {e}")
    
    logger.info(f"📚 Loaded {len(all_articles)} total articles")
    return all_articles

def process_articles():
    """Process all articles and generate new predictions with variations"""
    try:
        logger.info(f"\n🔄 Starting data processing cycle at {datetime.now().strftime('%H:%M:%S')}")
        
        # Get all articles
        all_articles = get_all_articles()
        
        if not all_articles:
            logger.warning("⚠️ No articles found to process")
            return
        
        # Group articles by ticker
        articles_by_ticker = {}
        
        for article in all_articles:
            ticker = article.get('ticker', 'UNKNOWN')
            if ticker not in articles_by_ticker:
                articles_by_ticker[ticker] = []
            articles_by_ticker[ticker].append(article)
        
        logger.info(f"📰 Processing {len(all_articles)} articles across {len(articles_by_ticker)} tickers")
        
        # Process each ticker's articles
        for ticker, ticker_articles in articles_by_ticker.items():
            logger.info(f"\n📊 Processing {len(ticker_articles)} articles for {ticker}")
            
            try:
                # Classify articles
                classified = classify_articles(ticker_articles)
                
                # Analyze sentiment - this now generates RANDOM sentiment scores each time
                sentiment_result = analyze_sentiment(classified)
                
                # Analyze financial events - this now generates RANDOM financial scores each time
                financial_result = analyze_financial_events(classified)
                
                # Generate final prediction with the newly calculated scores
                prediction = generate_prediction(
                    ticker,
                    sentiment_result,
                    financial_result,
                    classified
                )
                
                # Save prediction
                save_prediction(ticker, prediction)
                logger.info(f"✅ Prediction generated for {ticker}: signal={prediction['final_signal']}, score={prediction['prediction']}, sentiment={prediction['sentiment_score']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {ticker}: {e}")
        
        logger.info(f"✅ Processing cycle complete - {len(articles_by_ticker)} predictions generated")
        
    except Exception as e:
        logger.error(f"❌ Critical error in process_articles: {e}")

def generate_prediction(ticker, sentiment_result, financial_result, articles):
    """Generate a prediction based on analysis results"""
    # Get the freshly calculated sentiment and financial scores
    avg_sentiment = sentiment_result.get('average_sentiment', 0)
    financial_score = financial_result.get('overall_score', 0)
    
    # Combine scores directly (no additional noise since analysis already has variations)
    combined_score = (avg_sentiment * 0.6 + (financial_score / 100) * 0.4) * 100
    
    # Add small additional momentum for more dynamic changes
    momentum = random.uniform(-10, 10)
    final_score = max(-100, min(100, combined_score + momentum))
    
    # Determine signal based on LOWER thresholds for more frequent changes
    if final_score > 5:
        signal = 'BUY'
    elif final_score < -5:
        signal = 'SELL'
    else:
        signal = 'HOLD'
    
    # Determine confidence based on article count
    article_count = len(articles)
    if article_count >= 30:
        confidence = 'HIGH'
    elif article_count >= 15:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'
    
    # Determine direction with LOWER thresholds
    direction = 'BULLISH' if final_score > 5 else ('BEARISH' if final_score < -5 else 'NEUTRAL')
    
    prediction = {
        'ticker': ticker,
        'prediction': round(final_score, 2),
        'final_signal': signal,
        'confidence': confidence,
        'sentiment_score': round(avg_sentiment, 4),
        'financial_score': round(financial_score, 2),
        'average_sentiment': round(avg_sentiment, 4),
        'article_count': article_count,
        'last_updated': datetime.now().isoformat(),
        'timestamp': datetime.now().isoformat(),
        'direction': direction
    }
    
    return prediction

def save_prediction(ticker, prediction):
    """Save prediction to file"""
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    file_path = os.path.join(PREDICTIONS_DIR, f"{ticker}_prediction.json")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(prediction, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving prediction for {ticker}: {e}")

def start_processor():
    """Start the continuous data processor"""
    check_interval = int(os.getenv('PROCESSOR_CHECK_INTERVAL_SECONDS', 30))
    
    logger.info(f"✅ Data Processor started - reanalyzing articles every {check_interval}s")
    logger.info(f"💡 Will continuously generate NEW sentiment and financial scores from existing articles")
    
    try:
        while True:
            process_articles()
            time.sleep(check_interval)
    except KeyboardInterrupt:
        logger.info("❌ Data Processor stopped")

if __name__ == '__main__':
    start_processor()