import os
import sys
import json
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup paths
CUR_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CUR_DIR.parent
if str(CUR_DIR) not in sys.path:
    sys.path.insert(0, str(CUR_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from process_pipeline import ProcessingPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CHECK_INTERVAL = int(os.getenv('PROCESSOR_CHECK_INTERVAL_SECONDS', 60))


class ArticleProcessor(FileSystemEventHandler):
    """Process articles as they arrive"""
    
    def __init__(self):
        self.pipeline = ProcessingPipeline()
        
        self.processing_queue = set()
        self.last_processed = {}

        crawler_data_env = os.getenv('CRAWLER_DATA_DIR')
        if crawler_data_env and os.path.exists(crawler_data_env):
            self.crawler_data_dir = Path(crawler_data_env)
        else:
            # In Docker, use /app path; locally use relative path
            if os.path.exists('/app/crawler_service'):
                self.crawler_data_dir = Path('/app/crawler_service/data/by_company')
            else:
                self.crawler_data_dir = PROJECT_ROOT / "crawler_service" / "data" / "by_company"

        # Paths
        self.output_dir = CUR_DIR / "final_predictions"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Crawler data directory: {self.crawler_data_dir}")
        logger.info(f"Output directory: {self.output_dir}")

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
            
            # List of known company tickers
            known_tickers = [
                'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META', 
                'NVDA', 'NFLX', 'BABA', 'AMD', 'INTC', 'CRM', 'UNP',
                'FDX', 'UPS', 'CHRW', 'XPO', 'GXO'
            ]
            
            for part in path_parts:
                if part in known_tickers:
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
            
            # Use the ProcessingPipeline to handle all steps
            self.pipeline.process_company(ticker)
            
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
                # Use the ProcessingPipeline to handle all steps
                self.pipeline.process_company(ticker)
            except Exception as e:
                logger.error(f"❌ Error processing {ticker}: {e}", exc_info=True)


class ContinuousProcessor:
    """Manages continuous file watching and processing"""
    
    def __init__(self):
        self.processor = ArticleProcessor()
        self.observer = Observer()
        
        # Watch the crawler data directory
        self.observer.schedule(
            self.processor,
            str(self.processor.crawler_data_dir),
            recursive=True
        )
    
    def start(self):
        """Start watching for new files"""
        logger.info(f"👀 Watching: {self.processor.crawler_data_dir}")
        
        # Process all existing data first
        self.processor.process_all_existing()
        
        # Start watching for new files
        logger.info("👀 Now watching for new articles...")
        logger.info("Press Ctrl+C to stop")
        
        self.observer.start()
        
        try:
            while True:
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("⏹️  Stopping processor...")
            self.observer.stop()
        
        self.observer.join()


def process_new_articles(ticker):
    """
    Public function to process new articles for a given ticker.
    This can be called directly from other services (e.g., crawler).
    """
    try:
        pipeline = ProcessingPipeline()
        logger.info(f"🔔 [External Trigger] Processing new articles for {ticker}...")
        pipeline.process_company(ticker)
        logger.info(f"✅ [External Trigger] {ticker}: Processing complete")
        return True
    except Exception as e:
        logger.error(f"❌ [External Trigger] Error processing {ticker}: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    logger.info("🚀 Starting Continuous Data Processor")
    
    processor = ContinuousProcessor()
    processor.start()


if __name__ == "__main__":
    main()