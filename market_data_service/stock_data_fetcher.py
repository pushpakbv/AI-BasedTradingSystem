"""
Stock Data Fetcher
Fetches real-time and historical stock data using yfinance
"""
import yfinance as yf
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Companies to fetch data for
COMPANIES = [
    'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'AMD', 
    'INTC', 'CRM', 'UNP', 'FDX', 'UPS', 'CHRW', 'XPO', 'GXO', 'JD'
]

# Output directory
OUTPUT_DIR = Path(__file__).parent / 'stock_data'
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_stock_data(ticker, period='1y'):
    """
    Fetch historical stock data for a ticker
    period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
    """
    try:
        logger.info(f"📊 Fetching stock data for {ticker}...")
        
        # Download data
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            logger.warning(f"⚠️ No data found for {ticker}")
            return None
        
        # Get current price info
        info = stock.info
        
        # Convert to list format
        historical_data = []
        for date, row in hist.iterrows():
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
                'adjClose': round(float(row.get('Adj Close', row['Close'])), 2)
            })
        
        # Get current price and stats
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        
        stock_data = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': round(float(current_price), 2),
            'previous_close': round(float(info.get('previousClose', hist['Close'].iloc[-1])), 2),
            'day_high': round(float(info.get('dayHigh', hist['High'].iloc[-1])), 2),
            'day_low': round(float(info.get('dayLow', hist['Low'].iloc[-1])), 2),
            'fifty_two_week_high': round(float(info.get('fiftyTwoWeekHigh', hist['High'].max())), 2),
            'fifty_two_week_low': round(float(info.get('fiftyTwoWeekLow', hist['Low'].min())), 2),
            'volume': int(info.get('volume', hist['Volume'].iloc[-1])),
            'avg_volume': int(info.get('averageVolume', hist['Volume'].mean())),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'historical_data': historical_data,
            'last_updated': datetime.now().isoformat()
        }
        
        # Calculate change
        if len(historical_data) > 1:
            first_price = historical_data[0]['close']
            last_price = historical_data[-1]['close']
            change = last_price - first_price
            change_percent = (change / first_price) * 100
            
            stock_data['change'] = round(change, 2)
            stock_data['change_percent'] = round(change_percent, 2)
        
        logger.info(f"✅ {ticker}: ${stock_data['current_price']} | {len(historical_data)} data points")
        
        return stock_data
        
    except Exception as e:
        logger.error(f"❌ Error fetching {ticker}: {str(e)[:100]}")
        return None


def save_stock_data(stock_data, ticker):
    """Save stock data to JSON file"""
    if not stock_data:
        return False
    
    try:
        output_file = OUTPUT_DIR / f'{ticker}_stock_data.json'
        with open(output_file, 'w') as f:
            json.dump(stock_data, f, indent=2)
        
        logger.info(f"💾 Saved {ticker}")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving {ticker}: {e}")
        return False


def main():
    """Fetch and save stock data for all companies"""
    logger.info("\n" + "="*70)
    logger.info("🚀 STARTING STOCK DATA FETCH")
    logger.info("="*70)
    
    successful = 0
    failed = 0
    
    for ticker in COMPANIES:
        # Fetch 1 year of historical data
        stock_data = fetch_stock_data(ticker, period='1y')
        
        if stock_data and save_stock_data(stock_data, ticker):
            successful += 1
        else:
            failed += 1
    
    logger.info("\n" + "="*70)
    logger.info("✅ STOCK DATA FETCH COMPLETE")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {successful + failed}")
    logger.info(f"Output: {OUTPUT_DIR}")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()