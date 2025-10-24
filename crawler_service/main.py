# Entry point for web crawling service
"""
Web Crawler Service - Main Entry Point
Reads sites from config and runs Scrapy spider to crawl and store raw JSON data.
"""
import os
import sys
import yaml
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Import after path is set
from crawler_service.spiders.news_spider import NewsSpider

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Load config file
    cfg_path = os.path.join(os.path.dirname(__file__), "config", "sites.yml")
    if not os.path.exists(cfg_path):
        logger.error("Config file not found: %s", cfg_path)
        raise SystemExit(1)

    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    sites = cfg.get("sites", [])
    if not sites:
        logger.error("No sites configured to crawl in %s", cfg_path)
        raise SystemExit(1)

    logger.info("Starting crawler for %d sites", len(sites))

    # Configure Scrapy settings
    settings = get_project_settings()
    settings.set("LOG_LEVEL", "INFO")
    settings.set("ROBOTSTXT_OBEY", False)
    settings.set("CONCURRENT_REQUESTS", 8)
    settings.set("DOWNLOAD_TIMEOUT", 15)
    settings.set("RETRY_TIMES", 3)
    settings.set("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    # Start crawling
    process = CrawlerProcess(settings=settings)
    process.crawl(NewsSpider, start_urls=sites)
    process.start()
    
    logger.info("Crawling completed")

if __name__ == "__main__":
    main()