"""
Continuous Data Processor
Monitors for new articles and processes them immediately
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from article_classifier import ArticleClassifier
from sentiment_analysis import SentimentAnalyzer
from financial_analyzer.financial_event_classifier import FinancialEventClassifier
from financial_analyzer.earnings_parser import EarningsParser
from financial_analyzer.market_predictor import MarketImpactPredictor
from financial_analyzer.signal_combiner import SignalCombiner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CHECK_INTERVAL = int(os.getenv('PROCESSOR_CHECK_INTERVAL_SECONDS', 60))


class ArticleProcessor(FileSystemEventHandler):
    """Process articles as they arrive"""
    
    def __init__(self):
        self.classifier = ArticleClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.financial_classifier = FinancialEventClassifier()
        self.earnings_parser = EarningsParser()
        self.market_predictor = MarketImpactPredictor()
        self.signal_combiner = SignalCombiner()
        
        self.processing_queue = set()
        self.last_processed = {}
        
        # Paths
        self.crawler_data_dir = Path(__file__).parent.parent / "crawler_service" / "data" / "by_company"
        self.output_dir = Path(__file__).parent / "final_predictions"
        self.output_dir.mkdir(exist_ok=True)
        
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
            
        if event.src_path.endswith('.json'):
            logger.info(f"📄 New article detected: {event.src_path}")
            self.process_company_data(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification"""
        if event.is_directory:
            return
            
        if event.src_path.endswith('.json'):
            logger.info(f"📝 Article modified: {event.src_path}")
            self.process_company_data(event.src_path)
    
    def process_company_data(self, file_path):
        """Process data for a company"""
        try:
            # Extract company ticker from path
            path_parts = Path(file_path).parts
            ticker = None
            
            for part in path_parts:
                if part in ['MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META', 
                           'NVDA', 'NFLX', 'BABA', 'AMD', 'INTC', 'CRM', 'UNP']:
                    ticker = part
                    break
            
            if not ticker:
                return
            
            # Avoid duplicate processing
            current_time = time.time()
            if ticker in self.last_processed:
                if current_time - self.last_processed[ticker] < 30:  # 30 second cooldown
                    return
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 PROCESSING: {ticker}")
            logger.info(f"{'='*60}")
            
            # Step 1: Classify articles
            logger.info(f"[1/5] Classifying articles...")
            self.classifier.classify_company_articles(ticker)
            
            # Step 2: Sentiment analysis on general articles
            logger.info(f"[2/5] Analyzing sentiment...")
            self.sentiment_analyzer.analyze_company_sentiment(ticker)
            
            # Step 3: Financial event classification
            logger.info(f"[3/5] Classifying financial events...")
            self.financial_classifier.classify_company_financial_events(ticker)
            
            # Step 4: Earnings parsing
            logger.info(f"[4/5] Parsing earnings data...")
            self.earnings_parser.parse_company_earnings(ticker)
            
            # Step 5: Generate final prediction
            logger.info(f"[5/5] Generating prediction...")
            prediction = self.signal_combiner.combine_signals(ticker)
            
            # Save prediction
            output_file = self.output_dir / f"{ticker}_prediction.json"
            with open(output_file, 'w') as f:
                json.dump(prediction, f, indent=2)
            
            logger.info(f"✅ {ticker}: Prediction saved - {prediction['prediction']['final_signal']}")
            logger.info(f"{'='*60}\n")
            
            self.last_processed[ticker] = current_time
            
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}", exc_info=True)
    
    def process_all_existing(self):
        """Process all existing company data on startup"""
        logger.info("🔄 Processing all existing company data...")
        
        if not self.crawler_data_dir.exists():
            logger.warning(f"Crawler data directory not found: {self.crawler_data_dir}")
            return
        
        companies = [d for d in self.crawler_data_dir.iterdir() if d.is_dir()]
        
        for company_dir in companies:
            ticker = company_dir.name
            logger.info(f"Processing existing data for {ticker}...")
            
            try:
                # Process this company
                self.classifier.classify_company_articles(ticker)
                self.sentiment_analyzer.analyze_company_sentiment(ticker)
                self.financial_classifier.classify_company_financial_events(ticker)
                self.earnings_parser.parse_company_earnings(ticker)
                prediction = self.signal_combiner.combine_signals(ticker)
                
                # Save prediction
                output_file = self.output_dir / f"{ticker}_prediction.json"
                with open(output_file, 'w') as f:
                    json.dump(prediction, f, indent=2)
                
                logger.info(f"✅ {ticker}: Processed")
                
            except Exception as e:
                logger.error(f"❌ Error processing {ticker}: {e}")


class ContinuousProcessor:
    """Manages continuous processing"""
    
    def __init__(self):
        self.processor = ArticleProcessor()
        self.observer = Observer()
        
    def start(self):
        """Start continuous processing"""
        logger.info("🚀 Starting Continuous Data Processor")
        logger.info(f"Watching: {self.processor.crawler_data_dir}")
        logger.info("")
        
        # Process all existing data first
        self.processor.process_all_existing()
        
        # Start watching for new files
        self.observer.schedule(
            self.processor,
            str(self.processor.crawler_data_dir),
            recursive=True
        )
        self.observer.start()
        
        logger.info("👀 Now watching for new articles...")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("\n🛑 Processor stopped by user")
            self.observer.stop()
        
        self.observer.join()


def main():
    """Main entry point"""
    processor = ContinuousProcessor()
    processor.start()


if __name__ == "__main__":
    main()