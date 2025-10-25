"""
Stock Market Data Fetcher
Continuously fetches historical and current stock prices
"""
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import yfinance as yf
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

UPDATE_INTERVAL = int(os.getenv('MARKET_DATA_INTERVAL_HOURS', 1)) * 3600

# Companies to track
COMPANIES = ['MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'AMD', 'INTC', 'CRM', 'UNP']


class StockDataFetcher:
    """Fetches and stores stock market data"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent / "stock_data"
        self.output_dir.mkdir(exist_ok=True)
        
    def fetch_stock_data(self, ticker, period='7d'):
        """Fetch historical stock data"""
        try:
            logger.info(f"📈 Fetching data for {ticker}...")
            
            stock = yf.Ticker(ticker)
            
            # Get historical data (past week)
            hist = stock.history(period=period)
            
            if hist.empty:
                logger.warning(f"No data available for {ticker}")
                return None
            
            # Convert to dict
            data = {
                'ticker': ticker,
                'last_updated': datetime.now().isoformat(),
                'current_price': float(hist['Close'].iloc[-1]),
                'historical_data': []
            }
            
            # Add historical prices
            for date, row in hist.iterrows():
                data['historical_data'].append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            # Save to file
            output_file = self.output_dir / f"{ticker}_stock_data.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✅ {ticker}: Saved {len(data['historical_data'])} data points")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error fetching {ticker}: {e}")
            return None
    
    def fetch_all_stocks(self):
        """Fetch data for all companies"""
        logger.info("=" * 80)
        logger.info(f"FETCHING STOCK DATA FOR {len(COMPANIES)} COMPANIES")
        logger.info("=" * 80)
        
        successful = 0
        failed = []
        
        for ticker in COMPANIES:
            result = self.fetch_stock_data(ticker)
            if result:
                successful += 1
            else:
                failed.append(ticker)
            
            time.sleep(1)  # Rate limiting
        
        logger.info("\n" + "=" * 80)
        logger.info(f"COMPLETED: {successful}/{len(COMPANIES)} successful")
        if failed:
            logger.info(f"Failed: {', '.join(failed)}")
        logger.info("=" * 80 + "\n")
    
    def start(self):
        """Start continuous fetching"""
        logger.info("🚀 Starting Stock Data Fetcher")
        logger.info(f"Interval: Every {UPDATE_INTERVAL / 3600:.0f} hour(s)")
        logger.info(f"Companies: {len(COMPANIES)}")
        logger.info("")
        
        while True:
            try:
                self.fetch_all_stocks()
                
                logger.info(f"⏳ Sleeping for {UPDATE_INTERVAL / 3600:.0f} hour(s)...")
                time.sleep(UPDATE_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Stock data fetcher stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
                logger.info("⏳ Waiting 5 minutes before retry...")
                time.sleep(300)


def main():
    """Main entry point"""
    fetcher = StockDataFetcher()
    fetcher.start()


if __name__ == "__main__":
    main()