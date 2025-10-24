"""
Company Matching Utility
Provides functions to match text content with tracked companies.
"""
import os
import re
import yaml
from typing import List, Dict, Tuple


class CompanyMatcher:
    """Helper class for matching companies in text"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "companies.yml")
        
        self.companies = []
        self.company_keywords = {}
        self.general_keywords = []
        self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """Load company configuration from YAML file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Company config not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
        
        self.companies = config.get("companies", [])
        self.general_keywords = config.get("general_keywords", [])
        
        # Build keyword lookup
        for company in self.companies:
            ticker = company.get("ticker", "")
            keywords = company.get("keywords", [])
            self.company_keywords[ticker] = [kw.lower() for kw in keywords]
    
    def match_companies(self, text: str) -> Tuple[List[Dict], float]:
        """
        Find all companies mentioned in text.
        
        Args:
            text: Text to search for company mentions
            
        Returns:
            Tuple of (matched companies list, relevance score)
        """
        text_lower = text.lower()
        matched = []
        total_mentions = 0
        
        for company in self.companies:
            ticker = company.get("ticker", "")
            keywords = self.company_keywords.get(ticker, [])
            
            mentions = 0
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                mentions += len(re.findall(pattern, text_lower, re.IGNORECASE))
            
            if mentions > 0:
                matched.append({
                    "name": company.get("name", ""),
                    "ticker": ticker,
                    "sector": company.get("sector", ""),
                    "mentions": mentions
                })
                total_mentions += mentions
        
        # Sort by number of mentions (descending)
        matched.sort(key=lambda x: x["mentions"], reverse=True)
        
        # Calculate relevance score
        word_count = len(text.split())
        relevance_score = min(1.0, (total_mentions * 10) / max(word_count, 1))
        
        return matched, relevance_score
    
    def get_company_by_ticker(self, ticker: str) -> Dict:
        """Get company info by ticker symbol"""
        for company in self.companies:
            if company.get("ticker") == ticker:
                return company
        return None
    
    def get_all_tickers(self) -> List[str]:
        """Get list of all tracked ticker symbols"""
        return [c.get("ticker") for c in self.companies if c.get("ticker")]
    
    def get_companies_by_sector(self, sector: str) -> List[Dict]:
        """Get all companies in a specific sector"""
        return [c for c in self.companies if c.get("sector", "").lower() == sector.lower()]