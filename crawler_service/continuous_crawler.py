"""
Continuous News Crawler
Runs every 30 minutes to fetch latest articles and triggers downstream processing
"""
import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path so we can import data_processor_service
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add crawler_service to sys.path for local imports
sys.path.insert(0, str(Path(__file__).parent))
from run_daily_crawl import run_crawl_for_company
from config.company_config import COMPANIES

# Now import from data_processor_service.continuous_processor
from data_processor_service.continuous_processor import process_new_articles

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CRAWLER_INTERVAL = int(os.getenv('CRAWLER_INTERVAL_MINUTES', 30)) * 60  # seconds

class ContinuousCrawler:
    """Continuously crawls news articles and triggers processing"""

    def __init__(self):
        self.run_count = 0
        self.last_run_time = None
        self.stats_file = Path(__file__).parent / "data" / "crawler_stats.json"

    def run_crawl_cycle(self):
        self.run_count += 1
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info(f"STARTING CRAWL CYCLE #{self.run_count}")
        logger.info(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        total_articles = 0
        successful_companies = 0
        failed_companies = []

        for company in COMPANIES:
            ticker = company['ticker']
            try:
                logger.info(f"\n📰 Crawling news for {ticker}...")
                articles_count = run_crawl_for_company(ticker)
                total_articles += articles_count
                successful_companies += 1
                logger.info(f"✅ {ticker}: Fetched {articles_count} articles")

                # Trigger data processing for this ticker
                logger.info(f"⚙️ Processing new articles for {ticker}...")
                process_new_articles(ticker)

            except Exception as e:
                logger.error(f"❌ {ticker}: Failed - {e}")
                failed_companies.append(ticker)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info("\n" + "=" * 80)
        logger.info(f"CRAWL CYCLE #{self.run_count} COMPLETED")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total articles fetched: {total_articles}")
        logger.info(f"Successful: {successful_companies}/{len(COMPANIES)} companies")
        if failed_companies:
            logger.info(f"Failed: {', '.join(failed_companies)}")
        logger.info("=" * 80 + "\n")

        self.last_run_time = end_time
        self._save_stats(total_articles, successful_companies, failed_companies)

    def _save_stats(self, total_articles, successful, failed):
        stats = {
            "last_run": self.last_run_time.isoformat(),
            "run_count": self.run_count,
            "total_articles": total_articles,
            "successful_companies": successful,
            "failed_companies": failed
        }
        self.stats_file.parent.mkdir(exist_ok=True)
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

    def start(self):
        logger.info("🚀 Starting Continuous Crawler")
        logger.info(f"Interval: Every {CRAWLER_INTERVAL / 60:.0f} minutes")
        logger.info(f"Companies: {len(COMPANIES)}")
        logger.info("")
        while True:
            try:
                self.run_crawl_cycle()
                logger.info(f"Sleeping for {CRAWLER_INTERVAL / 60:.0f} minutes...\n")
                time.sleep(CRAWLER_INTERVAL)
            except KeyboardInterrupt:
                logger.info("🛑 Continuous Crawler stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait a minute before retrying

def main():
    crawler = ContinuousCrawler()
    crawler.start()

if __name__ == "__main__":
    main()