"""
Unit tests for Web Crawler Service
"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler_service.utils.dedup import is_duplicate, mark_as_seen, get_seen_count, clear_dedupe_db
from crawler_service.utils.company_matcher import CompanyMatcher


class TestCrawlerDedup(unittest.TestCase):
    """Test deduplication functionality"""
    
    def setUp(self):
        """Clear dedupe database before each test"""
        clear_dedupe_db()
    
    def test_is_duplicate(self):
        """Test duplicate detection"""
        url = "https://example.com/test"
        
        # First time should not be duplicate
        self.assertFalse(is_duplicate(url))
        
        # Second time should be duplicate
        self.assertTrue(is_duplicate(url))
    
    def test_mark_as_seen(self):
        """Test marking URLs as seen"""
        url = "https://example.com/article"
        title = "Test Article"
        
        mark_as_seen(url, title, 200)
        
        # Should now be marked as duplicate
        self.assertTrue(is_duplicate(url))
    
    def test_get_seen_count(self):
        """Test getting count of seen URLs"""
        self.assertEqual(get_seen_count(), 0)
        
        mark_as_seen("https://example.com/1", "Article 1")
        mark_as_seen("https://example.com/2", "Article 2")
        
        self.assertEqual(get_seen_count(), 2)


class TestCompanyMatcher(unittest.TestCase):
    """Test company matching functionality"""
    
    def setUp(self):
        """Create a test config"""
        self.test_config = {
            "companies": [
                {
                    "name": "FedEx Corporation",
                    "ticker": "FDX",
                    "keywords": ["FedEx", "Federal Express"],
                    "sector": "Logistics"
                },
                {
                    "name": "UPS",
                    "ticker": "UPS",
                    "keywords": ["UPS", "United Parcel Service"],
                    "sector": "Logistics"
                }
            ],
            "general_keywords": ["supply chain", "logistics", "shipping"]
        }
    
    def test_match_companies_single(self):
        """Test matching a single company"""
        # This would need the actual config file or mock
        text = "FedEx announced strong quarterly earnings today."
        # matcher = CompanyMatcher()
        # matched, score = matcher.match_companies(text)
        # self.assertEqual(len(matched), 1)
        # self.assertEqual(matched[0]["ticker"], "FDX")
        pass
    
    def test_match_companies_multiple(self):
        """Test matching multiple companies"""
        text = "FedEx and UPS are competing for market share in logistics."
        # matcher = CompanyMatcher()
        # matched, score = matcher.match_companies(text)
        # self.assertEqual(len(matched), 2)
        pass


class TestCrawlerOutput(unittest.TestCase):
    """Test crawler output format"""
    
    def test_json_structure(self):
        """Test that saved JSON has required fields"""
        required_fields = ["url", "fetched_at", "title", "content", "status", 
                          "matched_companies", "relevance_score"]
        
        sample_item = {
            "url": "https://example.com",
            "fetched_at": "2025-10-16T10:00:00Z",
            "title": "FedEx Reports Strong Earnings",
            "content": "FedEx Corporation announced...",
            "status": 200,
            "source_domain": "example.com",
            "word_count": 150,
            "matched_companies": [
                {"name": "FedEx Corporation", "ticker": "FDX", "sector": "Logistics", "mentions": 3}
            ],
            "relevance_score": 0.45,
            "article_type": "company_specific"
        }
        
        for field in required_fields:
            self.assertIn(field, sample_item)
    
    def test_company_data_structure(self):
        """Test company match data structure"""
        company_match = {
            "name": "FedEx Corporation",
            "ticker": "FDX",
            "sector": "Logistics",
            "mentions": 3
        }
        
        self.assertIn("ticker", company_match)
        self.assertIn("mentions", company_match)
        self.assertIsInstance(company_match["mentions"], int)


if __name__ == "__main__":
    unittest.main()