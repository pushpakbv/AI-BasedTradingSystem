"""
Scrapy Spider for crawling financial and supply chain news sites.
STRICT MODE: Company-specific articles from today only, free sources only.
"""
import os
import json
import hashlib
import datetime
import logging
from typing import List, Dict, Set, Tuple
import sqlite3
import re
from urllib.parse import urljoin, urlparse

import scrapy
from bs4 import BeautifulSoup
import yaml

# Try to use shared logger if available
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from shared.logger import get_logger
    logger = get_logger("crawler")
except Exception:
    logger = logging.getLogger("crawler")


class NewsSpider(scrapy.Spider):
    """
    Spider that crawls FREE news sites and extracts COMPANY-SPECIFIC articles from TODAY only.
    No paywalls. No generic articles. Company mentions required.
    """
    name = "news_spider"
    custom_settings = {
        'DOWNLOAD_DELAY': 1,  # Reduced from 2 for faster crawling
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,  # Increased from 3
        'DEPTH_LIMIT': 3,  # Increased from 2
        'DOWNLOAD_TIMEOUT': 20,
        'RETRY_TIMES': 2,
        'ROBOTSTXT_OBEY': True,  # Respect robots.txt
    }

    def __init__(self, start_urls: List[str] = None, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        if start_urls:
            self.start_urls = start_urls
        else:
            self.start_urls = kwargs.get("start_urls", [])
        
        # Setup data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.data_by_company_dir = os.path.join(base_dir, "data", "by_company")
        self.data_raw_dir = os.path.join(base_dir, "data", "raw")
        self.dedupe_db_path = os.path.join(base_dir, "data", "dedupe.db")
        
        os.makedirs(self.data_by_company_dir, exist_ok=True)
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.dedupe_db_path), exist_ok=True)
        
        # Load company configuration
        self.companies = []
        self.company_keywords = {}
        self.min_relevance_score = 0.3
        self.save_unmatched = False
        self.crawl_today_only = True
        self.max_article_age_hours = 24
        self.max_articles_per_site = 100
        self.articles_collected = {}
        
        self._load_company_config(base_dir)
        self._init_dedupe_db()
        
        # Get today's date range (00:00:00 to 23:59:59)
        self.today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        self.today_end = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Paywalled domains to skip
        self.paywall_domains = [
            'wsj.com',
            'ft.com',
            'bloomberg.com',
            'economist.com',
            'barrons.com',
            'nytimes.com',
        ]
        
        # Article URL patterns for free news sites
        self.article_patterns = {
            'reuters.com': r'/article/|/business/|/markets/',
            'cnbc.com': r'/\d{4}/\d{2}/\d{2}/',
            'yahoo.com': r'/news/|/finance/',
            'marketwatch.com': r'/story/',
            'supplychainbrain.com': r'/articles/',
            'supplychaindive.com': r'/news/',
            'freightwaves.com': r'/news/',
            'logisticsmgmt.com': r'/article/',
            'techcrunch.com': r'/\d{4}/\d{2}/\d{2}/',
            'businesswire.com': r'/news/',
            'prnewswire.com': r'/news-releases/',
        }
        
        logger.info("=" * 80)
        logger.info("STRICT CRAWLER MODE ACTIVATED")
        logger.info("=" * 80)
        logger.info("📅 Today's date range: %s to %s", 
                   self.today_start.strftime("%Y-%m-%d %H:%M"), 
                   self.today_end.strftime("%Y-%m-%d %H:%M"))
        logger.info("🏢 Tracking %d companies (company mentions REQUIRED)", len(self.companies))
        logger.info("🚫 Paywalled sites blocked: %d", len(self.paywall_domains))
        logger.info("✅ Crawling %d FREE news sources", len(self.start_urls))
        logger.info("=" * 80)

    def _load_company_config(self, base_dir: str):
        """Load company tracking configuration"""
        config_path = os.path.join(base_dir, "config", "companies.yml")
        
        if not os.path.exists(config_path):
            logger.error("Company config not found at %s", config_path)
            raise SystemExit(1)
        
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                config = yaml.safe_load(fh)
            
            self.companies = config.get("companies", [])
            self.min_relevance_score = config.get("min_relevance_score", 0.3)
            self.save_unmatched = config.get("save_unmatched_articles", False)
            self.crawl_today_only = config.get("crawl_today_only", True)
            self.max_article_age_hours = config.get("max_article_age_hours", 24)
            
            # Build keyword lookup
            for company in self.companies:
                ticker = company.get("ticker", "")
                keywords = company.get("keywords", [])
                self.company_keywords[ticker] = [kw.lower() for kw in keywords]
            
            logger.info("Loaded %d companies from config", len(self.companies))
            
        except Exception as e:
            logger.error("Error loading company config: %s", e)
            raise SystemExit(1)

    def _init_dedupe_db(self):
        """Initialize SQLite database for URL deduplication with migration support"""
        conn = sqlite3.connect(self.dedupe_db_path)
        cur = conn.cursor()
        
        # Check if table exists and get its columns
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seen_urls'")
        table_exists = cur.fetchone() is not None
        
        if not table_exists:
            # Create new table with all columns
            cur.execute("""
                CREATE TABLE seen_urls (
                    url TEXT PRIMARY KEY,
                    seen_at TEXT,
                    title TEXT,
                    status INTEGER,
                    crawl_date TEXT
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_crawl_date ON seen_urls(crawl_date)")
            logger.info("Created new deduplication database")
        else:
            # Check if crawl_date column exists
            cur.execute("PRAGMA table_info(seen_urls)")
            columns = [row[1] for row in cur.fetchall()]
            
            if 'crawl_date' not in columns:
                # Migration: Add crawl_date column to existing table
                logger.info("Migrating deduplication database - adding crawl_date column")
                cur.execute("ALTER TABLE seen_urls ADD COLUMN crawl_date TEXT")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_crawl_date ON seen_urls(crawl_date)")
                logger.info("Database migration completed")
        
        conn.commit()
        conn.close()

    def parse(self, response):
        """Main parse method - decides whether to extract content or follow links"""
        url = response.url
        domain = urlparse(url).netloc
        
        # Block paywalled sites
        if any(pw_domain in domain for pw_domain in self.paywall_domains):
            logger.warning("🚫 BLOCKED paywall site: %s", domain)
            return 
        
        # Check article limit per domain
        if domain in self.articles_collected:
            if self.articles_collected[domain] >= self.max_articles_per_site:
                logger.info("Hit article limit for %s", domain)
                return 
        
        # Check for duplicates
        if self._is_duplicate(url):
            return 
        
        # Determine if article page or listing page
        is_article_page = self._is_article_url(url)
        
        if is_article_page:
            result = self._extract_article(response)
            if result:
                yield from result
        else:
            yield from self._follow_article_links(response)

    def _is_article_url(self, url: str) -> bool:
        """Check if URL looks like an article page"""
        domain = urlparse(url).netloc
        
        # Check domain-specific patterns
        for site_domain, pattern in self.article_patterns.items():
            if site_domain in domain:
                if re.search(pattern, url):
                    return True
        
        # Generic article indicators
        article_indicators = [
            r'/article/',
            r'/news/',
            r'/story/',
            r'/\d{4}/\d{2}/\d{2}/',
            r'-\d{6,}',
        ]
        
        for pattern in article_indicators:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False

    def _follow_article_links(self, response):
        """Extract and follow links that look like articles"""
        soup = BeautifulSoup(response.text, "lxml")
        domain = urlparse(response.url).netloc
        
        links = soup.find_all('a', href=True)
        followed_count = 0
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            abs_url = urljoin(response.url, href)
            
            if not abs_url.startswith(('http://', 'https://')):
                continue
            
            # Only follow links on same domain
            if urlparse(abs_url).netloc != domain:
                continue
            
            # Check if it looks like an article
            if self._is_article_url(abs_url):
                followed_count += 1
                if followed_count <= 30:
                    yield scrapy.Request(
                        abs_url,
                        callback=self.parse,
                        dont_filter=False,
                        priority=10,
                        errback=self._handle_error
                    )

    def _handle_error(self, failure):
        """Handle request errors gracefully"""
        logger.error("Request failed: %s", failure.value)

    def _extract_article(self, response):
        """Extract content from an article page - STRICT COMPANY FILTER"""
        url = response.url
        domain = urlparse(url).netloc
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract content
        content = self._extract_content(soup)
        
        # Skip if content too short (likely not a real article or paywall)
        if len(content.split()) < 50:
            logger.debug("Skipping short/paywalled content from %s", url)
            return []
        
        # Extract metadata
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or \
                   soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag.get("content", "").strip()
        
        # Extract published date
        published_date, published_datetime = self._extract_published_date(soup, response)
        
        # FILTER 1: Check if article is from TODAY only
        if self.crawl_today_only and published_datetime:
            if not (self.today_start <= published_datetime <= self.today_end):
                age_hours = (datetime.datetime.utcnow() - published_datetime).total_seconds() / 3600
                logger.debug("⏭️  Skipping article from %s (%.1f hours old): %s", 
                           published_date, age_hours, title[:50])
                return []
        
        # Combine text for company matching
        full_text = f"{title} {meta_description} {content}".lower()
        
        # FILTER 2: Check for COMPANY MENTIONS (REQUIRED)
        matched_companies, relevance_score = self._match_companies(full_text)
        
        if not matched_companies:
            logger.debug("⏭️  Skipping article (no company mentions): %s", title[:60])
            return []
        
        if relevance_score < self.min_relevance_score:
            logger.debug("⏭️  Skipping article (low relevance %.2f): %s", 
                        relevance_score, title[:60])
            return []
        
        # Article passed all filters!
        if domain not in self.articles_collected:
            self.articles_collected[domain] = 0
        self.articles_collected[domain] += 1
        
        # Build item
        fetch_time = datetime.datetime.utcnow()
        item = {
            "url": url,
            "fetched_at": fetch_time.isoformat() + "Z",
            "published_date": published_date,
            "published_datetime": published_datetime.isoformat() + "Z" if published_datetime else None,
            "title": title,
            "content": content,
            "meta_description": meta_description,
            "status": response.status,
            "source_domain": domain,
            "word_count": len(content.split()),
            "matched_companies": matched_companies,
            "relevance_score": relevance_score,
            "article_type": "company_specific",
            "crawl_mode": "strict_today_only",
        }

        # Save raw backup
        self._save_raw_json(item)
        
        # Save by company and date
        self._save_by_company_and_date(item, matched_companies, published_date)
        
        # Mark as seen
        self._mark_as_seen(url, title, response.status, published_date)
        
        company_list = ", ".join([c["ticker"] for c in matched_companies])
        logger.info("✅ SAVED: [%s] %s | Score: %.2f | Words: %d", 
                   company_list, title[:50], relevance_score, item['word_count'])
        
        return []

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            # Remove site name from title
            if " - " in title:
                title = title.split(" - ")[0].strip()
            if " | " in title:
                title = title.split(" | ")[0].strip()
            return title
        
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return "No Title"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content - avoid paywall text"""
        content_parts = []
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe"]):
            script.decompose()
        
        # Strategy 1: article tag
        article = soup.find("article")
        if article:
            paragraphs = article.find_all("p")
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                # Filter out paywall indicators
                if len(text) > 30 and not self._is_paywall_text(text):
                    content_parts.append(text)
        
        # Strategy 2: common content divs
        if not content_parts:
            content_divs = soup.find_all(
                ["div"], 
                class_=re.compile(r'(article-body|story-body|post-content|entry-content|article-content|story__body)', re.I)
            )
            for div in content_divs:
                paragraphs = div.find_all("p")
                for p in paragraphs:
                    text = p.get_text(separator=" ", strip=True)
                    if len(text) > 30 and not self._is_paywall_text(text):
                        content_parts.append(text)
        
        # Strategy 3: all paragraphs (filtered)
        if not content_parts:
            paragraphs = soup.find_all("p")
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                if len(text) > 50 and not self._is_paywall_text(text):
                    content_parts.append(text)
        
        content = "\n\n".join(content_parts[:50])
        return content[:50000]

    def _is_paywall_text(self, text: str) -> bool:
        """Detect common paywall messages"""
        paywall_indicators = [
            "subscribe",
            "subscription",
            "paywall",
            "premium content",
            "become a member",
            "sign up",
            "already a subscriber",
            "log in to continue",
            "this article is for",
            "exclusive to",
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in paywall_indicators)

    def _extract_published_date(self, soup: BeautifulSoup, response) -> Tuple[str, datetime.datetime]:
        """Extract published date and return both string and datetime object"""
        date_selectors = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"name": "pubdate"}),
            ("meta", {"name": "publishdate"}),
            ("meta", {"property": "og:published_time"}),
            ("meta", {"name": "date"}),
            ("meta", {"name": "publish-date"}),
            ("time", {"datetime": True}),
            ("span", {"class": re.compile(r'date|time|published', re.I)}),
        ]
        
        for tag_name, attrs in date_selectors:
            tag = soup.find(tag_name, attrs=attrs)
            if tag:
                date_str = tag.get("content") or tag.get("datetime") or tag.get_text()
                if date_str:
                    try:
                        # Try ISO format first
                        parsed = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        return parsed.strftime("%Y-%m-%d"), parsed.replace(tzinfo=None)
                    except:
                        try:
                            # Try dateutil parser - FIXED IMPORT
                            import dateutil.parser
                            parsed = dateutil.parser.parse(date_str)
                            return parsed.strftime("%Y-%m-%d"), parsed.replace(tzinfo=None)
                        except Exception as e:
                            logger.debug("Failed to parse date '%s': %s", date_str, e)
                            pass
        
        # Fallback to today
        today = datetime.datetime.utcnow()
        return today.strftime("%Y-%m-%d"), today
        # Fallback to today
        today = datetime.datetime.utcnow()
        return today.strftime("%Y-%m-%d"), today
    
    def _match_companies(self, text: str) -> Tuple[List[Dict], float]:
        """Check which companies are mentioned - STRICT matching"""
        matched = []
        total_mentions = 0
        
        for company in self.companies:
            ticker = company.get("ticker", "")
            keywords = self.company_keywords.get(ticker, [])
            
            mentions = 0
            for keyword in keywords:
                # Use word boundaries for accurate matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                mentions += len(matches)
            
            if mentions > 0:
                matched.append({
                    "name": company.get("name", ""),
                    "ticker": ticker,
                    "sector": company.get("sector", ""),
                    "mentions": mentions
                })
                total_mentions += mentions
        
        # Sort by mentions
        matched.sort(key=lambda x: x["mentions"], reverse=True)
        
        # Calculate relevance score
        word_count = len(text.split())
        relevance_score = min(1.0, (total_mentions * 15) / max(word_count, 1))
        
        return matched, relevance_score

    def _is_duplicate(self, url: str) -> bool:
        """Check if URL has been seen before"""
        conn = sqlite3.connect(self.dedupe_db_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM seen_urls WHERE url = ?", (url,))
        found = cur.fetchone() is not None
        conn.close()
        return found

    def _mark_as_seen(self, url: str, title: str, status: int, crawl_date: str):
        """Mark URL as seen"""
        conn = sqlite3.connect(self.dedupe_db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO seen_urls (url, seen_at, title, status, crawl_date) VALUES (?, ?, ?, ?, ?)",
            (url, datetime.datetime.utcnow().isoformat(), title, status, crawl_date)
        )
        conn.commit()
        conn.close()

    def _save_raw_json(self, item: dict):
        """Save to raw directory"""
        url_hash = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()[:16]
        timestamp = int(datetime.datetime.utcnow().timestamp())
        
        companies_str = ""
        if item.get("matched_companies"):
            tickers = [c["ticker"].replace(".", "_") for c in item["matched_companies"][:3]]
            companies_str = "_" + "-".join(tickers)
        
        filename = f"article_{url_hash}{companies_str}_{timestamp}.json"
        filepath = os.path.join(self.data_raw_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(item, fh, ensure_ascii=False, indent=2)

    def _save_by_company_and_date(self, item: dict, matched_companies: List[Dict], date: str):
        """Save organized by company and date"""
        url_hash = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()[:12]
        
        for company in matched_companies:
            ticker = company["ticker"].replace(".", "_")
            company_date_dir = os.path.join(self.data_by_company_dir, ticker, date)
            os.makedirs(company_date_dir, exist_ok=True)
            
            filename = f"article_{url_hash}_mentions{company['mentions']}.json"
            filepath = os.path.join(company_date_dir, filename)
            
            company_item = item.copy()
            company_item["primary_company"] = company
            
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(company_item, fh, ensure_ascii=False, indent=2)