"""
Enhanced Earnings Parser
Extracts earnings data and determines beat/miss status with confidence scoring
"""
import re
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EarningsParser:
    """Parse and analyze earnings-related financial articles"""
    
    def __init__(self):
        # Earnings keywords with context
        self.earnings_patterns = {
            'beat': [
                r'beat\s+(?:wall\s+street\s+)?(?:analyst\s+)?estimates?',
                r'topped?\s+(?:analyst\s+)?estimates?',
                r'exceeded?\s+(?:analyst\s+)?expectations?',
                r'surpassed?\s+(?:analyst\s+)?forecasts?',
                r'better\s+than\s+(?:analyst\s+)?expected',
                r'above\s+(?:analyst\s+)?estimates?',
                r'stronger\s+than\s+expected',
            ],
            'miss': [
                r'miss(?:ed)?\s+(?:wall\s+street\s+)?(?:analyst\s+)?estimates?',
                r'fell\s+short\s+of\s+estimates?',
                r'below\s+(?:analyst\s+)?estimates?',
                r'disappointed?\s+(?:analyst\s+)?expectations?',
                r'worse\s+than\s+expected',
                r'weaker\s+than\s+expected',
                r'failed\s+to\s+meet\s+estimates?',
            ],
            'inline': [
                r'in\s+line\s+with\s+estimates?',
                r'met\s+estimates?',
                r'matched\s+expectations?',
                r'as\s+expected',
            ]
        }
        
        # Guidance patterns
        self.guidance_patterns = {
            'raised': [
                r'raised?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'increased?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'boosted?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'upgraded?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'improved?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
            ],
            'lowered': [
                r'lowered?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'reduced?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'cut\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'downgraded?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'trimmed?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
            ],
            'maintained': [
                r'maintained?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'reaffirmed?\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
                r'kept\s+(?:full[- ]year\s+)?(?:guidance|forecast|outlook)',
            ]
        }
    
    def parse_article(self, article: Dict) -> Dict:
        """
        Parse earnings article and extract structured data
        
        Args:
            article: Article dictionary with title and content
            
        Returns:
            Dictionary with earnings analysis
        """
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        full_text = f"{title} {content}"
        
        # Detect earnings beat/miss
        earnings_status = self._detect_earnings_status(full_text)
        
        # Detect guidance changes
        guidance_status = self._detect_guidance(full_text)
        
        # Extract financial figures
        financial_data = self._extract_financial_figures(full_text)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            earnings_status, 
            guidance_status, 
            financial_data,
            full_text
        )
        
        # Determine overall signal
        overall_signal = self._determine_signal(
            earnings_status,
            guidance_status,
            financial_data
        )
        
        return {
            'earnings_status': earnings_status,  # BEAT, MISS, INLINE, UNKNOWN
            'guidance_status': guidance_status,  # RAISED, LOWERED, MAINTAINED, UNKNOWN
            'financial_data': financial_data,
            'overall_signal': overall_signal,    # STRONG_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, STRONG_NEGATIVE
            'confidence': confidence,
            'analysis_timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _detect_earnings_status(self, text: str) -> str:
        """Detect if earnings beat, missed, or met estimates"""
        beat_score = 0
        miss_score = 0
        inline_score = 0
        
        for pattern in self.earnings_patterns['beat']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            beat_score += len(matches) * 2  # Weight beat indicators
        
        for pattern in self.earnings_patterns['miss']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            miss_score += len(matches) * 2
        
        for pattern in self.earnings_patterns['inline']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            inline_score += len(matches)
        
        # Determine status
        if beat_score > miss_score and beat_score > inline_score:
            return 'BEAT'
        elif miss_score > beat_score and miss_score > inline_score:
            return 'MISS'
        elif inline_score > 0:
            return 'INLINE'
        else:
            return 'UNKNOWN'
    
    def _detect_guidance(self, text: str) -> str:
        """Detect guidance changes"""
        raised_score = 0
        lowered_score = 0
        maintained_score = 0
        
        for pattern in self.guidance_patterns['raised']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            raised_score += len(matches)
        
        for pattern in self.guidance_patterns['lowered']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            lowered_score += len(matches)
        
        for pattern in self.guidance_patterns['maintained']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            maintained_score += len(matches)
        
        if raised_score > lowered_score and raised_score > maintained_score:
            return 'RAISED'
        elif lowered_score > raised_score:
            return 'LOWERED'
        elif maintained_score > 0:
            return 'MAINTAINED'
        else:
            return 'UNKNOWN'
    
    def _extract_financial_figures(self, text: str) -> Dict:
        """Extract EPS, revenue, and percentage figures"""
        figures = {
            'eps_actual': None,
            'eps_expected': None,
            'eps_beat_percent': None,
            'revenue_actual': None,
            'revenue_expected': None,
            'revenue_beat_percent': None,
            'growth_rates': []
        }
        
        # EPS patterns
        eps_pattern = r'eps\s+(?:of\s+)?[\$]?([\d.]+)'
        eps_matches = re.findall(eps_pattern, text, re.IGNORECASE)
        if eps_matches:
            figures['eps_actual'] = float(eps_matches[0])
        
        # Expected EPS
        expected_eps_pattern = r'expected\s+(?:eps\s+of\s+)?[\$]?([\d.]+)'
        expected_eps = re.findall(expected_eps_pattern, text, re.IGNORECASE)
        if expected_eps:
            figures['eps_expected'] = float(expected_eps[0])
        
        # Revenue patterns (in billions or millions)
        revenue_billion = r'[\$]?([\d.]+)\s*billion'
        revenue_million = r'[\$]?([\d.]+)\s*million'
        
        revenue_b = re.findall(revenue_billion, text, re.IGNORECASE)
        if revenue_b:
            figures['revenue_actual'] = float(revenue_b[0]) * 1_000_000_000
        else:
            revenue_m = re.findall(revenue_million, text, re.IGNORECASE)
            if revenue_m:
                figures['revenue_actual'] = float(revenue_m[0]) * 1_000_000
        
        # Growth rates (YoY, QoQ)
        growth_pattern = r'([\d.]+)%\s+(?:year[- ]over[- ]year|yoy|q(?:uarter)?[- ]over[- ]q(?:uarter)?|qoq)'
        growth_rates = re.findall(growth_pattern, text, re.IGNORECASE)
        figures['growth_rates'] = [float(g) for g in growth_rates[:5]]  # Top 5
        
        # Calculate beat percentages if both actual and expected exist
        if figures['eps_actual'] and figures['eps_expected']:
            figures['eps_beat_percent'] = (
                (figures['eps_actual'] - figures['eps_expected']) / figures['eps_expected']
            ) * 100
        
        return figures
    
    def _calculate_confidence(
        self,
        earnings_status: str,
        guidance_status: str,
        financial_data: Dict,
        text: str
    ) -> float:
        """Calculate confidence score (0-1)"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if clear earnings status
        if earnings_status in ['BEAT', 'MISS']:
            confidence += 0.2
        
        # Boost if guidance is clear
        if guidance_status in ['RAISED', 'LOWERED']:
            confidence += 0.15
        
        # Boost if we have actual numbers
        if financial_data.get('eps_actual'):
            confidence += 0.1
        
        if financial_data.get('revenue_actual'):
            confidence += 0.05
        
        # Check for earnings report keywords
        earnings_keywords = ['earnings report', 'quarterly results', 'fiscal quarter']
        if any(keyword in text for keyword in earnings_keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _determine_signal(
        self,
        earnings_status: str,
        guidance_status: str,
        financial_data: Dict
    ) -> str:
        """Determine overall market signal"""
        score = 0
        
        # Earnings status scoring
        if earnings_status == 'BEAT':
            score += 3
        elif earnings_status == 'MISS':
            score -= 3
        elif earnings_status == 'INLINE':
            score += 0
        
        # Guidance scoring (weighted heavily)
        if guidance_status == 'RAISED':
            score += 4
        elif guidance_status == 'LOWERED':
            score -= 4
        elif guidance_status == 'MAINTAINED':
            score += 1
        
        # Beat percentage scoring
        if financial_data.get('eps_beat_percent'):
            beat_pct = financial_data['eps_beat_percent']
            if beat_pct > 10:
                score += 2
            elif beat_pct > 5:
                score += 1
            elif beat_pct < -10:
                score -= 2
            elif beat_pct < -5:
                score -= 1
        
        # Determine final signal
        if score >= 5:
            return 'STRONG_POSITIVE'
        elif score >= 2:
            return 'POSITIVE'
        elif score <= -5:
            return 'STRONG_NEGATIVE'
        elif score <= -2:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'


def main():
    """Test earnings parser"""
    parser = EarningsParser()
    
    # Test article
    test_article = {
        'title': 'Microsoft beats Q3 estimates with $61.8B revenue',
        'content': '''Microsoft Corp. reported third-quarter earnings that beat Wall Street 
        estimates with revenue of $61.8 billion versus expected $60.5 billion. EPS came in 
        at $2.94, topping analyst estimates of $2.82. The company also raised full-year 
        guidance citing strong Azure growth of 31% year-over-year.'''
    }
    
    result = parser.parse_article(test_article)
    
    print("=" * 60)
    print("EARNINGS ANALYSIS TEST")
    print("=" * 60)
    print(f"Earnings Status: {result['earnings_status']}")
    print(f"Guidance Status: {result['guidance_status']}")
    print(f"Overall Signal: {result['overall_signal']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"\nFinancial Data:")
    for key, value in result['financial_data'].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()